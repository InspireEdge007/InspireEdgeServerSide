# from rest_framework_simplejwt.views import TokenRefreshView
# from .views import (
#     RegisterAPIView, VerifyOTPAPIView, LoginAPIView,
#     RoleListCreateAPIView, AssignRoleAPIView,
#     AdminDashboardAPIView, UserProfileAPIView, ResendOTPAPIView,
#     ForgotPasswordAPIView, ResetPasswordAPIView

# )

# urlpatterns = [
    
#     # old paths
#     path('register', RegisterAPIView.as_view(), name='register'),
#     path('verify-otp', VerifyOTPAPIView.as_view(), name='verify-otp'),
#     path('resend-otp', ResendOTPAPIView.as_view(), name='resend-otp'),

#     path('login', LoginAPIView.as_view(), name='login'),
#     path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

#     path('roles', RoleListCreateAPIView.as_view(), name='role-list-create'),
#     path('assign-role', AssignRoleAPIView.as_view(), name='assign-role'),

#     path('admin-dashboard', AdminDashboardAPIView.as_view(), name='admin-dashboard'),
#     path('profile', UserProfileAPIView.as_view(), name='user-profile'),

#     path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
#     path('reset-password/', ResetPasswordAPIView.as_view(), name='reset-password')

    

#  ]



from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
from customauth.views import (
    RegisterAPIView, VerifyOTPAPIView, LoginAPIView,
    RoleListCreateAPIView, AssignRoleAPIView,
    AdminDashboardAPIView, UserProfileAPIView, ResendOTPAPIView,
    ForgotPasswordAPIView, ResetPasswordAPIView,
    GoogleLogin
)

urlpatterns = [

    path("api/auth/google/", GoogleLogin.as_view(), name="google_login"),
    
    # normal auth and reg
    path("register", RegisterAPIView.as_view(), name="register"),
    path("verify-otp", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("resend-otp", ResendOTPAPIView.as_view(), name="resend-otp"),
    path("login", LoginAPIView.as_view(), name="login"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    
    path("roles", RoleListCreateAPIView.as_view(), name="role-list-create"),
    path("assign-role", AssignRoleAPIView.as_view(), name="assign-role"),
    
    path("admin-dashboard", AdminDashboardAPIView.as_view(), name="admin-dashboard"),
    path("profile", UserProfileAPIView.as_view(), name="user-profile"),


]