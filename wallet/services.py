"""
Wallet service layer.

Implements atomic financial operations with full validation.
Concurrency-safe with database locking and F() expressions.
"""

import uuid
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .exceptions import (
    DuplicateTransactionError,
    FrozenWalletError,
    InsufficientFundsError,
    InvalidAmountError,
    SelfTransferError,
)
from .models import Transaction, TransactionStatus, TransactionType, Wallet

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

    Concurrency-safe: Uses select_for_update() to lock wallet row.
    Uses F() expressions to avoid stale data overwrites.
    Implements robust idempotency via database UNIQUE constraint.

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

    # -- Lock wallet row for update (prevents concurrent modifications)
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    # -- Update balance using F() expression (avoids race conditions)
    Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + amount)

    # -- Refresh wallet from database to get updated balance
    wallet.refresh_from_db()

    # -- Create transaction record with idempotency protection
    try:
        transaction_record = Transaction.objects.create(
            wallet=wallet,
            counterparty_wallet=None,
            amount=amount,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            description=description,
            reference_id=reference_id,
            metadata={"operation": "deposit", "timestamp": timezone.now().isoformat()},
        )
    except IntegrityError as e:
        # Reference ID already exists - this is a duplicate request
        raise DuplicateTransactionError(reference_id) from e

    return transaction_record


