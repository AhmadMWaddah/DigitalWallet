"""
Wallet app URL configuration.
"""

from django.urls import path

from .views import DashboardView

app_name = "wallet"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]
