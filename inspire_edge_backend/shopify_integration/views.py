from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError
from django.core.exceptions import ValidationError
import requests
from urllib.parse import quote
from customauth.permissions import IsPremiumUser
from django.utils import timezone

from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from .models import ShopifyStore
from django.contrib.auth import get_user_model
from .utils import amazon_products, connect_to_market_recon, connect_to_risk_delta_anomaly, connect_to_risk_delta_forecast, connect_to_strike_detect, connect_to_engagex_recommend,connect_to_vooice_analyze_feedback, connect_to_abandonment_freemium,connect_to_abandonment_premium
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

    permission_classes = [IsAuthenticated]
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

    permission_classes = [IsAuthenticated, IsPremiumUser]  # Ensure user has premium access

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

class RiskDeltaView(APIView):

    permission_classes = [IsAuthenticated, IsPremiumUser]  # Ensure user has premium access

    def post(self, request):

        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")
        mode = request.data.get('mode')
        periods = request.data.get('period', 'default')  # Default period if not specified

        if not shop or not shopify_product_id or not mode:
            return Response({"error": "Missing required parameters"}, status=400)

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

            # Connect to Risk Delta Forecast API
            print("connecting to risk delta forecast or anomaly")
            print(f"mode : {mode} , periods : {periods}")

            if mode == 'forecast':

                ai_response = connect_to_risk_delta_forecast(dict(shopify_product), period=periods)
                return Response({"message": "Risk delta forecast !", "data" : ai_response[0]}, status= ai_response[1])

            elif mode == 'anomaly':

                ai_response = connect_to_risk_delta_anomaly(dict(shopify_product), period=periods)
                return Response({"message": "Risk delta anomaly !", "data" : ai_response[0]}, status= ai_response[1])

            else:
                    # Handle other modes if necessary
                    return Response({"error": "Invalid mode specified"}, status=400)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)

class StrikeDetectEngagexView(APIView):

    permission_classes = [IsAuthenticated, IsPremiumUser]

    def post(self, request):
        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")
        mode = request.data.get('mode')
        limit = request.data.get('limit')

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


            # Connect to Strike or Engagex Forecast API
            if mode == 'strike':

                ai_response = connect_to_strike_detect(dict(shopify_product), limit)
                return Response({"message": "Strike!", "data" : ai_response[0]}, status=ai_response[1])

            elif mode == 'engagex':

                ai_response = connect_to_engagex_recommend(dict(shopify_product), limit)
                return Response({"message": "Engagex!", "data" : ai_response[0]}, status=ai_response[1])

            else:
                    # Handle other modes if necessary
                    return Response({"error": "Invalid mode specified"}, status=400)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)

class VooiceAnalyzeFeedbackView(APIView):
    permission_classes = [IsAuthenticated, IsPremiumUser]  # Ensure user has premium access

    def post(self, request):
        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")

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

            # Connect to Vooice Analyze Feedback API
            ai_response = connect_to_vooice_analyze_feedback(dict(shopify_product))
            return Response({"message": "Vooice feedback analysis !", "data" : ai_response[0]}, status=ai_response[1])

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)

class AbandonmentFreePremiumView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = request.query_params.get("shop")
        shopify_product_id = request.query_params.get("shopify_product_id")
        mode = request.data.get('mode')

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

            print(type(shopify_product))


            # Check premium status using your existing fields
            is_premium = (
                request.user.tier in ['pro', 'enterprise'] or
                (request.user.is_paid and
                request.user.subscription_end and
                request.user.subscription_end > timezone.now()) or
                (request.user.trial_end and
                request.user.trial_end > timezone.now() and
                not request.user.trial_used)
            )

            if mode == 'premium' and not is_premium:
                return Response(
                    {"error": "Premium feature requires Pro or Enterprise subscription"},
                    status=403
                )
            if mode == 'freemium':

                ai_response = connect_to_abandonment_freemium(dict(shopify_product))
                return Response({"message": "Abandonment freemium analysis !", "data" : ai_response}, status=200)

            elif mode == 'premium' and is_premium:

                ai_response = connect_to_abandonment_premium(dict(shopify_product))
                return Response({"message": "Abandonment premium analysis !", "data" : ai_response}, status=200)

            else:
                    # Handle other modes if necessary
                    return Response({"error": "Invalid mode specified"}, status=400)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=500)


