"""
Wallet app views.

Dashboard and transaction views with HTMX interactivity.
"""

import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from accounts.models import ClientProfile
from accounts.views import ClientOnlyMixin

from .forms import DepositForm, TransferForm, WithdrawForm
from .models import Transaction, Wallet
from .services import deposit_funds, transfer_funds, withdraw_funds
from .tasks import generate_statement_pdf, get_task_status

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
    Transaction history view for HTMX with Load More functionality.

    Returns HTML partial of transactions for pagination.
    """

    def get(self, request):
        """Return transaction history partial or full page."""
        # Check if this is an HTMX request
        if request.headers.get("HX-Request"):
            # HTMX request - return partial
            return self.get_partial(request)
        else:
            # Direct request - return full page
            return self.get_full_page(request)

    def get_partial(self, request):
        """Return transaction history partial for HTMX."""
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 5))

        try:
            wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            return render(request, "wallet/partials/empty_transactions.html")

        # Get transactions with offset and limit
        all_transactions = wallet.transactions.select_related(
            "counterparty_wallet__client_profile__user"
        ).order_by("-created_at")

        transactions = list(all_transactions[offset:offset + limit])

        # Check if there are more transactions
        has_more = (offset + limit) < all_transactions.count()
        next_offset = offset + limit if has_more else None

        html = render_to_string(
            "wallet/partials/transaction_list.html",
            {
                "transactions": transactions,
                "has_more": has_more,
                "next_offset": next_offset,
                "limit": limit,
                "wallet": wallet,
            },
            request=request,
        )

        return HttpResponse(html)

    def get_full_page(self, request):
        """Return full transaction history page."""
        try:
            wallet = request.user.client_profile.wallet
            transactions = wallet.transactions.select_related(
                "counterparty_wallet__client_profile__user"
            ).order_by("-created_at")[:50]
        except Wallet.DoesNotExist:
            transactions = []

        return render(request, "wallet/transactions.html", {"transactions": transactions})


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

    def get(self, request):
        """Display deposit page."""
        form = DepositForm()
        return render(request, "wallet/deposit.html", {"form": form})

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

                # For HTMX requests, return just the message
                if request.headers.get("HX-Request"):
                    return HttpResponse(message_html)

                # For regular requests, return JSON
                return JsonResponse({"success": True, "message": f"Deposited ${transaction.amount:.2f}"})

            except Exception as e:
                error_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "danger", "message": str(e)},
                        )()
                    },
                    request=request,
                )
                if request.headers.get("HX-Request"):
                    return HttpResponse(error_html)
                return JsonResponse({"success": False, "error": str(e)})
        else:
            # Return form with errors for HTMX
            if request.headers.get("HX-Request"):
                form_html = render_to_string(
                    "wallet/partials/deposit_form.html",
                    {"form": form},
                    request=request,
                )
                return HttpResponse(form_html)

            # For regular requests, return JSON with errors
            return JsonResponse({"success": False, "errors": form.errors})


class WithdrawView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Withdraw view handling HTMX POST.

    Processes withdrawal and returns updated balance + success message.
    """

    def get(self, request):
        """Display withdraw page."""
        form = WithdrawForm()
        return render(request, "wallet/withdraw.html", {"form": form})

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

                # For HTMX requests, return just the message
                if request.headers.get("HX-Request"):
                    return HttpResponse(message_html)

                # For regular requests, return JSON
                return JsonResponse({"success": True, "message": f"Withdrew ${transaction.amount:.2f}"})

            except Exception as e:
                error_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "danger", "message": str(e)},
                        )()
                    },
                    request=request,
                )
                if request.headers.get("HX-Request"):
                    return HttpResponse(error_html)
                return JsonResponse({"success": False, "error": str(e)})
        else:
            # Return form with errors for HTMX
            if request.headers.get("HX-Request"):
                form_html = render_to_string(
                    "wallet/partials/withdraw_form.html",
                    {"form": form},
                    request=request,
                )
                return HttpResponse(form_html)
            
            # For regular requests, return JSON with errors
            return JsonResponse({"success": False, "errors": form.errors})


