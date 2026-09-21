"""
Wallet API serializers.

Read serializers expose wallet/transaction state; input serializers
validate write payloads before the service layer runs.
"""

from decimal import Decimal

from rest_framework import serializers

from .models import Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Read-only wallet state (balance renders as decimal string)."""

    class Meta:
        model = Wallet
        fields = ["id", "balance", "is_frozen", "updated_at"]
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    """Read-only transaction ledger entry."""

    class Meta:
        model = Transaction
        fields = [
            "id",
            "amount",
            "type",
            "status",
            "description",
            "reference_id",
            "counterparty_wallet",
            "created_at",
        ]
        read_only_fields = fields


class _MoneyInputSerializer(serializers.Serializer):
    """Shared amount/description/reference validation for money writes."""

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        default="",
    )
    reference_id = serializers.CharField(required=False, max_length=100)


class DepositInputSerializer(_MoneyInputSerializer):
    """Deposit payload validation."""


class WithdrawInputSerializer(_MoneyInputSerializer):
    """Withdraw payload validation."""


class TransferInputSerializer(_MoneyInputSerializer):
    """Transfer payload validation (recipient resolved from email)."""

    recipient_email = serializers.EmailField()
