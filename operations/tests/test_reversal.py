"""
Tests for fraud reversal and service-layer logic.

Verifies:
- Reverse transfer restores funds correctly
- Process fraud review handles approve/reject actions
- Balance restoration works for both parties
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserType
from wallet.models import Transaction, TransactionStatus, Wallet
from wallet.services import process_fraud_review, reverse_transfer, transfer_funds

CustomUser = get_user_model()


@pytest.fixture
def flagged_transfer_setup(db):
    """Create a flagged transfer for testing reversal."""
    # Create sender
    sender = CustomUser.objects.create_user(
        email="sender@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    sender_wallet = Wallet.objects.create(
        client_profile=sender.client_profile,
        balance=Decimal("1000.00"),
    )

    # Create receiver
    receiver = CustomUser.objects.create_user(
        email="receiver@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    receiver_wallet = Wallet.objects.create(
        client_profile=receiver.client_profile,
        balance=Decimal("500.00"),
    )

    # Create a flagged transfer manually (simulating fraud detection)
    transfer = Transaction.objects.create(
        wallet=sender_wallet,
        counterparty_wallet=receiver_wallet,
        amount=Decimal("200.00"),
        type="TRANSFER",
        status=TransactionStatus.FLAGGED,
        reference_id="FLAGGED-TRF-001",
        description="Flagged transfer test",
        metadata={
            "flagged": True,
            "flag_reason": "Test flag",
            "flag_rules_triggered": ["RULE_1"],
        },
    )

    # Manually update balances to simulate transfer in progress
    sender_wallet.balance = Decimal("800.00")  # 1000 - 200
    sender_wallet.save()
    receiver_wallet.balance = Decimal("700.00")  # 500 + 200
    receiver_wallet.save()

    # Create staff user
    staff = CustomUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        user_type=UserType.STAFF,
    )

    return {
        "sender": sender,
        "sender_wallet": sender_wallet,
        "receiver": receiver,
        "receiver_wallet": receiver_wallet,
        "transfer": transfer,
        "staff": staff,
    }


class TestReverseTransfer:
    """Test reverse_transfer service function."""

    @pytest.mark.django_db
    def test_reverse_transfer_restores_balances(self, flagged_transfer_setup):
        """Test that reversing a transfer restores funds to sender."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        sender_wallet = setup["sender_wallet"]
        receiver_wallet = setup["receiver_wallet"]
        staff = setup["staff"]

        # Verify initial state (money has moved)
        assert sender_wallet.balance == Decimal("800.00")
        assert receiver_wallet.balance == Decimal("700.00")

        # Reverse the transfer
        result = reverse_transfer(transfer.id, staff)

        # Verify result
        assert result["success"] is True
        assert "restored to sender" in result["message"]

        # Verify balances restored
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()

        assert sender_wallet.balance == Decimal("1000.00"), (
            f"Sender should have $1000 restored, got ${sender_wallet.balance}"
        )
        assert receiver_wallet.balance == Decimal("500.00"), (
            f"Receiver should have $500 (original), got ${receiver_wallet.balance}"
        )

        # Verify original transaction status
        transfer.refresh_from_db()
        assert transfer.status == TransactionStatus.FAILED
        assert transfer.metadata["reversed"] is True
        assert transfer.metadata["reversed_by"] == "staff@test.com"

        # Verify reversal transaction created
        reversal_txn = result["reversal_transaction"]
        assert reversal_txn.status == TransactionStatus.FAILED
        assert reversal_txn.metadata["operation"] == "reversal"
        assert reversal_txn.metadata["original_transaction_id"] == transfer.id

    @pytest.mark.django_db
    def test_reverse_transfer_non_flagged_fails(self, flagged_transfer_setup):
        """Test that reversing a non-flagged transfer fails."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        staff = setup["staff"]

        # First approve it (making it non-flagged)
        transfer.status = TransactionStatus.COMPLETED
        transfer.save()

        # Try to reverse - should fail
        with pytest.raises(ValueError, match="not flagged"):
            reverse_transfer(transfer.id, staff)

    @pytest.mark.django_db
    def test_reverse_transfer_non_transfer_fails(self, db):
        """Test that reversing a non-transfer fails."""
        # Create a deposit
        user = CustomUser.objects.create_user(
            email="depositor@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        wallet = Wallet.objects.create(
            client_profile=user.client_profile,
            balance=Decimal("0.00"),
        )

        deposit = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("100.00"),
            type="DEPOSIT",
            status=TransactionStatus.FLAGGED,
            reference_id="FLAGGED-DEP-001",
        )

        staff = CustomUser.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            user_type=UserType.STAFF,
        )

        # Try to reverse - should fail (not a transfer)
        with pytest.raises(ValueError, match="not a transfer"):
            reverse_transfer(deposit.id, staff)


class TestProcessFraudReview:
    """Test process_fraud_review service function."""

    @pytest.mark.django_db
    def test_process_fraud_review_approve(self, flagged_transfer_setup):
        """Test approving a flagged transfer."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        sender_wallet = setup["sender_wallet"]
        receiver_wallet = setup["receiver_wallet"]
        staff = setup["staff"]

        # Verify initial state
        assert transfer.status == TransactionStatus.FLAGGED

        # Approve the transfer
        result = process_fraud_review(transfer.id, "approve", staff)

        # Verify result
        assert result["success"] is True
        assert "approved" in result["message"]

        # Verify transaction status
        transfer.refresh_from_db()
        assert transfer.status == TransactionStatus.COMPLETED
        assert transfer.metadata["review_action"] == "approved"
        assert transfer.metadata["reviewed_by"] == "staff@test.com"

        # Verify balances NOT changed (money already moved)
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("800.00")
        assert receiver_wallet.balance == Decimal("700.00")

    @pytest.mark.django_db
    def test_process_fraud_review_reject_transfer(self, flagged_transfer_setup):
        """Test rejecting a flagged transfer (should reverse)."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        sender_wallet = setup["sender_wallet"]
        receiver_wallet = setup["receiver_wallet"]
        staff = setup["staff"]

        # Verify initial state
        assert transfer.status == TransactionStatus.FLAGGED
        assert sender_wallet.balance == Decimal("800.00")
        assert receiver_wallet.balance == Decimal("700.00")

        # Reject the transfer
        result = process_fraud_review(transfer.id, "reject", staff)

        # Verify result
        assert result["success"] is True
        assert "reversed" in result["message"].lower()

        # Verify balances restored
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("1000.00")
        assert receiver_wallet.balance == Decimal("500.00")

        # Verify transaction status
        transfer.refresh_from_db()
        assert transfer.status == TransactionStatus.FAILED
        assert transfer.metadata["reversed"] is True

    @pytest.mark.django_db
    def test_process_fraud_review_invalid_action(self, flagged_transfer_setup):
        """Test invalid action fails."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        staff = setup["staff"]

        # Try invalid action
        with pytest.raises(ValueError, match="Invalid action"):
            process_fraud_review(transfer.id, "invalid_action", staff)

    @pytest.mark.django_db
    def test_process_fraud_review_non_flagged_fails(self, flagged_transfer_setup):
        """Test reviewing non-flagged transaction fails."""
        setup = flagged_transfer_setup
        transfer = setup["transfer"]
        staff = setup["staff"]

        # First approve it
        transfer.status = TransactionStatus.COMPLETED
        transfer.save()

        # Try to review - should fail
        with pytest.raises(ValueError, match="not flagged"):
            process_fraud_review(transfer.id, "approve", staff)


