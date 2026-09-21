"""
Wallet API URL configuration.

Versioned REST endpoints (v1) mounted under /api/v1/ by core.urls.
"""

from django.urls import path

from .api import (
    DepositAPIView,
    TransactionListView,
    TransferAPIView,
    WalletDetailView,
    WithdrawAPIView,
)

app_name = "wallet_api"

urlpatterns = [
    path("wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("deposit/", DepositAPIView.as_view(), name="deposit"),
    path("withdraw/", WithdrawAPIView.as_view(), name="withdraw"),
    path("transfer/", TransferAPIView.as_view(), name="transfer"),
]
