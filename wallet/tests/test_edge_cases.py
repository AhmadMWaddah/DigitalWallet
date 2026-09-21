"""
Edge-case tests for wallet money flows.

Scope note: service-level edges (self-transfer, negative/zero amounts,
frozen wallets, insufficient funds, duplicate reference_id, concurrency)
are already covered in test_services.py / test_concurrency.py. This module
covers the gaps: ledger-balance invariant and view-level error paths.
"""

from decimal import Decimal

from django.urls import reverse

from accounts.models import CustomUser, UserType
from wallet.models import Transaction, TransactionStatus, Wallet
from wallet.services import deposit_funds, freeze_wallet, transfer_funds, withdraw_funds


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


class TestLedgerConsistency:
    """Test balance always equals initial plus net completed flow."""

    def test_balance_matches_completed_transactions(self, db):
        """Test flagged amounts credit the receiver but stay marked isolated."""
        sender = _make_client("ledger-a@test.com")
        receiver = _make_client("ledger-b@test.com", balance=Decimal("1000.00"))
        sender_wallet = sender.client_profile.wallet
        receiver_wallet = receiver.client_profile.wallet

        deposit_funds(wallet=sender_wallet, amount=Decimal("1000.00"), reference_id="LED-DEP-1")
        withdraw_funds(wallet=sender_wallet, amount=Decimal("200.00"), reference_id="LED-WDR-1")
        flagged = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("15000.00"),
            reference_id="LED-TRF-FLAG",
        )
        assert flagged.status == TransactionStatus.FLAGGED
        transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            reference_id="LED-TRF-1",
        )

        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()

        # Sender debited; receiver credited but flagged amount marked isolated
        # in metadata (reversal enforced at review time, not spend time).
        # Sender fees: 15000 -> 225.20, 100 -> 1.70.
        assert sender_wallet.balance == Decimal("35473.10")
        assert receiver_wallet.balance == Decimal("16100.00")
        assert receiver_wallet.metadata.get("isolated_LED-TRF-FLAG") == "15000.00"

        # Invariant from the ledger itself (sends/receives classified by
        # metadata operation; mirror rows live on the counterparty wallet):
        # balance == initial + deposits - withdrawals - sent + received
        # (both legs move immediately, whatever the status; FAILED rows
        # are excluded because rejection reverses the money)
        sid = sender_wallet.id

        def _op(txn):
            return (txn.metadata or {}).get("operation")

        ledger = list(Transaction.objects.filter(wallet_id=sid).exclude(status="FAILED"))
        credits = sum(
            (t.amount for t in ledger if t.type == "DEPOSIT"),
            Decimal("0.00"),
        ) + sum(
            (t.amount for t in ledger if _op(t) == "transfer_receive"),
            Decimal("0.00"),
        )
        debits = (
            sum(
                (t.amount for t in ledger if t.type == "WITHDRAWAL"),
                Decimal("0.00"),
            )
            + sum(
                (t.amount for t in ledger if _op(t) == "transfer_send"),
                Decimal("0.00"),
            )
            + sum(
                (t.amount for t in ledger if t.type == "FEE"),
                Decimal("0.00"),
            )
        )
        assert sender_wallet.balance == Decimal("50000.00") + credits - debits


class TestTransferViewEdges:
    """Test transfer view rejects invalid operations with usable errors."""

    def test_transfer_to_self_fails(self, client, db):
        """Test transferring to own email returns an error payload."""
        _make_client("self@test.com")
        client.login(email="self@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {"recipient_email": "self@test.com", "amount": "10.00"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_transfer_negative_amount_fails(self, client, db):
        """Test negative amounts fail form validation."""
        _make_client("neg-a@test.com")
        _make_client("neg-b@test.com")
        client.login(email="neg-a@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {"recipient_email": "neg-b@test.com", "amount": "-5.00"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_transfer_zero_amount_fails(self, client, db):
        """Test zero amounts fail form validation."""
        _make_client("zero-a@test.com")
        _make_client("zero-b@test.com")
        client.login(email="zero-a@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {"recipient_email": "zero-b@test.com", "amount": "0.00"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_transfer_from_frozen_wallet_fails(self, client, db):
        """Test frozen sender wallet blocks transfers."""
        sender = _make_client("frozen-a@test.com")
        _make_client("frozen-b@test.com")
        freeze_wallet(sender.client_profile.wallet, reason="edge test")
        client.login(email="frozen-a@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {"recipient_email": "frozen-b@test.com", "amount": "10.00"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_transfer_insufficient_funds_fails(self, client, db):
        """Test over-balance transfers fail validation."""
        _make_client("poor-a@test.com", balance=Decimal("5.00"))
        _make_client("poor-b@test.com")
        client.login(email="poor-a@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {"recipient_email": "poor-b@test.com", "amount": "500.00"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is False
