from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
import requests

from urllib.parse import urlencode
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from .models import ShopifyStore
from django.contrib.auth import get_user_model

# using fbv
from rest_framework.decorators import api_view, permission_classes



# woo and big commerce integration
from shopify_integration.models import *
from rest_framework import status
# from WooCommerce import API  # from 'woocommerce' Python package
import logging
logger = logging.getLogger(__name__)



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
from rest_framework.exceptions import PermissionDenied

import base64


User = get_user_model()

# Step 1: Generate OAuth redirect URL

class ShopifyAuthRedirectView(APIView):
    # permission_classes = [IsAuthenticated]

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


# Step 2: Handle callback and save token
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
    
    
# woo and big commerce integration   

# ==============================
# WooCommerce Integration
# ==============================


class WooCommerceAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        store_url = request.data.get("store_url")

        if not store_url:
            return Response({"error": "Store URL is required."}, status=400)

        callback_url = f"{settings.BASE_URL}/woocommerce/callback/"

        params = {
            "app_name": "YourAppName",
            "scope": "read_write",
            "user_id": str(request.user.id),
            "return_url": callback_url,
            "callback_url": callback_url,
        }

        # Build the full URL for authorization
        auth_url = f"{store_url}/wc-auth/v1/authorize?{urlencode(params)}"

        return Response({"url": auth_url})
    
class WooCommerceCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        store_url = request.GET.get("store_url")
        consumer_key = request.GET.get("consumer_key")
        consumer_secret = request.GET.get("consumer_secret")

        if not store_url or not consumer_key or not consumer_secret:
            return Response({"error": "Missing required parameters"}, status=400)

        WooCommerceStore.objects.update_or_create(
            store_url=store_url,
            defaults={
                "user": request.user,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
            },
        )

        return Response(
            {"message": "WooCommerce store connected successfully!", "store_url": store_url}
        )

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
