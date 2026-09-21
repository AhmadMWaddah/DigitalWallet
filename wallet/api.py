"""
Wallet REST API (v1).

Thin wrappers over wallet/services.py, which stays the single source of
truth for money movement. HTML views in views.py are untouched.
"""

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ClientProfile, UserType

from .exceptions import (
    DuplicateTransactionError,
    FrozenWalletError,
    InsufficientFundsError,
    InvalidAmountError,
    SelfTransferError,
)
from .models import Transaction, Wallet
from .serializers import (
    DepositInputSerializer,
    TransactionSerializer,
    TransferInputSerializer,
    WalletSerializer,
    WithdrawInputSerializer,
)
from .services import deposit_funds, transfer_funds, withdraw_funds

SERVICE_ERRORS = (
    FrozenWalletError,
    InvalidAmountError,
    InsufficientFundsError,
    SelfTransferError,
    DuplicateTransactionError,
)


class IsClientUser(permissions.BasePermission):
    """Mirror ClientOnlyMixin for DRF: clients see only their own data."""

    message = "Client access required."

    def has_permission(self, request, view):
        """Allow authenticated client users only."""
        user = request.user
        return bool(user.is_authenticated and user.user_type == UserType.CLIENT)


def _own_wallet(request):
    """Return the requesting client's wallet or 404."""
    return get_object_or_404(Wallet, client_profile__user=request.user)


def _reference(prefix, *parts):
    """Build a unique reference_id mirroring the HTML views."""
    return f"{prefix}-{'-'.join(str(p) for p in parts)}-{uuid.uuid4().hex[:12]}"


class WalletDetailView(APIView):
    """GET /api/v1/wallet/ — own wallet balance and state."""

    permission_classes = [IsClientUser]

    def get(self, request):
        """Return the requesting client's wallet."""
        return Response(WalletSerializer(_own_wallet(request)).data)


class TransactionListView(generics.ListAPIView):
    """GET /api/v1/transactions/ — own transactions, paginated."""

    permission_classes = [IsClientUser]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """Filter own wallet transactions by optional type/status."""
        queryset = Transaction.objects.filter(wallet=_own_wallet(self.request)).order_by(
            "-created_at"
        )
        transaction_type = self.request.query_params.get("type")
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        tx_status = self.request.query_params.get("status")
        if tx_status:
            queryset = queryset.filter(status=tx_status)
        return queryset


class _MoneyWriteView(APIView):
    """Shared write flow: validate input, run service, map errors to 400."""

    permission_classes = [IsClientUser]
    throttle_scope = "transfer"
    input_serializer: type[serializers.Serializer] | None = None

    def _run(self, wallet, data):
        """Execute the service call (implemented per view)."""
        raise NotImplementedError

    def post(self, request):
        """Validate payload and execute the money movement."""
        if self.input_serializer is None:
            raise APIException("View misconfigured: input_serializer unset.")
        serializer = self.input_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transaction = self._run(_own_wallet(request), serializer.validated_data)
        except SERVICE_ERRORS as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)


class DepositAPIView(_MoneyWriteView):
    """POST /api/v1/deposit/ — fund own wallet."""

    input_serializer = DepositInputSerializer

    def _run(self, wallet, data):
        """Run deposit_funds with generated or client reference_id."""
        return deposit_funds(
            wallet=wallet,
            amount=data["amount"],
            description=data.get("description", ""),
            reference_id=data.get("reference_id") or _reference("DEP", wallet.id),
        )


class WithdrawAPIView(_MoneyWriteView):
    """POST /api/v1/withdraw/ — withdraw from own wallet."""

    input_serializer = WithdrawInputSerializer

    def _run(self, wallet, data):
        """Run withdraw_funds with generated or client reference_id."""
        return withdraw_funds(
            wallet=wallet,
            amount=data["amount"],
            description=data.get("description", ""),
            reference_id=data.get("reference_id") or _reference("WDR", wallet.id),
        )


class TransferAPIView(_MoneyWriteView):
    """POST /api/v1/transfer/ — move funds to another client's wallet."""

    input_serializer = TransferInputSerializer

    def _run(self, wallet, data):
        """Resolve recipient by email, then run transfer_funds."""
        try:
            receiver_wallet = (
                ClientProfile.objects.select_related("wallet")
                .get(user__email=data["recipient_email"])
                .wallet
            )
        except ClientProfile.DoesNotExist as exc:
            raise serializers.ValidationError("Recipient not found.") from exc
        return transfer_funds(
            sender_wallet=wallet,
            receiver_wallet=receiver_wallet,
            amount=data["amount"],
            description=data.get("description", ""),
            reference_id=data.get("reference_id")
            or _reference("TRF", wallet.id, receiver_wallet.id),
        )
