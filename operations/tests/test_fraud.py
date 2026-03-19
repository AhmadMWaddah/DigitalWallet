"""
Tests for fraud detection engine.

Verifies Constitutional fraud detection rules:
- Rule 1: Any TRANSFER > $10,000
- Rule 2: > 5 transfers in the last 1 hour for a single user
- Rule 3: Any TRANSFER > $1,000 for accounts created in the last 7 days
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from accounts.models import UserType
from operations.fraud_engine import FraudEngine
from wallet.models import Transaction, Wallet
from wallet.services import transfer_funds


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    from accounts.models import ClientProfile, CustomUser

    user = CustomUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        user_type=UserType.STAFF,
    )
    return user


@pytest.fixture
def client_user_with_wallet(db):
    """Create a client user with wallet for testing."""
    from accounts.models import ClientProfile, CustomUser

    user = CustomUser.objects.create_user(
        email="client@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    wallet = Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("50000.00"))
    return user, wallet


@pytest.fixture
def new_account_user(db):
    """Create a new account user (created today) with wallet."""
    from accounts.models import ClientProfile, CustomUser

    user = CustomUser.objects.create_user(
        email="newuser@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    # Ensure account is very new (created today)
    user.date_joined = timezone.now()
    user.save()

    wallet = Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("5000.00"))
    return user, wallet


@pytest.fixture
def receiver_wallet(db):
    """Create a receiver wallet for testing."""
    from accounts.models import ClientProfile, CustomUser

    user = CustomUser.objects.create_user(
        email="receiver@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    wallet = Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("1000.00"))
    return wallet


class TestFraudEngineRule1:
    """Test Rule 1: Large transfer > $10,000."""

    @pytest.mark.django_db
    def test_flag_large_transfer_over_10k(self, client_user_with_wallet, receiver_wallet):
        """Test that transfers over $10,000 are flagged."""
        user, sender_wallet = client_user_with_wallet

        # Create a transaction over $10,000
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("15000.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE1-001",
        )

        result = FraudEngine.check_transaction(transaction)

        assert result["is_flagged"] is True
        assert "RULE_1" in result["rules_triggered"]
        assert any("10,000" in reason for reason in result["reasons"])

    @pytest.mark.django_db
    def test_no_flag_normal_transfer_under_10k(self, client_user_with_wallet, receiver_wallet):
        """Test that transfers under $10,000 are not flagged by Rule 1."""
        user, sender_wallet = client_user_with_wallet

        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("5000.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE1-002",
        )

        result = FraudEngine.check_transaction(transaction)

        # Should not be flagged by Rule 1 (might be flagged by other rules)
        assert "RULE_1" not in result["rules_triggered"]

    @pytest.mark.django_db
    def test_no_flag_deposit_any_amount(self, client_user_with_wallet):
        """Test that deposits are never flagged by Rule 1."""
        user, wallet = client_user_with_wallet

        transaction = Transaction.objects.create(
            wallet=wallet,
            counterparty_wallet=None,
            amount=Decimal("50000.00"),
            type="DEPOSIT",
            status="COMPLETED",
            reference_id="TEST-RULE1-003",
        )

        result = FraudEngine.check_transaction(transaction)

        # Deposits should not be checked by fraud engine
        assert result["is_flagged"] is False


class TestFraudEngineRule2:
    """Test Rule 2: > 5 transfers in the last 1 hour."""

    @pytest.mark.django_db
    def test_flag_frequent_transfers_over_5_in_hour(self, client_user_with_wallet, receiver_wallet):
        """Test that > 5 transfers in 1 hour triggers flag."""
        user, sender_wallet = client_user_with_wallet

        # Create 5 transfers in the last hour
        for i in range(5):
            Transaction.objects.create(
                wallet=sender_wallet,
                counterparty_wallet=receiver_wallet,
                amount=Decimal("100.00"),
                type="TRANSFER",
                status="COMPLETED",
                reference_id=f"TEST-RULE2-{i:03d}",
                created_at=timezone.now() - timedelta(minutes=i * 10),
            )

        # Create 6th transfer (should be flagged)
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE2-006",
        )

        result = FraudEngine.check_transaction(transaction)

        assert result["is_flagged"] is True
        assert "RULE_2" in result["rules_triggered"]
        assert any("5 transfers" in reason for reason in result["reasons"])

    @pytest.mark.django_db
    def test_no_flag_5_or_fewer_transfers(self, client_user_with_wallet, receiver_wallet):
        """Test that 5 or fewer transfers in 1 hour don't trigger flag."""
        user, sender_wallet = client_user_with_wallet

        # Create 4 transfers in the last hour
        for i in range(4):
            Transaction.objects.create(
                wallet=sender_wallet,
                counterparty_wallet=receiver_wallet,
                amount=Decimal("100.00"),
                type="TRANSFER",
                status="COMPLETED",
                reference_id=f"TEST-RULE2-FEW-{i:03d}",
                created_at=timezone.now() - timedelta(minutes=i * 10),
            )

        # Create 5th transfer (should NOT be flagged)
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE2-FEW-005",
        )

        result = FraudEngine.check_transaction(transaction)

        # Should not be flagged by Rule 2
        assert "RULE_2" not in result["rules_triggered"]

    @pytest.mark.django_db
    def test_no_flag_old_transfers(self, client_user_with_wallet, receiver_wallet):
        """Test that transfers older than 1 hour don't count."""
        user, sender_wallet = client_user_with_wallet

        # Create 10 transfers 2 hours ago (outside the 1-hour window)
        # Use a fixed time in the past to ensure consistency
        from datetime import datetime
        old_time = timezone.now() - timedelta(hours=2)
        
        for i in range(10):
            txn = Transaction.objects.create(
                wallet=sender_wallet,
                counterparty_wallet=receiver_wallet,
                amount=Decimal("100.00"),
                type="TRANSFER",
                status="COMPLETED",
                reference_id=f"TEST-RULE2-OLD-{i:03d}-{user.email}",
            )
            # Update created_at after creation to ensure it's in the past
            Transaction.objects.filter(pk=txn.pk).update(
                created_at=old_time - timedelta(minutes=i)
            )

        # Create new transfer (should NOT be flagged by Rule 2)
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id=f"TEST-RULE2-NEW-{user.email}-{timezone.now().isoformat()}",
        )

        result = FraudEngine.check_transaction(transaction)

        assert "RULE_2" not in result["rules_triggered"]


