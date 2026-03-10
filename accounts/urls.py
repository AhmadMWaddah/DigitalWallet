"""
Accounts app URL configuration.

Defines authentication-related URL patterns.
"""

from django.urls import path

from .views import ClientRegistrationView, CustomLoginView, LoginRedirectView, LogoutView
from .views_reset import ClientPasswordResetConfirmView, ClientPasswordResetView

app_name = "accounts"

urlpatterns = [
    # -- Authentication
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login-redirect/", LoginRedirectView.as_view(), name="login_redirect"),
    path("register/", ClientRegistrationView.as_view(), name="register"),
    # -- Client Password Reset
    path("password-reset/", ClientPasswordResetView.as_view(), name="password_reset_client"),
    path(
        "reset-password/<uidb64>/<token>/",
        ClientPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
