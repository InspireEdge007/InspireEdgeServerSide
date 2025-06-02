# shopify_integration/urls.py

from django.urls import path
from .views import ShopifyAuthRedirectView, ShopifyCallbackView, CompareProductsView, FetchProductsView, RiskDeltaView, StrikeDetectEngagexView, VooiceAnalyzeFeedbackView,AbandonmentFreePremiumView

urlpatterns = [
    path('auth', ShopifyAuthRedirectView.as_view(), name='shopify-auth'),
    path('callback', ShopifyCallbackView.as_view(), name='shopify-callback'),
    path('fetch-products', FetchProductsView.as_view(), name='shopify-products'),
    path('compare', CompareProductsView.as_view(), name='shopify-compare'),

    path('risk-delta', RiskDeltaView.as_view(), name='risk-delta'),
    path('strike-detect-engagex', StrikeDetectEngagexView.as_view(), name='strike-detect-engagex'),
    path('vooice-analyze-feedback', VooiceAnalyzeFeedbackView.as_view(), name='vooice-analyze-feedback'),
    path('abandonment', AbandonmentFreePremiumView.as_view(), name='abandonment-free-premium'),



]
