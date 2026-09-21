"""
Wallet app URL configuration.

Defines URLs for dashboard and transaction operations.
"""

from django.urls import path

from .views import (
    BalanceCardView,
    DashboardView,
    DepositView,
    MyQRView,
    QRImageView,
    QRPayView,
    StatementDownloadView,
    StatementFormPartialView,
    StatementRequestView,
    TaskStatusView,
    TransactionHistoryView,
    TransactionListView,
    TransferView,
    WithdrawView,
)

app_name = "wallet"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("transactions/history/", TransactionHistoryView.as_view(), name="transaction_history"),
    path("transactions/", TransactionListView.as_view(), name="transaction_list"),
    path("balance/", BalanceCardView.as_view(), name="balance"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
    path("transfer/", TransferView.as_view(), name="transfer"),
    # QR scan-to-pay
    path("qr/", MyQRView.as_view(), name="my_qr"),
    path("qr/image/", QRImageView.as_view(), name="qr_image"),
    path("qr/pay/", QRPayView.as_view(), name="qr_pay"),
    # Statement generation
    path("statement/form/", StatementFormPartialView.as_view(), name="statement_form_partial"),
    path("statement/request/", StatementRequestView.as_view(), name="statement_request"),
    path("statement/status/<str:task_id>/", TaskStatusView.as_view(), name="statement_status"),
    path(
        "statement/download/<str:task_id>/",
        StatementDownloadView.as_view(),
        name="statement_download",
    ),
]
