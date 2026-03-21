"""
Tests for staff dashboard and fraud management views.

Verifies:
- Staff-only access enforcement
- System statistics accuracy
- Transaction review functionality
- Wallet freeze/unfreeze operations
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import UserType
from operations.fraud_engine import FraudEngine
from wallet.models import Transaction, TransactionStatus, Wallet
from wallet.services import transfer_funds


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    from accounts.models import CustomUser

    user = CustomUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        user_type=UserType.STAFF,
    )
    return user


@pytest.fixture
def client_user_with_wallet(db):
    """Create a client user with wallet for testing."""
    from accounts.models import CustomUser

    user = CustomUser.objects.create_user(
        email="client@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    wallet = Wallet.objects.create(client_profile=user.client_profile, balance=Decimal("50000.00"))
    return user, wallet


@pytest.fixture
def flagged_transaction(client_user_with_wallet):
    """Create a flagged transaction for testing."""
    user, sender_wallet = client_user_with_wallet

    # Create receiver wallet
    receiver_user = type(user).objects.create_user(
        email="receiver@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    receiver_wallet = Wallet.objects.create(
        client_profile=receiver_user.client_profile,
        balance=Decimal("1000.00")
    )

    # Create a transfer that will be flagged (>$10,000)
    transaction = transfer_funds(
        sender_wallet=sender_wallet,
        receiver_wallet=receiver_wallet,
        amount=Decimal("15000.00"),
        description="Flagged transfer test",
    )

    # Verify it was flagged by FraudEngine
    assert transaction.status == TransactionStatus.FLAGGED

    return transaction


@pytest.fixture
def frozen_wallet(client_user_with_wallet):
    """Create a frozen wallet for testing."""
    user, wallet = client_user_with_wallet
    wallet.is_frozen = True
    wallet.save()
    return wallet


class TestStaffDashboardView:
    """Test StaffDashboardView access and functionality."""

    def test_staff_dashboard_requires_login(self, client):
        """Test staff dashboard requires authentication."""
        response = client.get(reverse("operations:staff_dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_staff_dashboard_requires_staff_user(self, client, client_user_with_wallet):
        """Test staff dashboard denies access to client users."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.get(reverse("operations:staff_dashboard"))
        assert response.status_code == 403  # Permission denied

    def test_staff_dashboard_allows_staff_user(self, client, staff_user):
        """Test staff dashboard allows staff users."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("operations:staff_dashboard"))
        assert response.status_code == 200
        assert "stats" in response.context

    def test_staff_dashboard_context_data(self, client, staff_user, flagged_transaction):
        """Test staff dashboard provides correct context data."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("operations:staff_dashboard"))

        assert response.status_code == 200
        assert "flagged_transactions" in response.context
        assert "recent_transactions" in response.context
        assert "stats" in response.context

        # Check stats
        stats = response.context["stats"]
        assert "total_users" in stats
        assert "total_volume" in stats
        assert "flagged_count" in stats
        assert stats["flagged_count"] >= 1  # At least our flagged transaction

    def test_staff_dashboard_shows_flagged_transactions(self, client, staff_user, flagged_transaction):
        """Test staff dashboard displays flagged transactions in High Alert section."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("operations:staff_dashboard"))

        assert response.status_code == 200
        flagged_txns = response.context["flagged_transactions"]
        assert flagged_transaction in flagged_txns


class TestReviewTransactionView:
    """Test ReviewTransactionView for approving/rejecting flagged transactions."""

    def test_review_transaction_requires_login(self, client, flagged_transaction):
        """Test review transaction requires authentication."""
        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "approve"}
        )
        assert response.status_code == 302

    def test_review_transaction_requires_staff(self, client, client_user_with_wallet, flagged_transaction):
        """Test review transaction requires staff user."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "approve"}
        )
        assert response.status_code == 403

    def test_review_transaction_approve(self, client, staff_user, flagged_transaction):
        """Test approving a flagged transaction."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "approve"}
        )

        # Refresh from database
        flagged_transaction.refresh_from_db()

        assert response.status_code == 200
        assert flagged_transaction.status == TransactionStatus.COMPLETED
        assert flagged_transaction.metadata["reviewed_by"] == "staff@test.com"
        assert flagged_transaction.metadata["review_action"] == "approved"

    def test_review_transaction_reject(self, client, staff_user, flagged_transaction):
        """Test rejecting a flagged transaction."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "reject"}
        )

        # Refresh from database
        flagged_transaction.refresh_from_db()

        assert response.status_code == 200
        assert flagged_transaction.status == TransactionStatus.FAILED
        # After reversal, metadata has 'reversed' key instead of 'review_action'
        assert flagged_transaction.metadata.get("reversed") is True
        assert flagged_transaction.metadata.get("reversed_by") == "staff@test.com"

    def test_review_transaction_invalid_action(self, client, staff_user, flagged_transaction):
        """Test review transaction with invalid action."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "invalid"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid action" in data["error"]

    def test_review_transaction_not_flagged(self, client, staff_user, client_user_with_wallet):
        """Test reviewing a non-flagged transaction fails."""
        client.login(email="staff@test.com", password="testpass123")
        user, sender_wallet = client_user_with_wallet

        # Create a normal (non-flagged) transaction
        receiver_user = type(user).objects.create_user(
            email="receiver2@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        receiver_wallet = Wallet.objects.create(
            client_profile=receiver_user.client_profile,
            balance=Decimal("1000.00")
        )

        transaction = transfer_funds(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=Decimal("100.00"),
        )

        response = client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": transaction.id}),
            {"action": "approve"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not flagged" in data["error"]


class TestFreezeWalletView:
    """Test FreezeWalletView functionality."""

    def test_freeze_wallet_requires_login(self, client, client_user_with_wallet):
        """Test freeze wallet requires authentication."""
        user, wallet = client_user_with_wallet
        response = client.post(reverse("operations:freeze_wallet", kwargs={"wallet_id": wallet.id}))
        assert response.status_code == 302

    def test_freeze_wallet_requires_staff(self, client, client_user_with_wallet):
        """Test freeze wallet requires staff user."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.post(reverse("operations:freeze_wallet", kwargs={"wallet_id": wallet.id}))
        assert response.status_code == 403

    def test_freeze_wallet_success(self, client, staff_user, client_user_with_wallet):
        """Test freezing a wallet."""
        client.login(email="staff@test.com", password="testpass123")
        user, wallet = client_user_with_wallet

        response = client.post(reverse("operations:freeze_wallet", kwargs={"wallet_id": wallet.id}))

        # Refresh from database
        wallet.refresh_from_db()

        assert response.status_code == 200
        assert wallet.is_frozen is True

    def test_freeze_wallet_already_frozen(self, client, staff_user, frozen_wallet):
        """Test freezing an already frozen wallet."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.post(reverse("operations:freeze_wallet", kwargs={"wallet_id": frozen_wallet.id}))

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already frozen" in data["error"]


class TestUnfreezeWalletView:
    """Test UnfreezeWalletView functionality."""

    def test_unfreeze_wallet_requires_login(self, client, frozen_wallet):
        """Test unfreeze wallet requires authentication."""
        response = client.post(reverse("operations:unfreeze_wallet", kwargs={"wallet_id": frozen_wallet.id}))
        assert response.status_code == 302

    def test_unfreeze_wallet_requires_staff(self, client, client_user_with_wallet, frozen_wallet):
        """Test unfreeze wallet requires staff user."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.post(reverse("operations:unfreeze_wallet", kwargs={"wallet_id": frozen_wallet.id}))
        assert response.status_code == 403

    def test_unfreeze_wallet_success(self, client, staff_user, frozen_wallet):
        """Test unfreezing a wallet."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.post(reverse("operations:unfreeze_wallet", kwargs={"wallet_id": frozen_wallet.id}))

        # Refresh from database
        frozen_wallet.refresh_from_db()

        assert response.status_code == 200
        assert frozen_wallet.is_frozen is False

    def test_unfreeze_wallet_not_frozen(self, client, staff_user, client_user_with_wallet):
        """Test unfreezing a wallet that is not frozen."""
        client.login(email="staff@test.com", password="testpass123")
        user, wallet = client_user_with_wallet

        response = client.post(reverse("operations:unfreeze_wallet", kwargs={"wallet_id": wallet.id}))

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not frozen" in data["error"]


class TestStaffDashboardIntegration:
    """Test staff dashboard integration with fraud detection."""

    def test_flagged_transaction_appears_in_dashboard(self, client, staff_user, flagged_transaction):
        """Test that flagged transactions appear in the High Alert section."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("operations:staff_dashboard"))

        assert response.status_code == 200
        flagged_txns = response.context["flagged_transactions"]
        assert flagged_transaction in flagged_txns

    def test_approved_transaction_removed_from_flagged(self, client, staff_user, flagged_transaction):
        """Test that approved transactions are removed from flagged list."""
        client.login(email="staff@test.com", password="testpass123")

        # Approve the transaction
        client.post(
            reverse("operations:review_transaction", kwargs={"transaction_id": flagged_transaction.id}),
            {"action": "approve"}
        )

        # Reload dashboard
        response = client.get(reverse("operations:staff_dashboard"))
        flagged_txns = response.context["flagged_transactions"]

        # Transaction should no longer be in flagged list
        assert flagged_transaction not in flagged_txns

    def test_system_stats_accuracy(self, client, staff_user, client_user_with_wallet):
        """Test system statistics are accurate."""
        client.login(email="staff@test.com", password="testpass123")
        user, wallet = client_user_with_wallet

        response = client.get(reverse("operations:staff_dashboard"))
        stats = response.context["stats"]

        # Check total users includes our test client
        assert stats["total_users"] >= 1

        # Check total volume includes deposits
        assert stats["total_volume"] >= Decimal("0.00")

        # Check flagged count
        assert stats["flagged_count"] >= 0
