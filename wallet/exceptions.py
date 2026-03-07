"""
Wallet app custom exceptions.

Defines specific exceptions for wallet operations.
"""


class WalletException(Exception):
    """Base exception for wallet operations."""

    pass


class InsufficientFundsError(WalletException):
    """Raised when a wallet has insufficient funds for an operation."""

    def __init__(self, balance, required):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient funds. Balance: ${balance:.2f}, Required: ${required:.2f}")


class SelfTransferError(WalletException):
    """Raised when attempting to transfer funds to the same wallet."""

    def __init__(self):
        super().__init__("Cannot transfer funds to the same wallet.")


class DuplicateTransactionError(WalletException):
    """Raised when a transaction with the same reference_id already exists."""

    def __init__(self, reference_id):
        self.reference_id = reference_id
        super().__init__(f"Duplicate transaction detected. Reference ID: {reference_id}")


class FrozenWalletError(WalletException):
    """Raised when attempting an operation on a frozen wallet."""

    def __init__(self, wallet_id):
        self.wallet_id = wallet_id
        super().__init__(f"Wallet {wallet_id} is frozen. Operation not allowed.")


class InvalidAmountError(WalletException):
    """Raised when an invalid amount is provided."""

    def __init__(self, amount):
        self.amount = amount
        super().__init__(f"Invalid amount: ${amount}. Amount must be positive.")


class CounterpartyWalletNotFoundError(WalletException):
    """Raised when the counterparty wallet is not found for a transfer."""

    def __init__(self, wallet_identifier):
        self.wallet_identifier = wallet_identifier
        super().__init__(f"Counterparty wallet not found: {wallet_identifier}")
