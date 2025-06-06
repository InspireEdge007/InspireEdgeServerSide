# store_integration/urls.py

from django.urls import path
from .views import (
    ShopifyAuthRedirectView, ShopifyCallbackView,
    CompareProductsView, FetchProductsView,
    WooCommerceAuthView, WooCommerceCallbackView, WooCommerceProductsAPIView, 
    WooCommerceCompareProductsView, BigCommerceAuthRedirectView, BigCommerceCallbackView,
    StoreListCreateView, StoreRetrieveUpdateDestroyView,
    CategoryListCreateView, CategoryRetrieveUpdateDestroyView,
    ProductListCreateView, ProductRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("auth", ShopifyAuthRedirectView.as_view(), name="shopify-auth"),
    path("callback", ShopifyCallbackView.as_view(), name="shopify-callback"),
    path('fetch-products', FetchProductsView.as_view(), name='shopify-products'),
    path('compare', CompareProductsView.as_view(), name='shopify-compare'),
    path("woocommerce/connect", WooCommerceAuthView.as_view(), name="woocommerce-connect"),
    path("woocommerce/callback/", WooCommerceCallbackView.as_view(), name="woocommerce-callback"),
    path("woocommerce/products/", WooCommerceProductsAPIView.as_view(), name="woocommerce-products"),
    path("woocommerce/compare/", WooCommerceCompareProductsView.as_view(), name="woocommerce-compare"),
    path("bigcommerce/auth", BigCommerceAuthRedirectView.as_view(), name="bigcommerce-auth"),
    path("bigcommerce/callback", BigCommerceCallbackView.as_view(), name="bigcommerce-callback"),
    
    
        # Store endpoints
    path('stores/', StoreListCreateView.as_view(), name='store-list-create'),
    path('stores/<int:pk>/', StoreRetrieveUpdateDestroyView.as_view(), name='store-detail'),

    # Category endpoints
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),

    # Product endpoints
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),

]