class TestFraudEngineRule3:
    """Test Rule 3: New account (< 7 days) with transfer > $1,000."""

    @pytest.mark.django_db
    def test_flag_new_account_large_transfer(self, new_account_user, receiver_wallet):
        """Test that new accounts transferring > $1,000 are flagged."""
        user, sender_wallet = new_account_user

        # Account is < 7 days old, transfer > $1,000
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("1500.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE3-001",
        )

        result = FraudEngine.check_transaction(transaction)

        assert result["is_flagged"] is True
        assert "RULE_3" in result["rules_triggered"]
        assert any("New account" in reason for reason in result["reasons"])

    @pytest.mark.django_db
    def test_no_flag_old_account_any_amount(self, client_user_with_wallet, receiver_wallet):
        """Test that old accounts can transfer any amount without Rule 3 flag."""
        user, sender_wallet = client_user_with_wallet

        # Ensure account is old (set date_joined to 30 days ago)
        user.date_joined = timezone.now() - timedelta(days=30)
        user.save()

        # Old account, large transfer
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("5000.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id=f"TEST-RULE3-OLD-{timezone.now().isoformat()}",
        )

        result = FraudEngine.check_transaction(transaction)

        # Should not be flagged by Rule 3 (account is old)
        assert "RULE_3" not in result["rules_triggered"]

    @pytest.mark.django_db
    def test_no_flag_new_account_small_amount(self, new_account_user, receiver_wallet):
        """Test that new accounts can transfer < $1,000 without Rule 3 flag."""
        user, sender_wallet = new_account_user

        # Account is < 7 days old, but transfer < $1,000
        transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("500.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id="TEST-RULE3-003",
        )

        result = FraudEngine.check_transaction(transaction)

        # Should not be flagged by Rule 3 (amount is small)
        assert "RULE_3" not in result["rules_triggered"]