class TestIntegration:
    """Integration tests for full fraud review workflow."""

    @pytest.mark.django_db
    def test_full_fraud_workflow(self, db):
        """Test complete workflow: transfer -> flag -> reject -> reverse."""
        # Create sender with $500
        sender = CustomUser.objects.create_user(
            email="sender2@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile,
            balance=Decimal("500.00"),
        )

        # Create receiver with $100
        receiver = CustomUser.objects.create_user(
            email="receiver2@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile,
            balance=Decimal("100.00"),
        )

        # Create staff
        staff = CustomUser.objects.create_user(
            email="staff2@test.com",
            password="testpass123",
            user_type=UserType.STAFF,
        )

        # Create transfer (will be auto-flagged by FraudEngine if > $10,000)
        # For this test, we'll manually flag it
        transfer = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("50.00"),
            description="Test transfer",
        )

        # Manually flag it for testing
        transfer.status = TransactionStatus.FLAGGED
        transfer.metadata["flagged"] = True
        transfer.save()

        # Verify money moved
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("450.00")
        assert receiver_wallet.balance == Decimal("150.00")

        # Reject the transfer
        result = process_fraud_review(transfer.id, "reject", staff)

        assert result["success"] is True

        # Verify money restored
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("500.00")
        assert receiver_wallet.balance == Decimal("100.00")

        # Verify transaction status
        transfer.refresh_from_db()
        assert transfer.status == TransactionStatus.FAILED
