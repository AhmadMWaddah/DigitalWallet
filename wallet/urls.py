"""
Wallet app URL configuration.

Defines URLs for dashboard and transaction operations.
"""

from django.urls import path

from .views import (
    BalanceCardView,
    DashboardView,
    DepositView,
    TransactionHistoryView,
    TransferView,
    WithdrawView,
)

app_name = "wallet"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("transactions/history/", TransactionHistoryView.as_view(), name="transaction_history"),
    path("balance/", BalanceCardView.as_view(), name="balance"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
    path("transfer/", TransferView.as_view(), name="transfer"),
]
