# shopify_integration/urls.py

from django.urls import path
from .views import ShopifyAuthRedirectView, ShopifyCallbackView, CompareProductsView, FetchProductsView

urlpatterns = [
    path('auth', ShopifyAuthRedirectView.as_view(), name='shopify-auth'),
    path('callback', ShopifyCallbackView.as_view(), name='shopify-callback'),
    path('fetch-products', FetchProductsView.as_view(), name='shopify-products'),
    path('compare', CompareProductsView.as_view(), name='shopify-compare'),

    # woocommerce
    
]