class TransferView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Transfer view handling HTMX POST.

    Processes transfer and returns updated balance + success message.
    """

    def get(self, request):
        """Display transfer page."""
        form = TransferForm()
        return render(request, "wallet/transfer.html", {"form": form})

    def post(self, request):
        """Handle transfer form submission."""
        # Get sender wallet for form validation
        try:
            sender_wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            error_html = render_to_string(
                "components/alert.html",
                {
                    "message": type(
                        "Message",
                        (),
                        {"tags": "danger", "message": "Wallet not found."},
                    )()
                },
                request=request,
            )
            if request.headers.get("HX-Request"):
                return HttpResponse(error_html)
            return JsonResponse({"success": False, "error": "Wallet not found."})

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

                # For HTMX requests, return just the message
                if request.headers.get("HX-Request"):
                    return HttpResponse(message_html)

                # For regular requests, return JSON
                return JsonResponse({"success": True, "message": f"Transferred ${transaction.amount:.2f}"})

            except ClientProfile.DoesNotExist:
                error_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "danger", "message": "Recipient not found."},
                        )()
                    },
                    request=request,
                )
                if request.headers.get("HX-Request"):
                    return HttpResponse(error_html)
                return JsonResponse({"success": False, "error": "Recipient not found."})
            except Exception as e:
                error_html = render_to_string(
                    "components/alert.html",
                    {
                        "message": type(
                            "Message",
                            (),
                            {"tags": "danger", "message": str(e)},
                        )()
                    },
                    request=request,
                )
                if request.headers.get("HX-Request"):
                    return HttpResponse(error_html)
                return JsonResponse({"success": False, "error": str(e)})
        else:
            # Return form with errors for HTMX
            if request.headers.get("HX-Request"):
                form_html = render_to_string(
                    "wallet/partials/transfer_form.html",
                    {"form": form},
                    request=request,
                )
                return HttpResponse(form_html)

            # For regular requests, return JSON with errors
            return JsonResponse({"success": False, "errors": form.errors})


class StatementFormPartialView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Return the statement request form partial.

    Used to reset the form after download or error.
    """

    def get(self, request):
        """Return the form partial HTML."""
        html = render_to_string(
            "wallet/partials/statement_form.html",
            {},
            request=request,
        )
        return HttpResponse(html)


