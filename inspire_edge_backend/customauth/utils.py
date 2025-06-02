from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response({
            'status_code': response.status_code,
            'detail': response.data
        }, status=response.status_code)
    
    return Response({
        'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'detail': 'Something went wrong. Please try again later.'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Teir payment control
def require_pro_tier(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.business_profile.subscription_tier in ['Pro', 'Enterprise']:
            return view_func(request, *args, **kwargs)
        return Response({'error': 'Upgrade required'}, status=status.HTTP_403_FORBIDDEN)
    return _wrapped_view