class TestFraudEngineIntegration:
    """Test FraudEngine integration with wallet services."""

    @pytest.mark.django_db
    def test_transfer_over_10k_flagged_automatically(self, client_user_with_wallet, receiver_wallet):
        """Test that transfer_funds automatically flags transfers > $10,000."""
        user, sender_wallet = client_user_with_wallet

        # Perform transfer over $10,000
        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("15000.00"),
            description="Large transfer test",
        )

        # Transaction should be flagged
        assert transaction.status == "FLAGGED"
        assert "flagged" in transaction.metadata
        assert "RULE_1" in transaction.metadata.get("flag_rules_triggered", [])

    @pytest.mark.django_db
    def test_transfer_under_10k_not_flagged(self, client_user_with_wallet, receiver_wallet):
        """Test that normal transfers are not flagged."""
        user, sender_wallet = client_user_with_wallet

        # Perform normal transfer
        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("500.00"),
            description="Normal transfer test",
        )

        # Transaction should be completed (not flagged)
        assert transaction.status == "COMPLETED"

    @pytest.mark.django_db
    def test_new_account_transfer_flagged(self, new_account_user, receiver_wallet):
        """Test that new account transfers > $1,000 are flagged."""
        user, sender_wallet = new_account_user

        # Perform transfer from new account
        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("1500.00"),
            description="New account transfer",
        )

        # Transaction should be flagged
        assert transaction.status == "FLAGGED"
        assert "flagged" in transaction.metadata
        assert "RULE_3" in transaction.metadata.get("flag_rules_triggered", [])

    @pytest.mark.django_db
    def test_frequent_transfers_flagged(self, client_user_with_wallet, receiver_wallet):
        """Test that frequent transfers are flagged."""
        user, sender_wallet = client_user_with_wallet

        # Create 5 transfers first
        for i in range(5):
            transfer_funds(
                sender_wallet=sender_wallet,
                receiver_wallet=receiver_wallet,
                amount=Decimal("100.00"),
                description=f"Frequent transfer {i+1}",
            )

        # 6th transfer should be flagged
        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            description="Frequent transfer 6",
        )

        # Transaction should be flagged
        assert transaction.status == "FLAGGED"
        assert "flagged" in transaction.metadata
        assert "RULE_2" in transaction.metadata.get("flag_rules_triggered", [])

    @pytest.mark.django_db
    def test_flagged_transaction_metadata(self, client_user_with_wallet, receiver_wallet):
        """Test that flagged transactions have proper metadata."""
        user, sender_wallet = client_user_with_wallet

        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("15000.00"),
            description="Test metadata",
        )

        # Check metadata
        assert transaction.metadata["flagged"] is True
        assert "flag_reason" in transaction.metadata
        assert "flag_rules_triggered" in transaction.metadata
        assert "flagged_at" in transaction.metadata
        assert "RULE_1" in transaction.metadata["flag_rules_triggered"]


class TestFraudEngineHelperMethods:
    """Test FraudEngine helper methods."""

    @pytest.mark.django_db
    def test_get_flagged_transactions(self, client_user_with_wallet, receiver_wallet):
        """Test getting flagged transactions."""
        user, sender_wallet = client_user_with_wallet

        # Create a unique receiver for this test to avoid cross-test contamination
        from accounts.models import CustomUser
        test_user = CustomUser.objects.create_user(
            email=f"test-flagged-{user.email}",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        test_wallet = Wallet.objects.create(client_profile=test_user.client_profile, balance=Decimal("50000.00"))

        # Get initial flagged count for this specific wallet
        initial_flagged = FraudEngine.get_flagged_transactions().filter(wallet=sender_wallet).count()

        # Perform transfers that will be flagged (Rule 1: > $10,000)
        transfer_funds(sender_wallet, test_wallet, Decimal("15000.00"))  # Flagged
        transfer_funds(sender_wallet, test_wallet, Decimal("20000.00"))  # Flagged

        # Get new flagged count for this wallet
        new_flagged = FraudEngine.get_flagged_transactions().filter(wallet=sender_wallet).count()

        # Should have 2 new flagged transactions
        assert new_flagged - initial_flagged == 2

    @pytest.mark.django_db
    def test_get_user_transfer_count_last_hour(self, client_user_with_wallet, receiver_wallet):
        """Test getting user's transfer count in last hour."""
        user, sender_wallet = client_user_with_wallet

        # Create some transfers
        transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))
        transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))
        transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))

        # Get count
        count = FraudEngine.get_user_transfer_count_last_hour(user)

        assert count == 3
