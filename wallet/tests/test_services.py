"""
Tests for wallet service layer.

Verifies atomic financial operations with full validation.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserType
from wallet.exceptions import (
    DuplicateTransactionError,
    FrozenWalletError,
    InsufficientFundsError,
    InvalidAmountError,
    SelfTransferError,
)
from wallet.models import TransactionStatus, Wallet
from wallet.services import (
    deposit_funds,
    flag_transaction,
    freeze_wallet,
    transfer_funds,
    unfreeze_wallet,
    withdraw_funds,
)

CustomUser = get_user_model()


@pytest.mark.django_db
class TestDepositFunds:
    """Test deposit_funds service function."""

    def test_deposit_success(self):
        """Test successful deposit."""
        user = CustomUser.objects.create_user(
            email="deposit-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = deposit_funds(wallet, Decimal("1000.00"))

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("1000.00")
        assert transaction.amount == Decimal("1000.00")
        assert transaction.type == "DEPOSIT"
        assert transaction.status == TransactionStatus.COMPLETED

    def test_deposit_multiple_times(self):
        """Test multiple deposits accumulate."""
        user = CustomUser.objects.create_user(
            email="multi-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        deposit_funds(wallet, Decimal("500.00"))
        deposit_funds(wallet, Decimal("300.00"))
        deposit_funds(wallet, Decimal("200.00"))

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("1000.00")

    def test_deposit_with_custom_reference_id(self):
        """Test deposit with custom reference_id."""
        user = CustomUser.objects.create_user(
            email="ref-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = deposit_funds(wallet, Decimal("100.00"), reference_id="CUSTOM-REF-001")

        assert transaction.reference_id == "CUSTOM-REF-001"

    def test_deposit_duplicate_reference_id_raises_error(self):
        """Test deposit with duplicate reference_id raises error."""
        user = CustomUser.objects.create_user(
            email="dup-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        deposit_funds(wallet, Decimal("100.00"), reference_id="DUP-REF-001")

        with pytest.raises(DuplicateTransactionError):
            deposit_funds(wallet, Decimal("50.00"), reference_id="DUP-REF-001")

    def test_deposit_negative_amount_raises_error(self):
        """Test deposit with negative amount raises error."""
        user = CustomUser.objects.create_user(
            email="neg-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        with pytest.raises(InvalidAmountError):
            deposit_funds(wallet, Decimal("-100.00"))

    def test_deposit_zero_amount_raises_error(self):
        """Test deposit with zero amount raises error."""
        user = CustomUser.objects.create_user(
            email="zero-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        with pytest.raises(InvalidAmountError):
            deposit_funds(wallet, Decimal("0.00"))

    def test_deposit_to_frozen_wallet_raises_error(self):
        """Test deposit to frozen wallet raises error."""
        user = CustomUser.objects.create_user(
            email="frozen-deposit@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile, is_frozen=True)

        with pytest.raises(FrozenWalletError):
            deposit_funds(wallet, Decimal("100.00"))


@pytest.mark.django_db
class TestWithdrawFunds:
    """Test withdraw_funds service function."""

    def test_withdraw_success(self):
        """Test successful withdrawal."""
        user = CustomUser.objects.create_user(
            email="withdraw-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("1000.00")
        )

        transaction = withdraw_funds(wallet, Decimal("300.00"))

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("700.00")
        assert transaction.amount == Decimal("300.00")
        assert transaction.type == "WITHDRAWAL"

    def test_withdraw_insufficient_funds_raises_error(self):
        """Test withdrawal with insufficient funds raises error."""
        user = CustomUser.objects.create_user(
            email="insufficient-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("100.00")
        )

        with pytest.raises(InsufficientFundsError) as excinfo:
            withdraw_funds(wallet, Decimal("500.00"))

        assert "Insufficient funds" in str(excinfo.value)
        assert wallet.balance == Decimal("100.00")  # Balance unchanged

    def test_withdraw_exact_balance(self):
        """Test withdrawal of exact balance."""
        user = CustomUser.objects.create_user(
            email="exact-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("500.00")
        )

        withdraw_funds(wallet, Decimal("500.00"))

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("0.00")

    def test_withdraw_negative_amount_raises_error(self):
        """Test withdrawal with negative amount raises error."""
        user = CustomUser.objects.create_user(
            email="neg-withdraw@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("1000.00")
        )

        with pytest.raises(InvalidAmountError):
            withdraw_funds(wallet, Decimal("-100.00"))

    def test_withdraw_from_frozen_wallet_raises_error(self):
        """Test withdrawal from frozen wallet raises error."""
        user = CustomUser.objects.create_user(
            email="frozen-withdraw@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile,
            balance=Decimal("1000.00"),
            is_frozen=True,
        )

        with pytest.raises(FrozenWalletError):
            withdraw_funds(wallet, Decimal("100.00"))


@pytest.mark.django_db
class TestTransferFunds:
    """Test transfer_funds service function."""

    def test_transfer_success(self):
        """Test successful transfer between wallets."""
        sender = CustomUser.objects.create_user(
            email="sender@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="receiver@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("1000.00")
        )

        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile, balance=Decimal("0.00")
        )

        transaction = transfer_funds(sender_wallet, receiver_wallet, Decimal("300.00"))

        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()

        assert sender_wallet.balance == Decimal("700.00")
        assert receiver_wallet.balance == Decimal("300.00")
        assert transaction.amount == Decimal("300.00")
        assert transaction.type == "TRANSFER"

    def test_transfer_creates_two_records(self):
        """Test transfer creates transaction records for both wallets."""
        sender = CustomUser.objects.create_user(
            email="sender2@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="receiver2@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("500.00")
        )

        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile, balance=Decimal("0.00")
        )

        transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))

        assert sender_wallet.transactions.count() == 1
        assert receiver_wallet.transactions.count() == 1

    def test_transfer_self_transfer_raises_error(self):
        """Test transfer to same wallet raises error."""
        user = CustomUser.objects.create_user(
            email="self-transfer@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("1000.00")
        )

        with pytest.raises(SelfTransferError):
            transfer_funds(wallet, wallet, Decimal("100.00"))

    def test_transfer_insufficient_funds_raises_error(self):
        """Test transfer with insufficient funds raises error."""
        sender = CustomUser.objects.create_user(
            email="insufficient-sender@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="insufficient-receiver@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("100.00")
        )

        receiver_wallet = Wallet.objects.create(client_profile=receiver.client_profile)

        with pytest.raises(InsufficientFundsError):
            transfer_funds(sender_wallet, receiver_wallet, Decimal("500.00"))

        # Verify balances unchanged (atomic rollback)
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("100.00")
        assert receiver_wallet.balance == Decimal("0.00")

    def test_transfer_atomic_rollback_on_error(self):
        """Test transfer atomic rollback when error occurs mid-operation."""
        sender = CustomUser.objects.create_user(
            email="rollback-sender@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="rollback-receiver@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("100.00")
        )

        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile, balance=Decimal("0.00")
        )

        # Try to transfer more than available - should rollback completely
        with pytest.raises(InsufficientFundsError):
            transfer_funds(sender_wallet, receiver_wallet, Decimal("500.00"))

        # Both balances should be unchanged
        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("100.00")
        assert receiver_wallet.balance == Decimal("0.00")

    def test_transfer_frozen_sender_wallet_raises_error(self):
        """Test transfer from frozen wallet raises error."""
        sender = CustomUser.objects.create_user(
            email="frozen-sender@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="frozen-receiver@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile,
            balance=Decimal("1000.00"),
            is_frozen=True,
        )

        receiver_wallet = Wallet.objects.create(client_profile=receiver.client_profile)

        with pytest.raises(FrozenWalletError):
            transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))

    def test_transfer_frozen_receiver_wallet_raises_error(self):
        """Test transfer to frozen wallet raises error."""
        sender = CustomUser.objects.create_user(
            email="normal-sender@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="frozen-recv@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("1000.00")
        )

        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile, is_frozen=True
        )

        with pytest.raises(FrozenWalletError):
            transfer_funds(sender_wallet, receiver_wallet, Decimal("100.00"))


@pytest.mark.django_db
class TestWalletManagement:
    """Test wallet management functions."""

    def test_freeze_wallet(self):
        """Test freezing a wallet."""
        user = CustomUser.objects.create_user(
            email="freeze-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        frozen_wallet = freeze_wallet(wallet, "Suspicious activity")

        assert frozen_wallet.is_frozen is True
        assert frozen_wallet.can_operate() is False

    def test_unfreeze_wallet(self):
        """Test unfreezing a wallet."""
        user = CustomUser.objects.create_user(
            email="unfreeze-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile, is_frozen=True)

        unfrozen_wallet = unfreeze_wallet(wallet)

        assert unfrozen_wallet.is_frozen is False
        assert unfrozen_wallet.can_operate() is True

    def test_flag_transaction(self):
        """Test flagging a transaction."""
        user = CustomUser.objects.create_user(
            email="flag-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        transaction = deposit_funds(wallet, Decimal("10000.00"))

        flagged = flag_transaction(transaction, "Large amount")

        assert flagged.status == TransactionStatus.FLAGGED
        assert flagged.is_flagged() is True
        assert "flag_reason" in flagged.metadata
