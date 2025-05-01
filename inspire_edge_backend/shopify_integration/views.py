from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
import requests

from .models import ShopifyStore
from django.contrib.auth import get_user_model

User = get_user_model()

# Step 1: Generate OAuth redirect URL
class ShopifyAuthRedirectView(APIView):
    def get(self, request):
        shop = request.query_params.get("shop")
        if not shop:
            return Response({"error": "Missing shop parameter"}, status=400)

        params = {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": settings.SHOPIFY_SCOPES,
            "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
        }
        redirect_url = f"https://{shop}/admin/oauth/authorize?" + urlencode(params)
        return Response({"url": redirect_url})


# Step 2: Handle callback and save token
class ShopifyCallbackView(APIView):
    def get(self, request):
        code = request.GET.get("code")
        shop = request.GET.get("shop")

        if not code or not shop:
            return Response({"error": "Missing code or shop"}, status=400)

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

            user = request.user if request.user.is_authenticated else User.objects.first()

            ShopifyStore.objects.update_or_create(
                shop_domain=shop,
                defaults={"access_token": access_token, "user": user},
            )

            return Response({"message": "Shop connected!", "shop": shop})

        return Response({"error": "Failed to get access token"}, status=400)
