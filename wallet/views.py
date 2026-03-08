"""
Wallet app views.

Dashboard and transaction views with HTMX interactivity.
"""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView

from accounts.models import ClientProfile
from accounts.views import ClientOnlyMixin

from .forms import DepositForm, TransferForm, WithdrawForm
from .models import Wallet
from .services import deposit_funds, transfer_funds, withdraw_funds

CustomUser = get_user_model()


class DashboardView(LoginRequiredMixin, ClientOnlyMixin, TemplateView):
    """
    Client dashboard view.

    Displays wallet balance, recent transactions, and quick actions.
    """

    template_name = "wallet/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add wallet and recent transactions to context."""
        context = super().get_context_data(**kwargs)

        # Get user's wallet
        try:
            wallet = self.request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            wallet = None

        # Get recent transactions (last 20)
        transactions = []
        if wallet:
            transactions = wallet.transactions.select_related(
                "counterparty_wallet__client_profile__user"
            ).order_by("-created_at")[:20]

        context["wallet"] = wallet
        context["transactions"] = transactions
        context["deposit_form"] = DepositForm()
        context["withdraw_form"] = WithdrawForm()
        context["transfer_form"] = TransferForm()

        return context


class TransactionHistoryView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Transaction history view for HTMX infinite scroll.

    Returns HTML partial of transactions for pagination.
    """

    def get(self, request):
        """Return transaction history partial."""
        # Get cursor for pagination (timestamp of last loaded transaction)
        cursor = request.GET.get("cursor")
        limit = 20

        # Get user's wallet
        try:
            wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            return render(
                request,
                "wallet/partials/empty_transactions.html",
            )

        # Query transactions with cursor-based pagination
        if cursor:
            transactions = list(
                wallet.transactions.select_related("counterparty_wallet__client_profile__user")
                .filter(created_at__lt=cursor)
                .order_by("-created_at")[:limit]
            )
        else:
            transactions = list(
                wallet.transactions.select_related(
                    "counterparty_wallet__client_profile__user"
                ).order_by("-created_at")[:limit]
            )

        # Check if more transactions exist
        has_more = False
        if len(transactions) == limit:
            last_transaction = transactions[-1] if transactions else None
            if last_transaction:
                has_more = wallet.transactions.filter(
                    created_at__lt=last_transaction.created_at
                ).exists()

        # Get next cursor
        next_cursor = None
        if has_more and transactions:
            last_transaction = transactions[-1]
            next_cursor = last_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Render partial
        html = render_to_string(
            "wallet/partials/transaction_list.html",
            {
                "transactions": transactions,
                "has_more": has_more,
                "next_cursor": next_cursor,
            },
            request=request,
        )

        return JsonResponse({"html": html, "has_more": has_more})


class BalanceCardView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Balance card view for HTMX OOB updates.

    Returns updated balance card HTML.
    """

    def get(self, request):
        """Return updated balance card."""
        try:
            wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            wallet = None

        html = render_to_string(
            "components/balance_card.html",
            {"wallet": wallet, "last_updated": "Just now"},
            request=request,
        )

        return JsonResponse({"html": html})


