from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError
from django.core.exceptions import ValidationError
import requests
from urllib.parse import quote
import traceback

import os
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from .models import ShopifyStore
from django.contrib.auth import get_user_model

# woo and big commerce integration
from shopify_integration.models import *
from rest_framework import status
from urllib.parse import unquote
from woocommerce import API
import logging
logger = logging.getLogger(__name__)
from requests.auth import HTTPBasicAuth

from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny

# Custom store integration
from rest_framework import generics, permissions
from .models import CustomStore, Category, CustomProduct
from .serializers import CustomStoreSerializer, CategorySerializer, CustomProductSerializer
from .serializers import (
    CustomStoreSerializer,
    CategorySerializer,
    CustomProductSerializer
)

from .utils import amazon_products, connect_to_market_recon

import base64
import json


User = get_user_model()

class ShopifyAuthRedirectView(APIView):

    permission_classes = [IsAuthenticated]  # Enable once frontend is ready to send auth token

    def get(self, request):
        shop = request.query_params.get("shop")
        if not shop:
            return Response({"error": "Missing shop parameter"}, status=400)

        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=401)

        # Encode user ID in base64 to send as `state`
        user_id = str(request.user.id)
        encoded_state = base64.urlsafe_b64encode(user_id.encode()).decode()

        params = {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": settings.SHOPIFY_SCOPES,
            "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
            "state": encoded_state,
        }

        redirect_url = f"https://{shop}/admin/oauth/authorize?" + urlencode(params)
        return Response({"url": redirect_url})

class ShopifyCallbackView(APIView):
    # No authentication here because user is identified via the `state` param

    def get(self, request):
        code = request.GET.get("code")
        shop = request.GET.get("shop")
        state = request.GET.get("state")

        if not code or not shop or not state:
            return Response({"error": "Missing code, shop, or state"}, status=400)

        # Decode `state` to retrieve the user ID
        try:
            decoded_user_id = base64.urlsafe_b64decode(state).decode()
            user = User.objects.get(id=int(decoded_user_id))
        except (ValueError, User.DoesNotExist, Exception) as e:
            return Response({"error": f"Invalid state/user: {str(e)}"}, status=400)

        # Exchange the authorization code for an access token
        token_url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code,
        }

        response = requests.post(token_url, json=payload)

        if response.status_code != 200:
            return Response({"error": "Failed to get access token", "details": response.json()}, status=400)

        data = response.json()
        access_token = data.get("access_token")

        if not access_token:
            return Response({"error": "No access token returned from Shopify"}, status=400)

        # Store or update the Shopify store for this user
        try:
            store, created = ShopifyStore.objects.update_or_create(
                shop_domain=shop.lower().strip(),
                defaults={"access_token": access_token, "user": user},
            )
            message = "Shopify store created." if created else "Shopify store updated."
            return Response({"message": message, "shop": shop})
        except IntegrityError as e:
            return Response({"error": f"Database integrity error: {e}"}, status=500)
        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)

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
                json.dump(products, file, indent= 4)


        return Response({"message": "Products fetched!", 'data' : products})

class CompareProductsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")
        # external_product_url = request.query_params.get("external_url")

        try:
            # Fetch from Shopify (connected)
            shopify_store = ShopifyStore.objects.get(shop_domain=shop)

            headers = {
                "X-Shopify-Access-Token": shopify_store.access_token
            }
            shopify_res = requests.get(
                f"https://{shop}/admin/api/2023-10/products/{shopify_product_id}.json",
                headers=headers
            )

            shopify_product = shopify_res.json()['product']

            shopify_product_title = quote("Apple iPhone 8 64GB Unlocked - Gray")

            # print(f'shopify title : {shopify_product_title}')

            # Fetch from external source (Amazon, WooCommerce, etc.)
            external_product = amazon_products(shopify_product_title, 1)

            print(type(shopify_product))


            if external_product:

                Ai_response = connect_to_market_recon(external_product, dict(shopify_product))
                print(Ai_response)

                return Response({"message": "Market recomends!", "data" : Ai_response}, status=200)
            else :
                return Response({"error": "competitors product with title not found"}, status=400)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)

    # def fetch_external_product(url):
    # # Placeholder: fetch from Amazon, WooCommerce, etc.
    #     return {
    #         "title": "Sample Product",
    #         "price": "42.00",
    #         "sku": "ABC123"
    #     }

        return Response({"error": "Failed to get access token"}, status=400)
    
    
# woo and big commerce integration   

# ==============================
# WooCommerce Integration
# ==============================

class WooCommerceAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        store_url = request.data.get("store_url")
        if not store_url:
            return Response({"error": "Missing store_url"}, status=status.HTTP_400_BAD_REQUEST)

        # Dynamically get domain from the incoming request
        base_url = os.getenv("WOOCOMMERCE_BASE_URL", request.build_absolute_uri('/').rstrip('/'))

        callback_url = f"{base_url}/shopify/woocommerce/callback"

        consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
        consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")

        if not all([consumer_key, consumer_secret]):
            return Response(
                {"error": "WooCommerce credentials missing in .env"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Build parameters to simulate auth URL
        params = urlencode({
            "store_url": store_url,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "callback_url": callback_url
        })

        auth_url = f"{callback_url}?{params}"

        return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)


class WooCommerceCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            store_url = request.query_params.get('store_url')
            consumer_key = request.query_params.get('consumer_key')
            consumer_secret = request.query_params.get('consumer_secret')
            callback_url = request.query_params.get('callback_url')

            return Response({
                "message": "WooCommerce callback received.",
                "store_url": store_url,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "callback_url": callback_url
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Print full traceback to your terminal or console
            traceback.print_exc()

            return Response({
                "status_code": 500,
                "detail": str(e),  
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
            
# class WooCommerceProductsAPIView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request):
#         return Response({"message": "WooCommerce Products API is working"})
            
class WooCommerceProductsAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            store_url = request.query_params.get("store_url")
            consumer_key = request.query_params.get("consumer_key")
            consumer_secret = request.query_params.get("consumer_secret")

            if not all([store_url, consumer_key, consumer_secret]):
                return Response(
                    {"status_code": 400, "detail": "Missing one or more required parameters."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response = requests.get(
                f"{store_url}/wp-json/wc/v3/products",
                auth=(consumer_key, consumer_secret),
                timeout=10
            )

            if response.status_code != 200:
                return Response(
                    {"status_code": response.status_code, "detail": "Failed to fetch products."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                "status_code": 200,
                "products": response.json()
            })
        except Exception as e:
            return Response({
                "status_code": 500,
                "detail": str(e),
                "trace": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    
class WooCommerceCompareProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_url = request.query_params.get("store_url")
        product_id = request.query_params.get("product_id")
        consumer_key = request.query_params.get("consumer_key")
        consumer_secret = request.query_params.get("consumer_secret")

        if not all([store_url, product_id, consumer_key, consumer_secret]):
            return Response({"error": "Missing required query parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wcapi = API(
                url=store_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3"
            )

            # Fetch WooCommerce product
            response = wcapi.get(f"products/{product_id}")
            if response.status_code != 200:
                return Response({"error": "Product not found in WooCommerce store"}, status=404)

            woocommerce_product = response.json()

            # Quote title for external search
            woocommerce_title = quote(woocommerce_product.get("name", ""))
            external_product = amazon_products(woocommerce_title, 1)

            if external_product:
                Ai_response = connect_to_market_recon(external_product, dict(woocommerce_product))
                return Response({"message": "Market recommends!", "data": Ai_response}, status=200)
            else:
                return Response({"error": "Competitor product with title not found"}, status=400)

        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
    
# ==============================
# BigCommerce Integration
# ==============================
class BigCommerceAuthRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        refresh = RefreshToken.for_user(request.user)
        state = base64.urlsafe_b64encode(str(refresh.access_token).encode()).decode()

        params = {
            "client_id": settings.BIGCOMMERCE_CLIENT_ID,
            "redirect_uri": settings.BIGCOMMERCE_REDIRECT_URI,
            "scope": settings.BIGCOMMERCE_SCOPES,
            "response_type": "code",
            "state": state,
        }

        url = f"https://login.bigcommerce.com/oauth2/authorize?{urlencode(params)}"
        return Response({"url": url})


class BigCommerceCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        context = request.GET.get("context")
        scope = request.GET.get("scope")
        state = request.GET.get("state")

        if not code or not context or not state:
            return Response({"error": "Missing required parameters"}, status=400)

        # Validate state (JWT token) and confirm user
        try:
            decoded_state = base64.urlsafe_b64decode(state).decode()
            access_token = AccessToken(decoded_state)
            if str(request.user.id) != str(access_token["user_id"]):
                return Response({"error": "State token does not match user"}, status=400)
        except Exception as e:
            logger.error(f"State validation error: {str(e)}")
            return Response({"error": "Invalid state parameter"}, status=400)

        # Extract store_hash from context
        try:
            if not context.startswith("stores/"):
                return Response({"error": "Invalid context format"}, status=400)
            store_hash = context.split("/")[1]
        except Exception as e:
            return Response({"error": f"Context parsing failed: {str(e)}"}, status=400)

        token_url = "https://login.bigcommerce.com/oauth2/token"
        payload = {
            "client_id": settings.BIGCOMMERCE_CLIENT_ID,
            "client_secret": settings.BIGCOMMERCE_CLIENT_SECRET,
            "redirect_uri": settings.BIGCOMMERCE_REDIRECT_URI,
            "grant_type": "authorization_code",
            "code": code,
            "context": context,
            "scope": scope,
        }

        try:
            # You can also use headers={"Content-Type": "application/json"} and json=payload
            response = requests.post(token_url, data=payload)
            response.raise_for_status()
            data = response.json()

            BigCommerceStore.objects.update_or_create(
                store_hash=store_hash,
                defaults={
                    "user": request.user,
                    "access_token": data.get("access_token"),
                    "scope": data.get("scope", ""),
                    "context": data.get("context", context),
                },
            )

            return Response({
                "message": "BigCommerce store connected successfully!",
                "store_hash": store_hash,
            })

        except requests.exceptions.RequestException as e:
            error_msg = f"Token request failed: {str(e)}"
            if e.response:
                logger.error(f"{error_msg} - {e.response.text}")
            else:
                logger.error(error_msg)
            return Response({"error": "Failed to obtain access token"}, status=400)


# ==============================
# Custom store integration
# ==============================

class IsOwner(permissions.BasePermission):
    """ Custom permission to allow only owners to manage their objects """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ---------- Custom Store Views ----------
class StoreListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomStoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomStore.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"message": "Shop created successfully", "data": response.data}, status=status.HTTP_201_CREATED)


class StoreRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomStoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return CustomStore.objects.filter(user=self.request.user)


# ---------- Category Views ----------
class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            return Category.objects.filter(shop__id=shop_id)
        return Category.objects.all()


class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Category.objects.all()
    lookup_field = 'pk'


# ---------- Custom Product Views ----------
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop')
        category_id = self.request.query_params.get('category')

        queryset = CustomProduct.objects.all()

        if shop_id:
            queryset = queryset.filter(shop__id=shop_id)
        if category_id:
            queryset = queryset.filter(category__id=category_id)
            
        return queryset
            

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = CustomProduct.objects.all()
    lookup_field = 'pk'

