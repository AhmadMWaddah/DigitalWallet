"""
Operations app URL configuration.

Staff dashboard and fraud management URLs.
"""

from django.urls import path

from .views import (
    FreezeWalletView,
    ReviewTransactionView,
    StaffDashboardView,
    UnfreezeWalletView,
)

app_name = "operations"

urlpatterns = [
    path("dashboard/", StaffDashboardView.as_view(), name="staff_dashboard"),
    path(
        "transaction/<int:transaction_id>/review/",
        ReviewTransactionView.as_view(),
        name="review_transaction",
    ),
    path("wallet/<int:wallet_id>/freeze/", FreezeWalletView.as_view(), name="freeze_wallet"),
    path("wallet/<int:wallet_id>/unfreeze/", UnfreezeWalletView.as_view(), name="unfreeze_wallet"),
]
