"""
Wallet app URL configuration.

Defines URLs for dashboard and transaction operations.
"""

from django.urls import path

from .views import (
    BalanceCardView,
    DashboardView,
    DepositView,
    StatementDownloadView,
    StatementRequestView,
    TaskStatusView,
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
    # Statement generation
    path("statement/request/", StatementRequestView.as_view(), name="statement_request"),
    path("statement/status/<str:task_id>/", TaskStatusView.as_view(), name="statement_status"),
    path(
        "statement/download/<str:task_id>/",
        StatementDownloadView.as_view(),
        name="statement_download",
    ),
]
