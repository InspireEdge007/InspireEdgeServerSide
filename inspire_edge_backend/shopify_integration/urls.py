# shopify_integration/urls.py

from django.urls import path
from .views import ShopifyAuthRedirectView, ShopifyCallbackView

urlpatterns = [
    path('auth', ShopifyAuthRedirectView.as_view(), name='shopify-auth'),
    path('callback', ShopifyCallbackView.as_view(), name='shopify-callback'),
]
