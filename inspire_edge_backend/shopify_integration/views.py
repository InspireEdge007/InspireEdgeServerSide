from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
import requests

from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from .models import ShopifyStore
from django.contrib.auth import get_user_model
from .utils import amazon_products
import base64
import json

User = get_user_model()

class ShopifyAuthRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = request.query_params.get("shop")
        if not shop:
            return Response({"error": "Missing shop parameter"}, status=400)

        # Create JWT for current user and encode it as base64
        refresh = RefreshToken.for_user(request.user)
        state = base64.urlsafe_b64encode(str(refresh.access_token).encode()).decode()

        params = {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": settings.SHOPIFY_SCOPES,
            "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
            "state": state,
        }

        redirect_url = f"https://{shop}/admin/oauth/authorize?" + urlencode(params)
        return Response({"url": redirect_url})

class ShopifyCallbackView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.GET.get("code")
        shop = request.GET.get("shop")
        state = request.GET.get("state")

        if not code or not shop or not state:
            return Response({"error": "Missing code, shop, or state"}, status=400)

        # Decode and validate the JWT token from state
        try:
            decoded_state = base64.urlsafe_b64decode(state).decode()
            access_token = AccessToken(decoded_state)
            user = request.user

            # Verify that the decoded token is for the current user (can be added as extra security)
            if str(user.id) != str(access_token['user_id']):
                return Response({"error": "Invalid user for this state"}, status=400)

        except Exception as e:
            return Response({"error": f"Invalid state parameter: {str(e)}"}, status=400)

        # Proceed to fetch the Shopify access token
        token_url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code,
        }

        response = requests.post(token_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            access_token = data["access_token"]

            # Store the access token in the ShopifyStore model
            ShopifyStore.objects.update_or_create(
                shop_domain=shop,
                defaults={"access_token": access_token, "user": user},
            )

            return Response({"message": "Shop connected!", "shop": shop})

        return Response({"error": "Failed to get access token"}, status=400)

class FetchProductsView(APIView):

    def get(self, request):

        stores = ShopifyStore.objects.all()

        for store in stores:
            headers = {
                "X-Shopify-Access-Token": store.access_token,
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"https://{store.shop_domain}/admin/api/2023-04/products.json",
                headers=headers
            )
            products = response.json().get("products", [])
            with open("products.json", "w") as file:
                json.dump(response.read(), file, indent= 4)

class CompareProductsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")
        # external_product_url = request.query_params.get("external_url")

        # Fetch from Shopify (connected)
        shopify_store = ShopifyStore.objects.get(shop_domain=shop)
        headers = {
            "X-Shopify-Access-Token": shopify_store.access_token
        }
        shopify_res = requests.get(
            f"https://{shop}/admin/api/2023-10/products/{shopify_product_id}.json",
            headers=headers
        )
        shopify_product = shopify_res.json()["product"]

        # Fetch from external source (Amazon, WooCommerce, etc.)
        external_product = amazon_products(shopify_product["title"])

        # Compare logic (simplified)
        result = {
            "title_match": shopify_product["title"] == external_product["title"],
            "price_diff": float(shopify_product["variants"][0]["price"]) - float(external_product["price"]),
            "shopify": shopify_product,
            "external": external_product,
        }

        return Response(result)

    def fetch_external_product(url):
    # Placeholder: fetch from Amazon, WooCommerce, etc.
        return {
            "title": "Sample Product",
            "price": "42.00",
            "sku": "ABC123"
        }