class DepositView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Deposit view handling HTMX POST.

    Processes deposit and returns updated balance + success message.
    """

    def post(self, request):
        """Handle deposit form submission."""
        form = DepositForm(request.POST)

        if form.is_valid():
            try:
                wallet = request.user.client_profile.wallet

                # Process deposit
                transaction = deposit_funds(
                    wallet=wallet,
                    amount=form.cleaned_data["amount"],
                    description=form.cleaned_data.get("description", ""),
                    reference_id=f"DEP-{wallet.id}-{uuid.uuid4().hex[:12]}",
                )

                # Render success message
                message_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "success", "message": f"Deposited ${transaction.amount:.2f}"},
                        )()
                    },
                    request=request,
                )

                # Render updated balance
                balance_html = render_to_string(
                    "components/balance_card.html",
                    {"wallet": wallet, "last_updated": "Just now"},
                    request=request,
                )

                # Render updated transaction list
                transactions = wallet.transactions.select_related(
                    "counterparty_wallet__client_profile__user"
                ).order_by("-created_at")[:20]

                transactions_html = render_to_string(
                    "wallet/partials/transaction_list.html",
                    {"transactions": transactions, "has_more": False, "next_cursor": None},
                    request=request,
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": message_html,
                        "balance": balance_html,
                        "transactions": transactions_html,
                    }
                )

            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(e),
                    }
                )
        else:
            # Return form with errors
            form_html = render_to_string(
                "wallet/partials/deposit_form.html",
                {"form": form},
                request=request,
            )

            return JsonResponse(
                {
                    "success": False,
                    "form": form_html,
                    "errors": form.errors,
                }
            )


class WithdrawView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Withdraw view handling HTMX POST.

    Processes withdrawal and returns updated balance + success message.
    """

    def post(self, request):
        """Handle withdraw form submission."""
        form = WithdrawForm(request.POST)

        if form.is_valid():
            try:
                wallet = request.user.client_profile.wallet

                # Process withdrawal
                transaction = withdraw_funds(
                    wallet=wallet,
                    amount=form.cleaned_data["amount"],
                    description=form.cleaned_data.get("description", ""),
                    reference_id=f"WDR-{wallet.id}-{uuid.uuid4().hex[:12]}",
                )

                # Render success message
                message_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "success", "message": f"Withdrew ${transaction.amount:.2f}"},
                        )()
                    },
                    request=request,
                )

                # Render updated balance
                balance_html = render_to_string(
                    "components/balance_card.html",
                    {"wallet": wallet, "last_updated": "Just now"},
                    request=request,
                )

                # Render updated transaction list
                transactions = wallet.transactions.select_related(
                    "counterparty_wallet__client_profile__user"
                ).order_by("-created_at")[:20]

                transactions_html = render_to_string(
                    "wallet/partials/transaction_list.html",
                    {"transactions": transactions, "has_more": False, "next_cursor": None},
                    request=request,
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": message_html,
                        "balance": balance_html,
                        "transactions": transactions_html,
                    }
                )

            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(e),
                    }
                )
        else:
            # Return form with errors
            form_html = render_to_string(
                "wallet/partials/withdraw_form.html",
                {"form": form},
                request=request,
            )

            return JsonResponse(
                {
                    "success": False,
                    "form": form_html,
                    "errors": form.errors,
                }
            )


class TransferView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Transfer view handling HTMX POST.

    Processes transfer and returns updated balance + success message.
    """

    def post(self, request):
        """Handle transfer form submission."""
        # Get sender wallet for form validation
        try:
            sender_wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Wallet not found.",
                }
            )

        form = TransferForm(request.POST, sender_wallet=sender_wallet)

        if form.is_valid():
            try:
                # Get recipient wallet
                recipient_profile = ClientProfile.objects.select_related("wallet").get(
                    user__email=form.cleaned_data["recipient_email"]
                )
                receiver_wallet = recipient_profile.wallet

                # Process transfer
                transaction = transfer_funds(
                    sender_wallet=sender_wallet,
                    receiver_wallet=receiver_wallet,
                    amount=form.cleaned_data["amount"],
                    description=form.cleaned_data.get("description", ""),
                    reference_id=f"TRF-{sender_wallet.id}-{receiver_wallet.id}-{uuid.uuid4().hex[:12]}",
                )

                # Render success message
                message_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {
                                "tags": "success",
                                "message": f"Transferred ${transaction.amount:.2f} to {recipient_profile.user.email}",
                            },
                        )()
                    },
                    request=request,
                )

                # Render updated balance
                balance_html = render_to_string(
                    "components/balance_card.html",
                    {"wallet": sender_wallet, "last_updated": "Just now"},
                    request=request,
                )

                # Render updated transaction list
                transactions = sender_wallet.transactions.select_related(
                    "counterparty_wallet__client_profile__user"
                ).order_by("-created_at")[:20]

                transactions_html = render_to_string(
                    "wallet/partials/transaction_list.html",
                    {"transactions": transactions, "has_more": False, "next_cursor": None},
                    request=request,
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": message_html,
                        "balance": balance_html,
                        "transactions": transactions_html,
                    }
                )

            except ClientProfile.DoesNotExist:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Recipient not found.",
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(e),
                    }
                )
        else:
            # Return form with errors
            form_html = render_to_string(
                "wallet/partials/transfer_form.html",
                {"form": form},
                request=request,
            )

            return JsonResponse(
                {
                    "success": False,
                    "form": form_html,
                    "errors": form.errors,
                }
            )
