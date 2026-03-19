"""
Operations app views.

Staff dashboard and fraud management views.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView

from accounts.views import StaffOnlyMixin
from wallet.models import Transaction, TransactionStatus, Wallet
from wallet.services import flag_transaction, freeze_wallet, unfreeze_wallet

CustomUser = get_user_model()


class StaffDashboardView(LoginRequiredMixin, StaffOnlyMixin, TemplateView):
    """
    Staff dashboard for monitoring transactions and flagged activity.

    Displays:
    - High Alert section: All FLAGGED transactions
    - Recent transactions list
    - System statistics
    """

    template_name = "operations/staff_dashboard.html"

    def get_context_data(self, **kwargs):
        """Add system stats and transactions to context."""
        context = super().get_context_data(**kwargs)

        # Get flagged transactions (High Alert)
        flagged_transactions = Transaction.objects.filter(
            status=TransactionStatus.FLAGGED
        ).select_related(
            "wallet__client_profile__user",
            "counterparty_wallet__client_profile__user",
        ).order_by("-created_at")[:50]

        # Get recent transactions (excluding flagged)
        recent_transactions = Transaction.objects.exclude(
            status=TransactionStatus.FLAGGED
        ).select_related(
            "wallet__client_profile__user",
            "counterparty_wallet__client_profile__user",
        ).order_by("-created_at")[:20]

        # System statistics
        total_users = CustomUser.objects.filter(user_type="CLIENT").count()

        total_deposits = Transaction.objects.filter(
            type="DEPOSIT",
            status=TransactionStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        flagged_count = Transaction.objects.filter(
            status=TransactionStatus.FLAGGED
        ).count()

        context["flagged_transactions"] = flagged_transactions
        context["recent_transactions"] = recent_transactions
        context["stats"] = {
            "total_users": total_users,
            "total_volume": total_deposits,
            "flagged_count": flagged_count,
        }

        return context


class ReviewTransactionView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    HTMX view to review and update flagged transaction status.

    Allows staff to mark flagged transactions as COMPLETED or FAILED.
    """

    def post(self, request, transaction_id):
        """Update transaction status based on staff review."""
        action = request.POST.get("action")
        transaction = get_object_or_404(Transaction, pk=transaction_id)

        # Ensure transaction is flagged
        if transaction.status != TransactionStatus.FLAGGED:
            return JsonResponse({
                "success": False,
                "error": "Transaction is not flagged."
            })

        if action == "approve":
            transaction.status = TransactionStatus.COMPLETED
            transaction.metadata = {
                **transaction.metadata,
                "reviewed_by": request.user.email,
                "reviewed_at": transaction.created_at.isoformat(),
                "review_action": "approved",
            }
            transaction.save(update_fields=["status", "metadata"])

            message = f"Transaction #{transaction.id} approved and marked as COMPLETED."

        elif action == "reject":
            transaction.status = TransactionStatus.FAILED
            transaction.metadata = {
                **transaction.metadata,
                "reviewed_by": request.user.email,
                "reviewed_at": transaction.created_at.isoformat(),
                "review_action": "rejected",
            }
            transaction.save(update_fields=["status", "metadata"])

            message = f"Transaction #{transaction.id} rejected and marked as FAILED."

        else:
            return JsonResponse({
                "success": False,
                "error": "Invalid action. Use 'approve' or 'reject'."
            })

        # For HTMX requests, return updated row
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "operations/partials/transaction_row.html",
                {"transaction": transaction},
                request=request,
            )
            return HttpResponse(html)

        return JsonResponse({"success": True, "message": message})


class FreezeWalletView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    HTMX view to freeze a user's wallet.

    Prevents all operations on the wallet until unfrozen.
    """

    def post(self, request, wallet_id):
        """Freeze the specified wallet."""
        wallet = get_object_or_404(Wallet, pk=wallet_id)

        if wallet.is_frozen:
            return JsonResponse({
                "success": False,
                "error": "Wallet is already frozen."
            })

        reason = request.POST.get("reason", "Administrative action")
        freeze_wallet(wallet, reason=reason)

        # For HTMX requests, return updated status
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "operations/partials/wallet_status.html",
                {"wallet": wallet},
                request=request,
            )
            return HttpResponse(html)

        return JsonResponse({
            "success": True,
            "message": f"Wallet #{wallet.id} has been frozen."
        })


class UnfreezeWalletView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    HTMX view to unfreeze a user's wallet.

    Restores wallet operations after staff review.
    """

    def post(self, request, wallet_id):
        """Unfreeze the specified wallet."""
        wallet = get_object_or_404(Wallet, pk=wallet_id)

        if not wallet.is_frozen:
            return JsonResponse({
                "success": False,
                "error": "Wallet is not frozen."
            })

        unfreeze_wallet(wallet)

        # For HTMX requests, return updated status
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "operations/partials/wallet_status.html",
                {"wallet": wallet},
                request=request,
            )
            return HttpResponse(html)

        return JsonResponse({
            "success": True,
            "message": f"Wallet #{wallet.id} has been unfrozen."
        })
