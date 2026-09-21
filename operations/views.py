"""
Operations app views.

Staff dashboard and fraud management views.
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accounts.models import ClientProfile, KYCStatus
from accounts.views import StaffOnlyMixin
from wallet.models import Transaction, TransactionStatus, Wallet
from wallet.services import freeze_wallet, unfreeze_wallet

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
        flagged_transactions = (
            Transaction.objects.filter(status=TransactionStatus.FLAGGED)
            .select_related(
                "wallet__client_profile__user",
                "counterparty_wallet__client_profile__user",
            )
            .order_by("-created_at")[:50]
        )

        # Get recent transactions (excluding flagged)
        recent_transactions = (
            Transaction.objects.exclude(status=TransactionStatus.FLAGGED)
            .select_related(
                "wallet__client_profile__user",
                "counterparty_wallet__client_profile__user",
            )
            .order_by("-created_at")[:20]
        )

        # System statistics
        total_users = CustomUser.objects.filter(user_type="CLIENT").count()

        total_deposits = Transaction.objects.filter(
            type="DEPOSIT", status=TransactionStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        flagged_count = Transaction.objects.filter(status=TransactionStatus.FLAGGED).count()

        # Pending KYC applications for staff review
        pending_kyc = (
            ClientProfile.objects.filter(kyc_status=KYCStatus.PENDING)
            .select_related("user")
            .order_by("kyc_submitted_at")[:50]
        )

        context["flagged_transactions"] = flagged_transactions
        context["recent_transactions"] = recent_transactions
        context["pending_kyc"] = pending_kyc
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
    Business logic delegated to wallet/services.py::process_fraud_review
    """

    def post(self, request, transaction_id):
        """Update transaction status based on staff review."""
        from wallet.services import process_fraud_review

        action = request.POST.get("action")
        is_htmx = request.headers.get("HX-Request") == "true"

        try:
            # Delegate to service layer
            result = process_fraud_review(
                transaction_id=transaction_id,
                action=action,
                staff_user=request.user,
            )

            # Get updated transaction
            transaction = get_object_or_404(Transaction, pk=transaction_id)

            # HTMX requests get the updated row HTML
            if is_htmx:
                html = render_to_string(
                    "operations/partials/transaction_row.html",
                    {"transaction": transaction},
                    request=request,
                )
                return HttpResponse(html)

            # Non-HTMX fallback: redirect with message (never raw JSON)
            messages.success(request, result["message"])
            return redirect("operations:staff_dashboard")

        except ValueError as e:
            if is_htmx:
                error_html = render_to_string(
                    "components/alert.html",
                    {"message": {"tags": "danger", "message": str(e)}},
                    request=request,
                )
                return HttpResponse(error_html)
            messages.error(request, str(e))
            return redirect("operations:staff_dashboard")


class FreezeWalletView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    HTMX view to freeze a user's wallet.

    Prevents all operations on the wallet until unfrozen.
    """

    def post(self, request, wallet_id):
        """Freeze the specified wallet."""
        is_htmx = request.headers.get("HX-Request") == "true"
        wallet = get_object_or_404(Wallet, pk=wallet_id)

        if wallet.is_frozen:
            error = "Wallet is already frozen."
            if is_htmx:
                error_html = render_to_string(
                    "components/alert.html",
                    {"message": {"tags": "danger", "message": error}},
                    request=request,
                )
                return HttpResponse(error_html)
            messages.error(request, error)
            return redirect("operations:staff_dashboard")

        reason = request.POST.get("reason", "Administrative action")
        freeze_wallet(wallet, reason=reason)

        # HTMX requests get the updated status HTML
        if is_htmx:
            html = render_to_string(
                "operations/partials/wallet_status.html",
                {"wallet": wallet},
                request=request,
            )
            return HttpResponse(html)

        # Non-HTMX fallback: redirect with message (never raw JSON)
        messages.success(request, f"Wallet #{wallet.id} has been frozen.")
        return redirect("operations:staff_dashboard")


class UnfreezeWalletView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    HTMX view to unfreeze a user's wallet.

    Restores wallet operations after staff review.
    """

    def post(self, request, wallet_id):
        """Unfreeze the specified wallet."""
        is_htmx = request.headers.get("HX-Request") == "true"
        wallet = get_object_or_404(Wallet, pk=wallet_id)

        if not wallet.is_frozen:
            error = "Wallet is not frozen."
            if is_htmx:
                error_html = render_to_string(
                    "components/alert.html",
                    {"message": {"tags": "danger", "message": error}},
                    request=request,
                )
                return HttpResponse(error_html)
            messages.error(request, error)
            return redirect("operations:staff_dashboard")

        unfreeze_wallet(wallet)

        # HTMX requests get the updated status HTML
        if is_htmx:
            html = render_to_string(
                "operations/partials/wallet_status.html",
                {"wallet": wallet},
                request=request,
            )
            return HttpResponse(html)

        # Non-HTMX fallback: redirect with message (never raw JSON)
        messages.success(request, f"Wallet #{wallet.id} has been unfrozen.")
        return redirect("operations:staff_dashboard")


class KYCReviewView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    Staff view to approve or reject KYC applications.

    Mirrors ReviewTransactionView shapes: alert HTML for HTMX,
    redirect with message otherwise.
    """

    def post(self, request, profile_id):
        """Approve or reject a pending KYC application."""
        is_htmx = request.headers.get("HX-Request") == "true"
        profile = get_object_or_404(ClientProfile, pk=profile_id)
        action = request.POST.get("action")
        reason = request.POST.get("reason", "").strip()

        def _fail(message):
            if is_htmx:
                return HttpResponse(
                    render_to_string(
                        "components/alert.html",
                        {"message": {"tags": "danger", "message": message}},
                        request=request,
                    )
                )
            messages.error(request, message)
            return redirect("operations:staff_dashboard")

        def _ok(message):
            if is_htmx:
                return HttpResponse(
                    render_to_string(
                        "components/alert.html",
                        {"message": {"tags": "success", "message": message}},
                        request=request,
                    )
                )
            messages.success(request, message)
            return redirect("operations:staff_dashboard")

        if profile.kyc_status != KYCStatus.PENDING:
            return _fail("Only pending applications can be reviewed.")

        if action == "approve":
            profile.kyc_status = KYCStatus.VERIFIED
            profile.kyc_verified = True
            profile.kyc_verified_at = timezone.now()
            profile.kyc_rejection_reason = ""
            profile.save(
                update_fields=[
                    "kyc_status",
                    "kyc_verified",
                    "kyc_verified_at",
                    "kyc_rejection_reason",
                ]
            )
            return _ok(f"KYC approved for {profile.user.email}.")

        if action == "reject":
            if not reason:
                return _fail("A rejection reason is required.")
            profile.kyc_status = KYCStatus.REJECTED
            profile.kyc_verified = False
            profile.kyc_rejection_reason = reason
            profile.save(update_fields=["kyc_status", "kyc_verified", "kyc_rejection_reason"])
            return _ok(f"KYC rejected for {profile.user.email}.")

        return _fail("Unknown action.")
