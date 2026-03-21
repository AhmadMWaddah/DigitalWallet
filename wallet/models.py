"""
Wallet app models.

Defines Wallet and Transaction models for financial operations.
"""

from decimal import Decimal

from django.db import models

from accounts.models import ClientProfile

# -- Transaction Type Choices


class TransactionType(models.TextChoices):
    """Transaction type enumeration."""

    DEPOSIT = "DEPOSIT", "Deposit"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
    TRANSFER = "TRANSFER", "Transfer"


class TransactionStatus(models.TextChoices):
    """Transaction status enumeration."""

    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    FLAGGED = "FLAGGED", "Flagged"


# -- Wallet Model


class Wallet(models.Model):
    """
    Wallet model for client users.

    Stores balance and provides methods for financial operations.
    """

    # -- Core Fields

    client_profile = models.OneToOneField(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="The client profile associated with this wallet.",
    )

    balance = models.DecimalField(
        "Balance",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current wallet balance.",
    )

    is_frozen = models.BooleanField(
        "Frozen",
        default=False,
        help_text="Indicates if the wallet is frozen (no operations allowed).",
    )

    # -- Timestamps

    created_at = models.DateTimeField(
        "Created At",
        auto_now_add=True,
        help_text="When this wallet was created.",
    )

    updated_at = models.DateTimeField(
        "Updated At",
        auto_now=True,
        help_text="When this wallet was last updated.",
    )

    # -- Metadata

    class Meta:
        db_table = "wallet_wallet"
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Wallet - {self.client_profile.user.email} (${self.balance:.2f})"

    def can_operate(self):
        """Check if wallet can perform operations."""
        return not self.is_frozen

    def get_balance(self):
        """Return current balance as Decimal."""
        return self.balance


# -- Transaction Model


class Transaction(models.Model):
    """
    Transaction model for financial ledger.

    Records all financial operations with full audit trail.
    """

    # -- Core Fields

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="The primary wallet for this transaction.",
    )

    counterparty_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counterparty_transactions",
        help_text="The counterparty wallet (for transfers).",
    )

    amount = models.DecimalField(
        "Amount",
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount.",
    )

    type = models.CharField(
        "Type",
        max_length=10,
        choices=TransactionType.choices,
        help_text="Type of transaction.",
    )

    status = models.CharField(
        "Status",
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        help_text="Current transaction status.",
    )

    description = models.TextField(
        "Description",
        blank=True,
        help_text="Transaction description or notes.",
    )

    reference_id = models.CharField(
        "Reference ID",
        max_length=100,
        unique=True,
        help_text="Unique reference for idempotency.",
    )

    metadata = models.JSONField(
        "Metadata",
        blank=True,
        default=dict,
        help_text="Additional data for audit trail.",
    )

    # -- Timestamps

    created_at = models.DateTimeField(
        "Created At",
        auto_now_add=True,
        db_index=True,
        help_text="When this transaction was created.",
    )

    # -- Metadata

    class Meta:
        db_table = "wallet_transaction"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["wallet", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - ${self.amount:.2f} ({self.get_status_display()})"

    def is_completed(self):
        """Check if transaction is completed."""
        return self.status == TransactionStatus.COMPLETED

    def is_flagged(self):
        """Check if transaction is flagged for review."""
        return self.status == TransactionStatus.FLAGGED
