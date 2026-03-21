"""
Fraud Detection Engine for Digital Wallet.

Implements Constitutional fraud detection rules:
- Rule 1: Any TRANSFER > $10,000
- Rule 2: > 5 transfers in the last 1 hour for a single user
- Rule 3: Any TRANSFER > $1,000 for accounts created in the last 7 days
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)


class FraudEngine:
    """
    Fraud detection engine for transaction monitoring.

    Evaluates transactions against Constitutional fraud detection rules
    and returns flags for suspicious activity.
    """

    # -- Constitutional Rule Thresholds

    # Rule 1: Large transfer threshold
    LARGE_TRANSFER_THRESHOLD = Decimal("10000.00")

    # Rule 2: Maximum transfers per hour before flagging
    MAX_TRANSFERS_PER_HOUR = 5

    # Rule 3: New account threshold (days) and amount
    NEW_ACCOUNT_DAYS = 7
    NEW_ACCOUNT_TRANSFER_THRESHOLD = Decimal("1000.00")

    @classmethod
    def check_transaction(cls, transaction):
        """
        Check a transaction against all fraud detection rules.

        Args:
            transaction: Transaction instance to evaluate

        Returns:
            dict: Evaluation result containing:
                - is_flagged: Boolean indicating if transaction should be flagged
                - rules_triggered: List of rule IDs that were triggered
                - reasons: List of human-readable reasons for flags
        """
        result = {
            "is_flagged": False,
            "rules_triggered": [],
            "reasons": [],
        }

        # Only check TRANSFER transactions
        if transaction.type != "TRANSFER":
            return result

        # Rule 1: Large transfer > $10,000
        if cls._check_large_transfer(transaction):
            result["is_flagged"] = True
            result["rules_triggered"].append("RULE_1")
            result["reasons"].append(
                f"Large transfer: ${transaction.amount:,.2f} exceeds ${cls.LARGE_TRANSFER_THRESHOLD:,.2f} threshold"
            )
            logger.warning(
                "FRAUD ALERT: Transaction #%d flagged - Rule 1 triggered (Large Transfer > $10,000). "
                "Amount: $%s, User: %s",
                transaction.id,
                transaction.amount,
                transaction.wallet.client_profile.user.email,
            )

        # Rule 2: > 5 transfers in last hour
        if cls._check_frequent_transfers(transaction):
            result["is_flagged"] = True
            result["rules_triggered"].append("RULE_2")
            result["reasons"].append(
                f"Frequent transfers: More than {cls.MAX_TRANSFERS_PER_HOUR} transfers in the last hour"
            )
            logger.warning(
                "FRAUD ALERT: Transaction #%d flagged - Rule 2 triggered (Frequent Transfers). "
                "User: %s, Count: >%d/hour",
                transaction.id,
                transaction.wallet.client_profile.user.email,
                cls.MAX_TRANSFERS_PER_HOUR,
            )

        # Rule 3: New account with large transfer > $1,000
        if cls._check_new_account_transfer(transaction):
            result["is_flagged"] = True
            result["rules_triggered"].append("RULE_3")
            result["reasons"].append(
                f"New account transfer: ${transaction.amount:,.2f} exceeds ${cls.NEW_ACCOUNT_TRANSFER_THRESHOLD:,.2f} threshold for accounts < {cls.NEW_ACCOUNT_DAYS} days old"
            )
            logger.warning(
                "FRAUD ALERT: Transaction #%d flagged - Rule 3 triggered (New Account Large Transfer). "
                "Amount: $%s, User: %s, Account Age: <%d days",
                transaction.id,
                transaction.amount,
                transaction.wallet.client_profile.user.email,
                cls.NEW_ACCOUNT_DAYS,
            )

        # Log if transaction was flagged
        if result["is_flagged"]:
            logger.info(
                "Transaction #%d flagged with rules: %s",
                transaction.id,
                ", ".join(result["rules_triggered"]),
            )

        return result

    @classmethod
    def _check_large_transfer(cls, transaction):
        """
        Rule 1: Check if transfer exceeds large transfer threshold.

        Args:
            transaction: Transaction instance

        Returns:
            bool: True if transfer > $10,000
        """
        return transaction.amount > cls.LARGE_TRANSFER_THRESHOLD

    @classmethod
    def _check_frequent_transfers(cls, transaction):
        """
        Rule 2: Check if user has made > 5 transfers in the last hour.

        Args:
            transaction: Transaction instance

        Returns:
            bool: True if user has > 5 transfers in last hour
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)

        # Count transfers from this wallet in the last hour
        # Exclude the current transaction from the count
        transfer_count = transaction.wallet.transactions.filter(
            type="TRANSFER",
            created_at__gte=one_hour_ago,
        ).exclude(pk=transaction.pk).count()

        # If count >= MAX_TRANSFERS_PER_HOUR, this would be the (MAX+1)th transfer
        return transfer_count >= cls.MAX_TRANSFERS_PER_HOUR

    @classmethod
    def _check_new_account_transfer(cls, transaction):
        """
        Rule 3: Check if transfer is from a new account (< 7 days) and > $1,000.

        Args:
            transaction: Transaction instance

        Returns:
            bool: True if account is < 7 days old and transfer > $1,000
        """
        # Get wallet owner's account creation date
        wallet = transaction.wallet
        user = wallet.client_profile.user

        account_age = timezone.now() - user.date_joined
        is_new_account = account_age.days < cls.NEW_ACCOUNT_DAYS

        # Check if transfer amount exceeds threshold for new accounts
        exceeds_threshold = transaction.amount > cls.NEW_ACCOUNT_TRANSFER_THRESHOLD

        return is_new_account and exceeds_threshold

    @classmethod
    def get_flagged_transactions(cls, queryset=None):
        """
        Get all flagged transactions from a queryset.

        Args:
            queryset: Optional Transaction queryset to filter

        Returns:
            QuerySet: Filtered to only FLAGGED transactions
        """
        from wallet.models import Transaction

        if queryset is None:
            queryset = Transaction.objects.all()

        return queryset.filter(status="FLAGGED")

    @classmethod
    def get_user_transfer_count_last_hour(cls, user):
        """
        Get the number of transfers a user has made in the last hour.

        Args:
            user: User instance

        Returns:
            int: Number of transfers in last hour
        """
        from wallet.models import Transaction

        one_hour_ago = timezone.now() - timedelta(hours=1)

        try:
            wallet = user.client_profile.wallet
            return wallet.transactions.filter(
                type="TRANSFER",
                created_at__gte=one_hour_ago,
            ).count()
        except AttributeError:
            # User has no wallet or client profile
            return 0
