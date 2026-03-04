"""
Accounts app URL configuration.

Defines authentication-related URL patterns.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from .views import ClientRegistrationView, CustomLoginView, LoginRedirectView, LogoutView

app_name = "accounts"

urlpatterns = [
    # -- Authentication
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login-redirect/", LoginRedirectView.as_view(), name="login_redirect"),
    path("register/", ClientRegistrationView.as_view(), name="register"),
    # -- Password Reset (Django built-in)
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
