"""
Wallet app views.

Dashboard and transaction-related views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from accounts.views import ClientOnlyMixin


class DashboardView(LoginRequiredMixin, ClientOnlyMixin, TemplateView):
    """
    Client dashboard view.

    Displays wallet balance, recent transactions, and quick actions.
    """

    template_name = "wallet/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add dashboard context data."""
        context = super().get_context_data(**kwargs)

        # --#-- Placeholder data for Phase 3 testing
        # Will be replaced with real data in Phase 4
        context["wallet"] = type(
            "Wallet",
            (),
            {"balance": "12,850.75", "is_frozen": False},
        )()

        context["last_updated"] = "Just now"

        # Placeholder transactions for testing
        context["transactions"] = [
            type(
                "Transaction",
                (),
                {
                    "id": 1,
                    "type": "DEPOSIT",
                    "get_type_display": "Deposit",
                    "amount": "5000.00",
                    "created_at": None,
                    "status": "COMPLETED",
                    "get_status_display": "Completed",
                    "description": "Initial deposit",
                    "wallet": None,
                    "counterparty_wallet": None,
                },
            )(),
            type(
                "Transaction",
                (),
                {
                    "id": 2,
                    "type": "TRANSFER",
                    "get_type_display": "Transfer",
                    "amount": "250.00",
                    "created_at": None,
                    "status": "COMPLETED",
                    "get_status_display": "Completed",
                    "description": "Transfer to Alex",
                    "wallet": None,
                    "counterparty_wallet": True,
                },
            )(),
            type(
                "Transaction",
                (),
                {
                    "id": 3,
                    "type": "WITHDRAWAL",
                    "get_type_display": "Withdrawal",
                    "amount": "500.00",
                    "created_at": None,
                    "status": "PENDING",
                    "get_status_display": "Pending",
                    "description": "ATM withdrawal",
                    "wallet": None,
                    "counterparty_wallet": None,
                },
            )(),
        ]

        return context
