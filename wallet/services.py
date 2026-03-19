"""
Wallet service layer.

Implements atomic financial operations with full validation.
"""

import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .exceptions import (
    DuplicateTransactionError,
    FrozenWalletError,
    InsufficientFundsError,
    InvalidAmountError,
    SelfTransferError,
)
from .models import Transaction, TransactionStatus, TransactionType

# -- Helper Functions


def _validate_amount(amount):
    """Validate amount is positive."""
    if amount <= Decimal("0.00"):
        raise InvalidAmountError(amount)


def _validate_wallet_not_frozen(wallet):
    """Validate wallet is not frozen."""
    if wallet.is_frozen:
        raise FrozenWalletError(wallet.id)


def _check_reference_id_exists(reference_id):
    """Check if reference_id already exists."""
    return Transaction.objects.filter(reference_id=reference_id).exists()


def _create_transaction_record(
    wallet,
    counterparty_wallet,
    amount,
    transaction_type,
    status,
    description,
    reference_id,
    metadata=None,
):
    """Create a transaction record."""
    return Transaction.objects.create(
        wallet=wallet,
        counterparty_wallet=counterparty_wallet,
        amount=amount,
        type=transaction_type,
        status=status,
        description=description,
        reference_id=reference_id,
        metadata=metadata or {},
    )


# -- Service Functions


@transaction.atomic
def deposit_funds(wallet, amount, description="", reference_id=None):
    """
    Deposit funds into a wallet.

    Args:
        wallet: Wallet instance to deposit into
        amount: Decimal amount to deposit
        description: Optional description for the transaction
        reference_id: Unique reference for idempotency (auto-generated if not provided)

    Returns:
        Transaction: The created transaction record

    Raises:
        FrozenWalletError: If wallet is frozen
        InvalidAmountError: If amount is not positive
        DuplicateTransactionError: If reference_id already exists
    """
    # -- Validate
    _validate_amount(amount)
    _validate_wallet_not_frozen(wallet)

    # -- Generate reference_id if not provided
    if reference_id is None:
        reference_id = f"DEP-{wallet.id}-{uuid.uuid4().hex[:12]}"

    # -- Check idempotency
    if _check_reference_id_exists(reference_id):
        raise DuplicateTransactionError(reference_id)

    # -- Update balance
    wallet.balance = wallet.balance + amount
    wallet.save()

    # -- Create transaction record
    transaction_record = _create_transaction_record(
        wallet=wallet,
        counterparty_wallet=None,
        amount=amount,
        transaction_type=TransactionType.DEPOSIT,
        status=TransactionStatus.COMPLETED,
        description=description,
        reference_id=reference_id,
        metadata={"operation": "deposit", "timestamp": timezone.now().isoformat()},
    )

    return transaction_record


@transaction.atomic
def withdraw_funds(wallet, amount, description="", reference_id=None):
    """
    Withdraw funds from a wallet.

    Args:
        wallet: Wallet instance to withdraw from
        amount: Decimal amount to withdraw
        description: Optional description for the transaction
        reference_id: Unique reference for idempotency (auto-generated if not provided)

    Returns:
        Transaction: The created transaction record

    Raises:
        FrozenWalletError: If wallet is frozen
        InsufficientFundsError: If balance is insufficient
        InvalidAmountError: If amount is not positive
        DuplicateTransactionError: If reference_id already exists
    """
    # -- Validate
    _validate_amount(amount)
    _validate_wallet_not_frozen(wallet)

    # -- Check sufficient funds
    if wallet.balance < amount:
        raise InsufficientFundsError(wallet.balance, amount)

    # -- Generate reference_id if not provided
    if reference_id is None:
        reference_id = f"WDR-{wallet.id}-{uuid.uuid4().hex[:12]}"

    # -- Check idempotency
    if _check_reference_id_exists(reference_id):
        raise DuplicateTransactionError(reference_id)

    # -- Update balance
    wallet.balance = wallet.balance - amount
    wallet.save()

    # -- Create transaction record
    transaction_record = _create_transaction_record(
        wallet=wallet,
        counterparty_wallet=None,
        amount=amount,
        transaction_type=TransactionType.WITHDRAWAL,
        status=TransactionStatus.COMPLETED,
        description=description,
        reference_id=reference_id,
        metadata={"operation": "withdrawal", "timestamp": timezone.now().isoformat()},
    )

    return transaction_record


