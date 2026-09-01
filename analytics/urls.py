"""
Analytics app URL configuration.

JSON endpoints for Chart.js dashboard.
"""

from django.urls import path

from .views import (
    AnalyticsDashboardDataView,
    AnalyticsDashboardView,
    SpendingByCategoryView,
    SpendingByMonthView,
)

app_name = "analytics"

urlpatterns = [
    path("dashboard/", AnalyticsDashboardView.as_view(), name="analytics_dashboard"),
    path("dashboard/data/", AnalyticsDashboardDataView.as_view(), name="analytics_dashboard_data"),
    path(
        "api/spending-by-category/", SpendingByCategoryView.as_view(), name="spending_by_category"
    ),
    path("api/spending-by-month/", SpendingByMonthView.as_view(), name="spending_by_month"),
]
