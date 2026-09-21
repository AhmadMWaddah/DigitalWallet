"""
Tests for transfer fees (1.5% + $0.20, sender-paid).

Fee is deducted on top of the transfer amount inside the same atomic
block and recorded as a FEE ledger entry. Deposits/withdrawals free.
"""

from decimal import Decimal

import pytest

from accounts.models import CustomUser, UserType
from wallet.models import Transaction, TransactionType, Wallet
from wallet.services import calculate_transfer_fee, transfer_funds


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


def _wallet_of(email):
    """Return the wallet belonging to the client with this email."""
    return Wallet.objects.get(client_profile__user__email=email)


class TestFeeMath:
    """Test pure fee calculation (1.5% + $0.20, half-up to cents)."""

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            (Decimal("100.00"), Decimal("1.70")),
            (Decimal("30.00"), Decimal("0.65")),
            (Decimal("0.01"), Decimal("0.20")),
            (Decimal("33.33"), Decimal("0.70")),
        ],
    )
    def test_fee_cases(self, amount, expected):
        """Test fee math across representative amounts."""
        assert calculate_transfer_fee(amount) == expected


class TestTransferFees:
    """Test fee deduction and ledger recording on transfers."""

    def test_sender_pays_amount_plus_fee(self, db):
        """Test sender debited amount + fee, receiver gets full amount."""
        _make_client("fee-snd@test.com", balance=Decimal("100.00"))
        _make_client("fee-rcv@test.com", balance=Decimal("10.00"))

        transfer_funds(
            sender_wallet=_wallet_of("fee-snd@test.com"),
            receiver_wallet=_wallet_of("fee-rcv@test.com"),
            amount=Decimal("30.00"),
            reference_id="FEE-TEST-1",
        )

        assert _wallet_of("fee-snd@test.com").balance == Decimal("69.35")
        assert _wallet_of("fee-rcv@test.com").balance == Decimal("40.00")

    def test_fee_ledger_entry(self, db):
        """Test FEE record exists, completed, with fee metadata."""
        _make_client("fee-led-s@test.com", balance=Decimal("100.00"))
        _make_client("fee-led-r@test.com", balance=Decimal("10.00"))

        transfer_funds(
            sender_wallet=_wallet_of("fee-led-s@test.com"),
            receiver_wallet=_wallet_of("fee-led-r@test.com"),
            amount=Decimal("30.00"),
            reference_id="FEE-TEST-2",
        )

        fee_tx = Transaction.objects.get(
            wallet=_wallet_of("fee-led-s@test.com"),
            type=TransactionType.FEE,
        )
        assert fee_tx.amount == Decimal("0.65")
        assert fee_tx.status == "COMPLETED"
        assert fee_tx.reference_id == "FEE-TEST-2-FEE"
        assert fee_tx.metadata["operation"] == "transfer_fee"

    def test_insufficient_for_fee_rejected(self, db):
        """Test balance covering amount but not fee is rejected."""
        _make_client("fee-poor@test.com", balance=Decimal("30.00"))
        _make_client("fee-rich@test.com", balance=Decimal("10.00"))

        with pytest.raises(Exception):
            transfer_funds(
                sender_wallet=_wallet_of("fee-poor@test.com"),
                receiver_wallet=_wallet_of("fee-rich@test.com"),
                amount=Decimal("30.00"),
                reference_id="FEE-TEST-3",
            )

        assert _wallet_of("fee-poor@test.com").balance == Decimal("30.00")

    def test_qr_transfer_also_charged(self, db):
        """Test QR-prefixed transfers go through the same fee path."""
        _make_client("fee-qr-s@test.com", balance=Decimal("100.00"))
        _make_client("fee-qr-r@test.com", balance=Decimal("10.00"))

        transfer_funds(
            sender_wallet=_wallet_of("fee-qr-s@test.com"),
            receiver_wallet=_wallet_of("fee-qr-r@test.com"),
            amount=Decimal("30.00"),
            reference_id="QR-1-2-abcdef123456",
        )

        assert _wallet_of("fee-qr-s@test.com").balance == Decimal("69.35")
        assert Transaction.objects.filter(
            wallet=_wallet_of("fee-qr-s@test.com"),
            type=TransactionType.FEE,
        ).exists()