@transaction.atomic
def transfer_funds(sender_wallet, receiver_wallet, amount, description="", reference_id=None):
    """
    Transfer funds between wallets.

    Args:
        sender_wallet: Wallet to send from
        receiver_wallet: Wallet to receive
        amount: Decimal amount to transfer
        description: Optional description for the transaction
        reference_id: Unique reference for idempotency (auto-generated if not provided)

    Returns:
        Transaction: The created transaction record (for sender)

    Raises:
        FrozenWalletError: If either wallet is frozen
        SelfTransferError: If sender and receiver are the same
        InsufficientFundsError: If sender balance is insufficient
        InvalidAmountError: If amount is not positive
        DuplicateTransactionError: If reference_id already exists
    """
    # -- Validate amount
    _validate_amount(amount)

    # -- Validate wallets not frozen
    _validate_wallet_not_frozen(sender_wallet)
    _validate_wallet_not_frozen(receiver_wallet)

    # -- Prevent self-transfer
    if sender_wallet.id == receiver_wallet.id:
        raise SelfTransferError()

    # -- Check sufficient funds
    if sender_wallet.balance < amount:
        raise InsufficientFundsError(sender_wallet.balance, amount)

    # -- Generate reference_id if not provided
    if reference_id is None:
        reference_id = f"TRF-{sender_wallet.id}-{receiver_wallet.id}-{uuid.uuid4().hex[:12]}"

    # -- Check idempotency
    if _check_reference_id_exists(reference_id):
        raise DuplicateTransactionError(reference_id)

    # -- Update balances atomically
    sender_wallet.balance = sender_wallet.balance - amount
    sender_wallet.save()

    receiver_wallet.balance = receiver_wallet.balance + amount
    receiver_wallet.save()

    # -- Determine initial status (COMPLETED or FLAGGED based on fraud check)
    from operations.fraud_engine import FraudEngine

    # Create sender transaction first (needed for fraud check)
    sender_transaction = _create_transaction_record(
        wallet=sender_wallet,
        counterparty_wallet=receiver_wallet,
        amount=amount,
        transaction_type=TransactionType.TRANSFER,
        status=TransactionStatus.COMPLETED,  # Temporary status
        description=description,
        reference_id=reference_id,
        metadata={
            "operation": "transfer_send",
            "counterparty": receiver_wallet.id,
            "timestamp": timezone.now().isoformat(),
        },
    )

    # -- Run fraud detection on the transaction
    fraud_result = FraudEngine.check_transaction(sender_transaction)

    # Update status if flagged
    if fraud_result["is_flagged"]:
        sender_transaction.status = TransactionStatus.FLAGGED
        sender_transaction.metadata = {
            **sender_transaction.metadata,
            "flagged": True,
            "flag_reason": "; ".join(fraud_result["reasons"]),
            "flag_rules_triggered": fraud_result["rules_triggered"],
            "flagged_at": timezone.now().isoformat(),
        }
        sender_transaction.save(update_fields=["status", "metadata"])

    # -- Create corresponding receiver transaction with same reference
    receiver_transaction = _create_transaction_record(
        wallet=receiver_wallet,
        counterparty_wallet=sender_wallet,
        amount=amount,
        transaction_type=TransactionType.TRANSFER,
        status=sender_transaction.status,  # Match sender's status
        description=f"Received from {sender_wallet.client_profile.user.email}",
        reference_id=f"{reference_id}-RECV",
        metadata={
            "operation": "transfer_receive",
            "counterparty": sender_wallet.id,
            "original_reference": reference_id,
            "timestamp": timezone.now().isoformat(),
        },
    )

    return sender_transaction


@transaction.atomic
def flag_transaction(transaction, reason=""):
    """
    Flag a transaction for review.

    Args:
        transaction: Transaction instance to flag
        reason: Reason for flagging

    Returns:
        Transaction: The flagged transaction
    """
    transaction.status = TransactionStatus.FLAGGED
    transaction.metadata = {
        **transaction.metadata,
        "flagged": True,
        "flag_reason": reason,
        "flagged_at": timezone.now().isoformat(),
    }
    transaction.save(update_fields=["status", "metadata"])

    return transaction


@transaction.atomic
def freeze_wallet(wallet, reason=""):
    """
    Freeze a wallet to prevent operations.

    Args:
        wallet: Wallet instance to freeze
        reason: Reason for freezing

    Returns:
        Wallet: The frozen wallet
    """
    wallet.is_frozen = True
    wallet.metadata = {
        **getattr(wallet, "metadata", {}),
        "frozen": True,
        "frozen_reason": reason,
        "frozen_at": timezone.now().isoformat(),
    }
    wallet.save(update_fields=["is_frozen"])

    return wallet


@transaction.atomic
def unfreeze_wallet(wallet):
    """
    Unfreeze a wallet to allow operations.

    Args:
        wallet: Wallet instance to unfreeze

    Returns:
        Wallet: The unfrozen wallet
    """
    wallet.is_frozen = False
    if hasattr(wallet, "metadata") and wallet.metadata:
        wallet.metadata["unfrozen_at"] = timezone.now().isoformat()
        wallet.save(update_fields=["is_frozen"])
    else:
        wallet.save(update_fields=["is_frozen"])

    return wallet
