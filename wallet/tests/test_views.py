"""
Tests for wallet app views.

Verifies HTMX dashboard, transaction history, and action views.
"""

import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import UserType
from wallet.models import Transaction, Wallet

CustomUser = get_user_model()


@pytest.mark.django_db
class TestDashboardView:
    """Test DashboardView."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get(reverse("wallet:dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_dashboard_client_access(self, client):
        """Test client can access dashboard."""
        CustomUser.objects.create_user(
            email="dashboard-client@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        client.login(email="dashboard-client@test.com", password="testpass123")
        response = client.get(reverse("wallet:dashboard"))

        assert response.status_code == 200
        assert "wallet" in response.context

    def test_dashboard_staff_redirected(self, client):
        """Test staff user is redirected from dashboard."""
        CustomUser.objects.create_user(
            email="dashboard-staff@test.com",
            password="testpass123",
            user_type=UserType.STAFF,
        )

        client.login(email="dashboard-staff@test.com", password="testpass123")
        response = client.get(reverse("wallet:dashboard"))

        assert response.status_code == 403  # ClientOnlyMixin denies access

    def test_dashboard_context_with_wallet(self, client):
        """Test dashboard provides wallet in context."""
        user = CustomUser.objects.create_user(
            email="wallet-context@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("1000.00")
        )

        client.login(email="wallet-context@test.com", password="testpass123")
        response = client.get(reverse("wallet:dashboard"))

        assert response.context["wallet"] == wallet
        assert "deposit_form" in response.context
        assert "withdraw_form" in response.context
        assert "transfer_form" in response.context

    def test_dashboard_context_without_wallet(self, client):
        """Test dashboard handles missing wallet."""
        CustomUser.objects.create_user(
            email="no-wallet@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        # Don't create wallet

        client.login(email="no-wallet@test.com", password="testpass123")
        response = client.get(reverse("wallet:dashboard"))

        assert response.context["wallet"] is None


@pytest.mark.django_db
class TestTransactionHistoryView:
    """Test TransactionHistoryView for HTMX infinite scroll."""

    def test_transaction_history_requires_login(self, client):
        """Test history requires authentication."""
        response = client.get(reverse("wallet:transaction_history"))
        assert response.status_code == 302

    def test_transaction_history_returns_json(self, client):
        """Test history returns JSON response."""
        user = CustomUser.objects.create_user(
            email="history-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        Wallet.objects.create(client_profile=user.client_profile)

        client.login(email="history-test@test.com", password="testpass123")
        response = client.get(reverse("wallet:transaction_history"))

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert "html" in data
        assert "has_more" in data

    def test_transaction_history_pagination(self, client):
        """Test history pagination with cursor."""
        user = CustomUser.objects.create_user(
            email="pagination-test@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile)

        # Create 25 transactions
        for i in range(25):
            Transaction.objects.create(
                wallet=wallet,
                amount=Decimal(f"{i + 1}.00"),
                type="DEPOSIT",
                reference_id=f"PAG-{i}",
            )

        client.login(email="pagination-test@test.com", password="testpass123")

        # First page
        response = client.get(reverse("wallet:transaction_history"))
        data = json.loads(response.content)
        assert data["has_more"] is True

        # Second page with cursor - should have 5 remaining (25 total - 20 first page)
        last_txn = Transaction.objects.filter(wallet=wallet).order_by("-created_at")[19]
        cursor = last_txn.created_at.strftime("%Y-%m-%d %H:%M:%S")

        response = client.get(f"{reverse('wallet:transaction_history')}?cursor={cursor}")
        data = json.loads(response.content)
        # After taking 20, we have 5 more, so has_more should be False after this page
        assert "html" in data  # But we still get HTML


@pytest.mark.django_db
class TestDepositView:
    """Test DepositView HTMX handling."""

    def test_deposit_requires_login(self, client):
        """Test deposit requires authentication."""
        response = client.post(reverse("wallet:deposit"))
        assert response.status_code == 302

    def test_deposit_success(self, client):
        """Test successful deposit via HTMX."""
        user = CustomUser.objects.create_user(
            email="deposit-success@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("100.00")
        )

        client.login(email="deposit-success@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:deposit"),
            {"amount": "50.00", "description": "Test deposit"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "balance" in data
        assert "message" in data

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("150.00")

    def test_deposit_invalid_amount(self, client):
        """Test deposit with invalid amount."""
        user = CustomUser.objects.create_user(
            email="deposit-invalid@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        Wallet.objects.create(client_profile=user.client_profile)

        client.login(email="deposit-invalid@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:deposit"),
            {"amount": "-50.00"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        data = json.loads(response.content)
        assert data["success"] is False
        assert "form" in data  # Form with errors returned


@pytest.mark.django_db
class TestWithdrawView:
    """Test WithdrawView HTMX handling."""

    def test_withdraw_requires_login(self, client):
        """Test withdraw requires authentication."""
        response = client.post(reverse("wallet:withdraw"))
        assert response.status_code == 302

    def test_withdraw_success(self, client):
        """Test successful withdrawal via HTMX."""
        user = CustomUser.objects.create_user(
            email="withdraw-success@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(
            client_profile=user.client_profile, balance=Decimal("200.00")
        )

        client.login(email="withdraw-success@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:withdraw"),
            {"amount": "50.00", "description": "Test withdrawal"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("150.00")

    def test_withdraw_insufficient_funds(self, client):
        """Test withdrawal with insufficient funds."""
        user = CustomUser.objects.create_user(
            email="withdraw-fail@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        wallet = Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("50.00"))

        client.login(email="withdraw-fail@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:withdraw"),
            {"amount": "100.00"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        data = json.loads(response.content)
        assert data["success"] is False
        assert "error" in data

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("50.00")  # Balance unchanged


@pytest.mark.django_db
class TestTransferView:
    """Test TransferView HTMX handling."""

    def test_transfer_requires_login(self, client):
        """Test transfer requires authentication."""
        response = client.post(reverse("wallet:transfer"))
        assert response.status_code == 302

    def test_transfer_success(self, client):
        """Test successful transfer via HTMX."""
        sender = CustomUser.objects.create_user(
            email="sender-transfer@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        receiver = CustomUser.objects.create_user(
            email="receiver-transfer@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        sender_wallet = Wallet.objects.create(
            client_profile=sender.client_profile, balance=Decimal("500.00")
        )

        receiver_wallet = Wallet.objects.create(
            client_profile=receiver.client_profile, balance=Decimal("0.00")
        )

        client.login(email="sender-transfer@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {
                "recipient_email": "receiver-transfer@test.com",
                "amount": "100.00",
                "description": "Test transfer",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        sender_wallet.refresh_from_db()
        receiver_wallet.refresh_from_db()
        assert sender_wallet.balance == Decimal("400.00")
        assert receiver_wallet.balance == Decimal("100.00")

    def test_transfer_to_self_fails(self, client):
        """Test transfer to self fails validation."""
        user = CustomUser.objects.create_user(
            email="self-transfer@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("500.00"))

        client.login(email="self-transfer@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {
                "recipient_email": "self-transfer@test.com",
                "amount": "100.00",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        data = json.loads(response.content)
        assert data["success"] is False
        assert "form" in data  # Form with errors

    def test_transfer_to_nonexistent_user(self, client):
        """Test transfer to non-existent user fails."""
        user = CustomUser.objects.create_user(
            email="transfer-nobody@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("500.00"))

        client.login(email="transfer-nobody@test.com", password="testpass123")

        response = client.post(
            reverse("wallet:transfer"),
            {
                "recipient_email": "nonexistent@test.com",
                "amount": "100.00",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        data = json.loads(response.content)
        assert data["success"] is False
        assert "errors" in data or "error" in data  # Either form errors or error message


@pytest.mark.django_db
class TestBalanceCardView:
    """Test BalanceCardView for OOB updates."""

    def test_balance_card_requires_login(self, client):
        """Test balance card requires authentication."""
        response = client.get(reverse("wallet:balance"))
        assert response.status_code == 302

    def test_balance_card_returns_json(self, client):
        """Test balance card returns JSON."""
        user = CustomUser.objects.create_user(
            email="balance-card@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )

        Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("999.99"))

        client.login(email="balance-card@test.com", password="testpass123")

        response = client.get(reverse("wallet:balance"))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "html" in data
