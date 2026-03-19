"""
Analytics app URL configuration.

JSON endpoints for Chart.js dashboard.
"""

from django.urls import path

from .views import SpendingByCategoryView, SpendingByMonthView

app_name = "analytics"

urlpatterns = [
    path("api/spending-by-category/", SpendingByCategoryView.as_view(), name="spending_by_category"),
    path("api/spending-by-month/", SpendingByMonthView.as_view(), name="spending_by_month"),
]
