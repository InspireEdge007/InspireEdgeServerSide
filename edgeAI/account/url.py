from . import views
from django.urls import path


urlpatterns = [
    path("register", views.register.as_views(), name="register"),
    path("send-otp/", views.SendOTPView.as_view(), name="send_otp"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),
    path("login/token", views.CustomTokenObtainPairView.as_view(), name="token_access"),
    path(
        "login/token/refresh-token",
        views.CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("logout", views.logout, name="logout"),
    path("update-profile", views.UserProfileView.as_view(), name="user_profile"),
    path("password-reset-email", views.reset_password, name="reset_token"),
    path(
        "reset/<uidb64>/<token>",
        views.password_reset_link_confirmation,
        name="password_reset_confirm",
    ),
    path("verify-email/<uidb64>", views.verify_email, name="verify_email"),
    path("set-new-password", views.set_new_password, name="password_reset_confirm"),
    path("waitlist", views.waitlist, name="waitlist"),

]