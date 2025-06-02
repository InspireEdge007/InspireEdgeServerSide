# store_integration/urls.py

from django.urls import path
from .views import ShopifyAuthRedirectView, ShopifyCallbackView, CompareProductsView, FetchProductsView, RiskDeltaView, StrikeDetectEngagexView, VooiceAnalyzeFeedbackView,AbandonmentFreePremiumView
from .views import (

    BigCommerceAuthRedirectView, BigCommerceCallbackView,
    StoreListCreateView, StoreRetrieveUpdateDestroyView,
    ProductListCreateView, ProductRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("auth", ShopifyAuthRedirectView.as_view(), name="shopify-auth"),
    path("callback", ShopifyCallbackView.as_view(), name="shopify-callback"),
    path('fetch-products', FetchProductsView.as_view(), name='shopify-products'),
    path('compare', CompareProductsView.as_view(), name='shopify-compare'),

    path('risk-delta', RiskDeltaView.as_view(), name='risk-delta'),
    path('strike-detect-engagex', StrikeDetectEngagexView.as_view(), name='strike-detect-engagex'),
    path('vooice-analyze-feedback', VooiceAnalyzeFeedbackView.as_view(), name='vooice-analyze-feedback'),
    path('abandonment', AbandonmentFreePremiumView.as_view(), name='abandonment-free-premium'),


    # path("woocommerce/connect", WooCommerceAuthView.as_view(), name="woocommerce-connect"),
    path("bigcommerce/auth", BigCommerceAuthRedirectView.as_view(), name="bigcommerce-auth"),
    path("bigcommerce/callback", BigCommerceCallbackView.as_view(), name="bigcommerce-callback"),


        # Store endpoints
    path('stores/', StoreListCreateView.as_view(), name='store-list-create'),
    path('stores/<int:pk>/', StoreRetrieveUpdateDestroyView.as_view(), name='store-detail'),


    # Product endpoints
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),

]

