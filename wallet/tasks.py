"""
Celery tasks for the Wallet app.

This module defines all background tasks related to wallet operations.
"""

import uuid
from datetime import datetime

from celery import shared_task
from django.core.cache import cache

from wallet.models import Wallet
from wallet.utils.pdf_generator import generate_statement_pdf_to_media


@shared_task(bind=True)
def generate_statement_pdf(self, wallet_id: int, start_date_str: str, end_date_str: str) -> dict:
    """
    Generate a PDF statement for a wallet's transactions within a date range.

    This task generates a professional PDF statement including:
    - Account information
    - Balance summary
    - Transaction history

    Args:
        self: Task instance (for bind=True)
        wallet_id: Primary key of the wallet
        start_date_str: Start date in ISO format (YYYY-MM-DD)
        end_date_str: End date in ISO format (YYYY-MM-DD)

    Returns:
        dict: Task result containing:
            - success: Boolean indicating success
            - file_path: Relative path to generated PDF (if successful)
            - error: Error message (if failed)
            - wallet_id: Wallet ID for reference
    """
    # Generate unique task ID
    task_id = self.request.id if hasattr(self, "request") and self.request else str(uuid.uuid4())

    # SECURITY: Get wallet early to bind task to owner
    try:
        wallet = Wallet.objects.select_related("client_profile__user").get(pk=wallet_id)
        task_owner_id = wallet.client_profile.user_id
    except Wallet.DoesNotExist:
        result = {
            "success": False,
            "error": f"Wallet {wallet_id} not found",
            "wallet_id": wallet_id,
        }
        cache.set(f"task_result_{task_id}", result, timeout=3600)
        cache.set(
            f"task_status_{task_id}", {"status": "FAILURE", "error": result["error"]}, timeout=3600
        )
        return result

    try:
        # Update task state to STARTED
        if hasattr(self, "update_state"):
            self.update_state(state="STARTED", meta={"progress": 10})

        # Store task status in cache with OWNER BINDING
        # This ensures only the task creator can access status
        cache.set(
            f"task_status_{task_id}",
            {
                "status": "STARTED",
                "progress": 10,
                "task_owner_id": task_owner_id,  # SECURITY: Bind task to owner
            },
            timeout=3600,
        )

        # Parse dates
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Generate PDF
        file_path = generate_statement_pdf_to_media(
            wallet=wallet, start_date=start_date, end_date=end_date, task_id=task_id
        )

        result = {
            "success": True,
            "file_path": file_path,
            "wallet_id": wallet_id,
            "start_date": start_date_str,
            "end_date": end_date_str,
        }

        # Store result in cache for easy retrieval
        cache.set(f"task_result_{task_id}", result, timeout=3600)
        cache.set(f"task_status_{task_id}", {"status": "SUCCESS", "result": result}, timeout=3600)

        if hasattr(self, "update_state"):
            self.update_state(state="SUCCESS", meta={"progress": 100})

        return result

    except Wallet.DoesNotExist:
        result = {
            "success": False,
            "error": f"Wallet {wallet_id} not found",
            "wallet_id": wallet_id,
        }
        cache.set(f"task_result_{task_id}", result, timeout=3600)
        cache.set(
            f"task_status_{task_id}", {"status": "FAILURE", "error": result["error"]}, timeout=3600
        )
        return result

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "wallet_id": wallet_id,
        }
        cache.set(f"task_result_{task_id}", result, timeout=3600)
        cache.set(f"task_status_{task_id}", {"status": "FAILURE", "error": str(e)}, timeout=3600)
        return result


@shared_task
def get_task_status(task_id: str) -> dict:
    """
    Get the current status of a Celery task.

    Args:
        task_id: The Celery task ID

    Returns:
        dict: Task status information containing:
            - status: Current task state (PENDING, STARTED, SUCCESS, FAILURE)
            - info: Task metadata (progress, etc.)
            - result: Task result (if completed)
    """
    # First try to get status from cache (more reliable)
    cached_status = cache.get(f"task_status_{task_id}")
    if cached_status:
        return cached_status

    # Fallback to Celery AsyncResult
    from celery.result import AsyncResult

    result = AsyncResult(task_id)

    response = {
        "status": result.status,
        "task_id": task_id,
    }

    if result.status == "SUCCESS" and result.result:
        response["result"] = result.result
    elif result.status == "FAILURE":
        response["error"] = str(result.result) if result.result else "Unknown error"
    elif result.info and hasattr(result.info, "get"):
        response["info"] = result.info

    return response
