from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
import requests

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

# class WooCommerceAuthView(APIView):
#     def post(self, request):
#         data = request.data
#         site_url = data.get("store_url")
#         consumer_key = data.get("consumer_key")
#         consumer_secret = data.get("consumer_secret")

#         try:
#             wcapi = API(
#                 url=site_url,
#                 consumer_key=consumer_key,
#                 consumer_secret=consumer_secret,
#                 version="wc/v3"
#             )

#             response = wcapi.get("products")  # Test call

#             if response.status_code == 200:
#                 return Response({"message": "WooCommerce store connected!"}, status=200)
#             else:
#                 return Response({"error": "Failed to connect"}, status=response.status_code)

#         except Exception as e:
#             return Response({"error": str(e)}, status=400)


# ==============================
# BigCommerce Integration
# ==============================

class BigCommerceAuthRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = {
            "client_id" : settings.BIGCOMMERCE_CLIENT_ID,
            "redirect_uri" : settings.BIGCOMMERCE_REDIRECT_URI,
            "scope" : settings.BIGCOMMERCE_SCOPES,
            "response_type": "code",
            "context" : "store",
        }
        
        url = f"https://login.bigcommerce.com/oauth2/authorize?{urlencode(params)}"
        
        return Response({"url": url})



class BigCommerceCallbackView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.GET.get("code")
        context = request.GET.get("context")
        scope = request.GET.get("scope")

        if not code or not context:
            return Response({"error": "Missing required parameters"}, status=400)

        token_url = "https://login.bigcommerce.com/oauth2/token"
        payload = {
            "client_id": settings.BIGCOMMERCE_CLIENT_ID,
            "client_secret": settings.BIGCOMMERCE_CLIENT_SECRET,
            "redirect_uri": settings.BIGCOMMERCE_REDIRECT_URI,
            "grant_type": "authorization_code",
            "code": code,
            "scope": scope,
            "context": context,
        }

        try:
            response = requests.post(token_url, json=payload)
            response.raise_for_status()
            data = response.json()

            context_str = data.get("context", "")
            parts = context_str.split("/")
            if len(parts) != 2 or parts[0] != "store":
                logger.error(f"Invalid context format: {context_str}")
                return Response({"error": f"Invalid context format: {context_str}"}, status=400)

            store_hash = parts[1]

            user = request.user if request.user.is_authenticated else None

            BigCommerceStore.objects.update_or_create(
                store_hash=store_hash,
                defaults={
                    "user": user,
                    "access_token": data["access_token"],
                    "scope": data.get("scope", ""),
                    "context": context_str,
                },
            )

            return Response({"message": "BigCommerce store connected!"})

        except requests.RequestException as e:
            logger.error(f"Token request failed: {str(e)}")
            return Response({"error": "Failed to fetch access token"}, status=500)

        except Exception as e:
            logger.exception("Unexpected error occurred during BigCommerce callback")
            return Response({"error": f"Internal error: {str(e)}"}, status=500)




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
