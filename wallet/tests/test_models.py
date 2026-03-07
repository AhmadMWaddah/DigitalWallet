"""
Tests for wallet app models.

Verifies Wallet and Transaction model behavior.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from accounts.models import UserType
from wallet.models import Transaction, TransactionStatus, TransactionType, Wallet

CustomUser = get_user_model()


@pytest.mark.django_db
class TestWalletModel:
    """Test Wallet model."""

    def test_create_wallet_success(self):
        """Test creating a wallet successfully."""
        user = CustomUser.objects.create_user(
            email="wallet-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        assert wallet.client_profile == user.client_profile
        assert wallet.balance == Decimal("0.00")
        assert wallet.is_frozen is False

    def test_wallet_default_balance_is_zero(self):
        """Test wallet default balance is zero."""
        user = CustomUser.objects.create_user(
            email="balance-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        assert wallet.balance == Decimal("0.00")

    def test_wallet_str_representation(self):
        """Test wallet string representation."""
        user = CustomUser.objects.create_user(
            email="str-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("1000.50")
        )

        assert "str-test@test.com" in str(wallet)
        assert "1000.50" in str(wallet)

    def test_wallet_can_operate_when_not_frozen(self):
        """Test wallet can operate when not frozen."""
        user = CustomUser.objects.create_user(
            email="frozen-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        assert wallet.can_operate() is True

    def test_wallet_cannot_operate_when_frozen(self):
        """Test wallet cannot operate when frozen."""
        user = CustomUser.objects.create_user(
            email="frozen2-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile, is_frozen=True)

        assert wallet.can_operate() is False

    def test_wallet_one_to_one_with_client_profile(self):
        """Test wallet has one-to-one relationship with client profile."""
        user = CustomUser.objects.create_user(
            email="onetoone-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        # Create wallet
        Wallet.objects.create(client_profile=user.client_profile)

        # Should not be able to create another wallet for same profile
        with pytest.raises(IntegrityError):
            Wallet.objects.create(client_profile=user.client_profile)


@pytest.mark.django_db
class TestTransactionModel:
    """Test Transaction model."""

    def test_create_transaction_success(self):
        """Test creating a transaction successfully."""
        user = CustomUser.objects.create_user(
            email="transaction-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("100.00"),
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            reference_id="TEST-001",
        )

        assert transaction.wallet == wallet
        assert transaction.amount == Decimal("100.00")
        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.status == TransactionStatus.COMPLETED

    def test_transaction_default_status_is_pending(self):
        """Test transaction default status is pending."""
        user = CustomUser.objects.create_user(
            email="pending-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("50.00"),
            type=TransactionType.WITHDRAWAL,
            reference_id="TEST-002",
        )

        assert transaction.status == TransactionStatus.PENDING

    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        user = CustomUser.objects.create_user(
            email="txn-str-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("250.75"),
            type=TransactionType.TRANSFER,
            status=TransactionStatus.FLAGGED,
            reference_id="TEST-003",
        )

        assert "Transfer" in str(transaction)
        assert "250.75" in str(transaction)
        assert "Flagged" in str(transaction)

    def test_transaction_is_completed_method(self):
        """Test transaction is_completed method."""
        user = CustomUser.objects.create_user(
            email="completed-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        completed_txn = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("100.00"),
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            reference_id="TEST-004",
        )

        pending_txn = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("50.00"),
            type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.PENDING,
            reference_id="TEST-005",
        )

        assert completed_txn.is_completed() is True
        assert pending_txn.is_completed() is False

    def test_transaction_is_flagged_method(self):
        """Test transaction is_flagged method."""
        user = CustomUser.objects.create_user(
            email="flagged-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        flagged_txn = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("10000.00"),
            type=TransactionType.TRANSFER,
            status=TransactionStatus.FLAGGED,
            reference_id="TEST-006",
        )

        normal_txn = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("100.00"),
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            reference_id="TEST-007",
        )

        assert flagged_txn.is_flagged() is True
        assert normal_txn.is_flagged() is False

    def test_transaction_reference_id_unique(self):
        """Test transaction reference_id is unique."""
        user = CustomUser.objects.create_user(
            email="unique-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        # Create first transaction
        Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("100.00"),
            type=TransactionType.DEPOSIT,
            reference_id="UNIQUE-001",
        )

        # Should not be able to create another with same reference_id
        with pytest.raises(IntegrityError):
            Transaction.objects.create(
                wallet=wallet,
                amount=Decimal("50.00"),
                type=TransactionType.WITHDRAWAL,
                reference_id="UNIQUE-001",
            )

    def test_transaction_created_at_indexed(self):
        """Test transaction created_at field is indexed."""
        # This test verifies the index exists by checking model Meta
        indexes = Transaction._meta.indexes
        index_fields = []
        for index in indexes:
            index_fields.extend(index.fields)

        assert "created_at" in index_fields


@pytest.mark.django_db
class TestWalletTransactionRelationship:
    """Test Wallet-Transaction relationship."""

    def test_wallet_has_many_transactions(self):
        """Test wallet can have many transactions."""
        user = CustomUser.objects.create_user(
            email="many-txn-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        # Create multiple transactions
        for i in range(5):
            Transaction.objects.create(
                wallet=wallet,
                amount=Decimal(f"{100 + i}.00"),
                type=TransactionType.DEPOSIT,
                reference_id=f"MANY-00{i}",
            )

        assert wallet.transactions.count() == 5

    def test_transaction_counterparty_nullable(self):
        """Test transaction counterparty_wallet is nullable for deposits/withdrawals."""
        user = CustomUser.objects.create_user(
            email="counterparty-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        # Deposit should not have counterparty
        deposit = Transaction.objects.create(
            wallet=wallet,
            amount=Decimal("500.00"),
            type=TransactionType.DEPOSIT,
            counterparty_wallet=None,
            reference_id="COUNTERPARTY-001",
        )

        assert deposit.counterparty_wallet is None
