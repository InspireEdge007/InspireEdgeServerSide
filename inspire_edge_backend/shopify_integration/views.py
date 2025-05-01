from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
import requests

from .models import ShopifyStore
from django.contrib.auth import get_user_model

User = get_user_model()

# Step 1: Generate OAuth redirect URL
from rest_framework_simplejwt.tokens import RefreshToken
import base64

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