@transaction.atomic
def withdraw_funds(wallet, amount, description="", reference_id=None):
    """
    Withdraw funds from a wallet.

    Concurrency-safe: Uses select_for_update() to lock wallet row.
    Uses F() expressions to avoid stale data overwrites.
    Implements robust idempotency via database UNIQUE constraint.

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

    # -- Generate reference_id if not provided
    if reference_id is None:
        reference_id = f"WDR-{wallet.id}-{uuid.uuid4().hex[:12]}"

    # -- Lock wallet row for update (prevents concurrent modifications)
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    # -- Check sufficient funds (after lock, balance is current)
    if wallet.balance < amount:
        raise InsufficientFundsError(wallet.balance, amount)

    # -- Update balance using F() expression (avoids race conditions)
    Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") - amount)

    # -- Refresh wallet from database to get updated balance
    wallet.refresh_from_db()

    # -- Create transaction record with idempotency protection
    try:
        transaction_record = Transaction.objects.create(
            wallet=wallet,
            counterparty_wallet=None,
            amount=amount,
            type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.COMPLETED,
            description=description,
            reference_id=reference_id,
            metadata={"operation": "withdrawal", "timestamp": timezone.now().isoformat()},
        )
    except IntegrityError as e:
        # Reference ID already exists - this is a duplicate request
        raise DuplicateTransactionError(reference_id) from e

    return transaction_record


@transaction.atomic
def transfer_funds(sender_wallet, receiver_wallet, amount, description="", reference_id=None):
    """
    Transfer funds between wallets.

    Concurrency-safe: Uses select_for_update() to lock BOTH wallet rows.
    Uses F() expressions to avoid stale data overwrites.
    Implements robust idempotency via database UNIQUE constraint.

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

    # -- Generate reference_id if not provided
    if reference_id is None:
        reference_id = f"TRF-{sender_wallet.id}-{receiver_wallet.id}-{uuid.uuid4().hex[:12]}"

    # -- CRITICAL: Lock BOTH wallet rows for update (order by ID to prevent deadlocks)
    # Lock in consistent order (lower ID first) to prevent deadlocks
    if sender_wallet.id < receiver_wallet.id:
        sender_wallet = Wallet.objects.select_for_update().get(pk=sender_wallet.pk)
        receiver_wallet = Wallet.objects.select_for_update().get(pk=receiver_wallet.pk)
    else:
        receiver_wallet = Wallet.objects.select_for_update().get(pk=receiver_wallet.pk)
        sender_wallet = Wallet.objects.select_for_update().get(pk=sender_wallet.pk)

    # -- Check sufficient funds (after lock, balance is current)
    if sender_wallet.balance < amount:
        raise InsufficientFundsError(sender_wallet.balance, amount)

    # -- Update balances using F() expressions (avoids race conditions)
    Wallet.objects.filter(pk=sender_wallet.pk).update(balance=F("balance") - amount)
    Wallet.objects.filter(pk=receiver_wallet.pk).update(balance=F("balance") + amount)

    # -- Refresh wallets from database to get updated balances
    sender_wallet.refresh_from_db()
    receiver_wallet.refresh_from_db()

    # -- Determine initial status (COMPLETED or FLAGGED based on fraud check)
    from operations.fraud_engine import FraudEngine

    # -- Create sender transaction with idempotency protection
    try:
        sender_transaction = Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=amount,
            type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,  # Temporary status
            description=description,
            reference_id=reference_id,
            metadata={
                "operation": "transfer_send",
                "counterparty": receiver_wallet.id,
                "timestamp": timezone.now().isoformat(),
            },
        )
    except IntegrityError as e:
        # Reference ID already exists - this is a duplicate request
        raise DuplicateTransactionError(reference_id) from e

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
    try:
        receiver_transaction = Transaction.objects.create(
            wallet=receiver_wallet,
            counterparty_wallet=sender_wallet,
            amount=amount,
            type=TransactionType.TRANSFER,
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
    except IntegrityError as e:
        # This shouldn't happen for receiver transaction, but handle it
        raise DuplicateTransactionError(f"{reference_id}-RECV") from e

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


@transaction.atomic
def reverse_transfer(transaction_id, staff_user):
    """
    Reverse a flagged transfer and restore funds to sender.

    This function is called when a staff member rejects a flagged transfer.
    It creates a reversal transaction and updates both wallets.

    Args:
        transaction_id: ID of the flagged transfer to reverse
        staff_user: Staff user performing the reversal

    Returns:
        dict: Result containing success status and reversal transaction

    Raises:
        ValueError: If transaction is not flagged or not a transfer
    """
    from .models import Transaction

    # Get the original transaction with lock
    original_txn = Transaction.objects.select_for_update().get(pk=transaction_id)

    # Verify it's a flagged transfer
    if original_txn.type != TransactionType.TRANSFER:
        raise ValueError(f"Transaction {transaction_id} is not a transfer")

    if original_txn.status != TransactionStatus.FLAGGED:
        raise ValueError(f"Transaction {transaction_id} is not flagged")

    # Get wallets with lock
    sender_wallet = Wallet.objects.select_for_update().get(
        pk=original_txn.wallet.pk
    )
    receiver_wallet = Wallet.objects.select_for_update().get(
        pk=original_txn.counterparty_wallet.pk
    )

    # Restore funds to sender
    Wallet.objects.filter(pk=sender_wallet.pk).update(
        balance=F("balance") + original_txn.amount
    )
    Wallet.objects.filter(pk=receiver_wallet.pk).update(
        balance=F("balance") - original_txn.amount
    )

    # Refresh wallets
    sender_wallet.refresh_from_db()
    receiver_wallet.refresh_from_db()

    # Create reversal transaction record
    reversal_txn = Transaction.objects.create(
        wallet=receiver_wallet,
        counterparty_wallet=sender_wallet,
        amount=original_txn.amount,
        type=TransactionType.TRANSFER,
        status=TransactionStatus.FAILED,
        description=f"Reversal by staff: {original_txn.description}",
        reference_id=f"{original_txn.reference_id}-REVERSAL",
        metadata={
            "operation": "reversal",
            "original_transaction_id": transaction_id,
            "reversed_by": staff_user.email,
            "reversed_at": timezone.now().isoformat(),
            "reason": "Staff review - transfer rejected",
        },
    )

    # Update original transaction status to FAILED
    original_txn.status = TransactionStatus.FAILED
    original_txn.metadata = {
        **original_txn.metadata,
        "reversed": True,
        "reversed_by": staff_user.email,
        "reversed_at": timezone.now().isoformat(),
        "reversal_transaction_id": reversal_txn.id,
    }
    original_txn.save(update_fields=["status", "metadata"])

    # Update receiver's counterparty transaction
    receiver_txn = Transaction.objects.filter(
        reference_id=f"{original_txn.reference_id}-RECV"
    ).first()
    if receiver_txn:
        receiver_txn.status = TransactionStatus.FAILED
        receiver_txn.metadata = {
            **receiver_txn.metadata,
            "reversed": True,
            "reversed_by": staff_user.email,
            "reversed_at": timezone.now().isoformat(),
        }
        receiver_txn.save(update_fields=["status", "metadata"])

    return {
        "success": True,
        "message": f"Transfer reversed. ${original_txn.amount} restored to sender.",
        "reversal_transaction": reversal_txn,
        "original_transaction": original_txn,
    }


@transaction.atomic
def process_fraud_review(transaction_id, action, staff_user):
    """
    Process staff fraud review decision.

    This function handles both approve and reject actions for flagged transactions.

    Args:
        transaction_id: ID of the flagged transaction
        action: 'approve' or 'reject'
        staff_user: Staff user making the decision

    Returns:
        dict: Result containing success status and details

    Raises:
        ValueError: If transaction is not flagged or invalid action
    """
    from .models import Transaction

    # Get transaction with lock
    transaction = Transaction.objects.select_for_update().get(pk=transaction_id)

    # Verify it's flagged
    if transaction.status != TransactionStatus.FLAGGED:
        raise ValueError(f"Transaction {transaction_id} is not flagged")

    if action == "approve":
        # Mark as completed
        transaction.status = TransactionStatus.COMPLETED
        transaction.metadata = {
            **transaction.metadata,
            "reviewed_by": staff_user.email,
            "reviewed_at": timezone.now().isoformat(),
            "review_action": "approved",
        }
        transaction.save(update_fields=["status", "metadata"])

        # Update receiver's transaction if exists
        receiver_txn = Transaction.objects.filter(
            reference_id=f"{transaction.reference_id}-RECV"
        ).first()
        if receiver_txn:
            receiver_txn.status = TransactionStatus.COMPLETED
            receiver_txn.metadata = {
                **receiver_txn.metadata,
                "reviewed_by": staff_user.email,
                "reviewed_at": timezone.now().isoformat(),
                "review_action": "approved",
            }
            receiver_txn.save(update_fields=["status", "metadata"])

        return {
            "success": True,
            "message": f"Transaction {transaction_id} approved and marked as COMPLETED.",
            "transaction": transaction,
        }

    elif action == "reject":
        # For transfers, reverse the transaction
        if transaction.type == TransactionType.TRANSFER:
            return reverse_transfer(transaction_id, staff_user)

        # For non-transfers (deposit/withdrawal), just mark as failed
        transaction.status = TransactionStatus.FAILED
        transaction.metadata = {
            **transaction.metadata,
            "reviewed_by": staff_user.email,
            "reviewed_at": timezone.now().isoformat(),
            "review_action": "rejected",
        }
        transaction.save(update_fields=["status", "metadata"])

        return {
            "success": True,
            "message": f"Transaction {transaction_id} rejected and marked as FAILED.",
            "transaction": transaction,
        }

    else:
        raise ValueError(f"Invalid action: {action}. Use 'approve' or 'reject'.")