class StatementRequestView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Statement request view for generating PDF statements.

    Handles form submission and triggers async PDF generation.
    """

    def post(self, request):
        """
        Handle statement request form submission.

        Triggers Celery task to generate PDF and returns progress bar for polling.
        """
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            html = render_to_string(
                "wallet/partials/statement_error.html",
                {"error": "Both start date and end date are required."},
                request=request,
            )
            return HttpResponse(html)

        try:
            wallet = request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            html = render_to_string(
                "wallet/partials/statement_error.html",
                {"error": "Wallet not found."},
                request=request,
            )
            return HttpResponse(html)

        # Trigger async task
        task = generate_statement_pdf.delay(
            wallet_id=wallet.id, start_date_str=start_date, end_date_str=end_date
        )

        # Return progress bar for HTMX polling
        html = render_to_string(
            "wallet/partials/statement_progress.html",
            {"task_id": task.id, "progress": 10},
            request=request,
        )
        return HttpResponse(html)


class TaskStatusView(LoginRequiredMixin, View):
    """
    Task status view for HTMX polling.

    Returns HTML fragment based on task state (PENDING/STARTED/SUCCESS/FAILURE).
    """

    def get(self, request, task_id):
        """
        Get task status and return appropriate HTML fragment.

        States:
        - PENDING/STARTED: Progress bar with polling
        - SUCCESS: Download button
        - FAILURE: Error message with retry option
        """
        # Get status from cache directly (more reliable)
        from django.core.cache import cache

        status_data = cache.get(f"task_status_{task_id}")

        # Fallback to task function if cache miss
        if not status_data:
            status_data = get_task_status(task_id)

        status = status_data.get("status", "PENDING")

        if status in ["PENDING", "STARTED"]:
            # Return progress bar with continued polling
            progress = status_data.get("progress", 0) or status_data.get("info", {}).get("progress", 0)
            html = render_to_string(
                "wallet/partials/statement_progress.html",
                {"task_id": task_id, "progress": progress},
                request=request,
            )
            return HttpResponse(html)

        elif status == "SUCCESS":
            # Return download button
            result = status_data.get("result", {})
            file_path = result.get("file_path")
            # Construct download URL with task_id for the view
            download_url = reverse("wallet:statement_download", kwargs={"task_id": task_id})
            html = render_to_string(
                "wallet/partials/statement_download.html",
                {
                    "task_id": task_id,
                    "file_path": file_path,
                    "download_url": download_url,
                    "success": result.get("success", False),
                },
                request=request,
            )
            return HttpResponse(html)

        elif status == "FAILURE":
            # Return error message
            html = render_to_string(
                "wallet/partials/statement_error.html",
                {"task_id": task_id, "error": status_data.get("error", "Unknown error occurred")},
                request=request,
            )
            return HttpResponse(html)

        # Default: return unknown state
        html = render_to_string(
            "wallet/partials/statement_progress.html",
            {"task_id": task_id, "progress": 0},
            request=request,
        )
        return HttpResponse(html)


class StatementDownloadView(LoginRequiredMixin, ClientOnlyMixin, View):
    """
    Statement download view with ownership verification.

    Ensures users can only download their own statements.
    """

    def get(self, request, task_id):
        """
        Download generated statement after verifying ownership.

        Security: Verifies that the statement belongs to the requesting user.
        """
        import os

        from django.core.cache import cache
        from django.http import FileResponse

        # Get task result from cache (more reliable than AsyncResult)
        task_result = cache.get(f"task_result_{task_id}")

        if not task_result or not isinstance(task_result, dict):
            return JsonResponse({"success": False, "error": "Statement not found. Please generate a new statement."})

        if not task_result.get("success"):
            return JsonResponse({"success": False, "error": task_result.get("error", "Statement generation failed.")})

        # Security check: Verify wallet ownership
        wallet_id = task_result.get("wallet_id")
        if not wallet_id:
            return JsonResponse({"success": False, "error": "Invalid statement data."})

        try:
            wallet = Wallet.objects.select_related("client_profile__user").get(pk=wallet_id)
            # Verify ownership
            if wallet.client_profile.user != request.user:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Access denied. This statement does not belong to you.",
                    }
                )
        except Wallet.DoesNotExist:
            return JsonResponse({"success": False, "error": "Statement not found."})

        # Get file path from cache result
        file_path = task_result.get("file_path")
        if not file_path:
            return JsonResponse({"success": False, "error": "File path not found."})

        # Construct full path and serve file
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if not os.path.exists(full_path):
            return JsonResponse({"success": False, "error": "File not found on server."})

        # Serve the file as attachment
        response = FileResponse(open(full_path, "rb"), content_type="application/pdf", as_attachment=True)
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response


class TransactionListView(LoginRequiredMixin, ClientOnlyMixin, ListView):
    """
    Full transaction history page with pagination.

    Displays all user transactions with standard pagination.
    """

    model = Transaction
    template_name = "wallet/transaction_list_page.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        """Get user's transactions ordered by date."""
        try:
            wallet = self.request.user.client_profile.wallet
            return Transaction.objects.filter(
                wallet=wallet
            ).select_related(
                "counterparty_wallet__client_profile__user"
            ).order_by("-created_at")
        except Wallet.DoesNotExist:
            return Transaction.objects.none()

    def get_context_data(self, **kwargs):
        """Add wallet to context."""
        context = super().get_context_data(**kwargs)
        try:
            context["wallet"] = self.request.user.client_profile.wallet
        except Wallet.DoesNotExist:
            context["wallet"] = None
        return context
