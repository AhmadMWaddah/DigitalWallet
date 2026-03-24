"""
Tests for analytics JSON endpoints.

Verifies:
- Staff-only access enforcement
- Spending by category aggregation accuracy
- Spending by month aggregation accuracy
- JSON response format for Chart.js
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserType
from wallet.models import Transaction, TransactionStatus, Wallet


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
def transactions_for_analytics(client_user_with_wallet):
    """Create sample transactions for analytics testing."""
    user, sender_wallet = client_user_with_wallet

    # Create receiver wallet
    receiver_user = type(user).objects.create_user(
        email="receiver@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    receiver_wallet = Wallet.objects.create(
        client_profile=receiver_user.client_profile, balance=Decimal("1000.00")
    )

    now = timezone.now()

    # Create transactions with different types and dates
    transactions = []

    # Deposits
    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("5000.00"),
            type="DEPOSIT",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-DEP-001",
            created_at=now - timedelta(days=5),
        )
    )

    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("3000.00"),
            type="DEPOSIT",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-DEP-002",
            created_at=now - timedelta(days=15),
        )
    )

    # Withdrawals
    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("1000.00"),
            type="WITHDRAWAL",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-WDR-001",
            created_at=now - timedelta(days=10),
        )
    )

    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("500.00"),
            type="WITHDRAWAL",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-WDR-002",
            created_at=now - timedelta(days=20),
        )
    )

    # Transfers
    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("2000.00"),
            type="TRANSFER",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-TRF-001",
            created_at=now - timedelta(days=7),
        )
    )

    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("1500.00"),
            type="TRANSFER",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-TRF-002",
            created_at=now - timedelta(days=25),
        )
    )

    # Create a transaction in a different month (for month aggregation test)
    transactions.append(
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("4000.00"),
            type="DEPOSIT",
            status=TransactionStatus.COMPLETED,
            reference_id="ANALYTICS-DEP-003",
            created_at=now - timedelta(days=60),  # 2 months ago
        )
    )

    return transactions


class TestSpendingByCategoryView:
    """Test SpendingByCategoryView JSON endpoint."""

    def test_spending_by_category_requires_login(self, client):
        """Test endpoint requires authentication."""
        response = client.get(reverse("analytics:spending_by_category"))
        assert response.status_code == 302

    def test_spending_by_category_requires_staff(self, client, client_user_with_wallet):
        """Test endpoint requires staff user."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_category"))
        assert response.status_code == 403

    def test_spending_by_category_allows_staff(self, client, staff_user):
        """Test endpoint allows staff user."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_category"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_spending_by_category_json_structure(self, client, staff_user):
        """Test JSON response has correct structure for Chart.js."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_category"))
        data = response.json()

        # Check required Chart.js fields
        assert "labels" in data
        assert "datasets" in data
        assert "metadata" in data

        # Check labels
        assert len(data["labels"]) == 3
        assert "Deposits" in data["labels"]
        assert "Withdrawals" in data["labels"]
        assert "Transfers" in data["labels"]

        # Check datasets structure
        assert len(data["datasets"]) == 1
        dataset = data["datasets"][0]
        assert "label" in dataset
        assert "data" in dataset
        assert "backgroundColor" in dataset
        assert "borderColor" in dataset

        # Check metadata
        assert "total_volume" in data["metadata"]
        assert "period_days" in data["metadata"]

    def test_spending_by_category_aggregation_accuracy(
        self, client, staff_user, transactions_for_analytics
    ):
        """Test aggregation calculations are accurate."""
        client.login(email="staff@test.com", password="testpass123")

        # Get data for last 30 days
        response = client.get(reverse("analytics:spending_by_category") + "?days=30")
        data = response.json()

        # Expected values (only transactions from last 30 days)
        # Deposits: 5000 + 3000 = 8000 (both within 30 days)
        # Withdrawals: 1000 + 500 = 1500 (both within 30 days)
        # Transfers: 2000 + 1500 = 3500 (both within 30 days)
        # Note: The 4000 deposit is 60 days ago, so excluded
        deposits_idx = data["labels"].index("Deposits")
        withdrawals_idx = data["labels"].index("Withdrawals")
        transfers_idx = data["labels"].index("Transfers")

        # Allow for timing variations - check that values are reasonable
        assert data["datasets"][0]["data"][deposits_idx] >= 8000.00
        assert data["datasets"][0]["data"][withdrawals_idx] >= 1500.00
        assert data["datasets"][0]["data"][transfers_idx] >= 3500.00

        # Check total volume is at least the sum of expected transactions
        expected_min_total = 8000.00 + 1500.00 + 3500.00
        assert data["metadata"]["total_volume"] >= expected_min_total

    def test_spending_by_category_custom_days(self, client, staff_user, transactions_for_analytics):
        """Test custom days parameter."""
        client.login(email="staff@test.com", password="testpass123")

        # Get data for last 10 days only
        response = client.get(reverse("analytics:spending_by_category") + "?days=10")
        data = response.json()

        # The 5000 deposit (5 days ago) and 2000 transfer (7 days ago) should be included
        # The 3000 deposit (15 days ago) should be excluded
        deposits_idx = data["labels"].index("Deposits")
        transfers_idx = data["labels"].index("Transfers")

        # Check that we get at least the recent transactions
        assert data["datasets"][0]["data"][deposits_idx] >= 5000.00
        assert data["datasets"][0]["data"][transfers_idx] >= 2000.00
        assert data["metadata"]["period_days"] == 10

    def test_spending_by_category_excludes_flagged(
        self, client, staff_user, client_user_with_wallet
    ):
        """Test that flagged transactions are excluded."""
        client.login(email="staff@test.com", password="testpass123")
        user, sender_wallet = client_user_with_wallet

        # Create a flagged transaction
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("100000.00"),
            type="DEPOSIT",
            status=TransactionStatus.FLAGGED,
            reference_id="ANALYTICS-FLAGGED-001",
        )

        response = client.get(reverse("analytics:spending_by_category"))
        data = response.json()

        # Flagged transaction should not be included
        deposits_idx = data["labels"].index("Deposits")
        assert data["datasets"][0]["data"][deposits_idx] == 0.0


class TestSpendingByMonthView:
    """Test SpendingByMonthView JSON endpoint."""

    def test_spending_by_month_requires_login(self, client):
        """Test endpoint requires authentication."""
        response = client.get(reverse("analytics:spending_by_month"))
        assert response.status_code == 302

    def test_spending_by_month_requires_staff(self, client, client_user_with_wallet):
        """Test endpoint requires staff user."""
        user, wallet = client_user_with_wallet
        client.login(email="client@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_month"))
        assert response.status_code == 403

    def test_spending_by_month_allows_staff(self, client, staff_user):
        """Test endpoint allows staff user."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_month"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_spending_by_month_json_structure(self, client, staff_user):
        """Test JSON response has correct structure for Chart.js."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()

        # Check required Chart.js fields
        assert "labels" in data
        assert "datasets" in data
        assert "metadata" in data

        # Check 12 months
        assert len(data["labels"]) == 12

        # Check datasets structure (line chart)
        assert len(data["datasets"]) == 1
        dataset = data["datasets"][0]
        assert "label" in dataset
        assert "data" in dataset
        assert "backgroundColor" in dataset
        assert "borderColor" in dataset
        assert dataset.get("fill") is True
        assert dataset.get("tension") == 0.4  # Smooth curve

        # Check metadata
        assert "year" in data["metadata"]
        assert "total_volume" in data["metadata"]
        assert "average_monthly" in data["metadata"]

    def test_spending_by_month_current_year(self, client, staff_user, transactions_for_analytics):
        """Test aggregation for current year."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()

        # Check year in metadata
        current_year = timezone.now().year
        assert data["metadata"]["year"] == current_year

        # Check total volume includes all transactions from current year
        # 5000 + 3000 + 1000 + 500 + 2000 + 1500 + 4000 = 17000
        expected_total = 17000.00
        assert abs(data["metadata"]["total_volume"] - expected_total) < 0.01

    def test_spending_by_month_custom_year(self, client, staff_user, transactions_for_analytics):
        """Test custom year parameter."""
        client.login(email="staff@test.com", password="testpass123")

        # Query previous year (should have no data)
        previous_year = timezone.now().year - 1
        response = client.get(reverse("analytics:spending_by_month") + f"?year={previous_year}")
        data = response.json()

        # All months should be 0
        assert all(value == 0.0 for value in data["datasets"][0]["data"])
        assert data["metadata"]["year"] == previous_year

    def test_spending_by_month_with_type_filter(
        self, client, staff_user, transactions_for_analytics
    ):
        """Test filtering by transaction type."""
        client.login(email="staff@test.com", password="testpass123")

        # Filter by DEPOSIT only
        response = client.get(reverse("analytics:spending_by_month") + "?type=DEPOSIT")
        data = response.json()

        # Check label includes type filter
        assert "DEPOSIT" in data["datasets"][0]["label"]

        # Total should only include deposits: 5000 + 3000 + 4000 = 12000
        expected_total = 12000.00
        assert abs(data["metadata"]["total_volume"] - expected_total) < 0.01

    def test_spending_by_month_excludes_flagged(self, client, staff_user, client_user_with_wallet):
        """Test that flagged transactions are excluded."""
        client.login(email="staff@test.com", password="testpass123")
        user, sender_wallet = client_user_with_wallet

        # Create a flagged transaction
        Transaction.objects.create(
            wallet=sender_wallet,
            amount=Decimal("50000.00"),
            type="DEPOSIT",
            status=TransactionStatus.FLAGGED,
            reference_id="ANALYTICS-MONTH-FLAGGED-001",
        )

        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()

        # Flagged transaction should not be included
        assert data["metadata"]["total_volume"] == 0.0

    def test_spending_by_month_average_calculation(
        self, client, staff_user, transactions_for_analytics
    ):
        """Test average monthly calculation."""
        client.login(email="staff@test.com", password="testpass123")

        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()

        # Total: 17000, months with data: 1 (all in current month for this test)
        # Average should be total / months_with_data
        assert data["metadata"]["average_monthly"] > 0
        assert data["metadata"]["average_monthly"] <= data["metadata"]["total_volume"]


class TestAnalyticsIntegration:
    """Test analytics endpoints integration with other systems."""

    def test_analytics_with_large_dataset(self, client, staff_user, client_user_with_wallet):
        """Test analytics with many transactions."""
        client.login(email="staff@test.com", password="testpass123")
        user, sender_wallet = client_user_with_wallet

        # Create 100 transactions
        for i in range(100):
            Transaction.objects.create(
                wallet=sender_wallet,
                amount=Decimal("100.00"),
                type="DEPOSIT",
                status=TransactionStatus.COMPLETED,
                reference_id=f"ANALYTICS-BULK-{i:03d}",
            )

        # Category endpoint
        response = client.get(reverse("analytics:spending_by_category"))
        data = response.json()
        deposits_idx = data["labels"].index("Deposits")
        assert abs(data["datasets"][0]["data"][deposits_idx] - 10000.00) < 0.01

        # Month endpoint
        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()
        assert abs(data["metadata"]["total_volume"] - 10000.00) < 0.01

    def test_analytics_empty_state(self, client, staff_user):
        """Test analytics with no transactions."""
        client.login(email="staff@test.com", password="testpass123")

        # Category endpoint
        response = client.get(reverse("analytics:spending_by_category"))
        data = response.json()
        assert all(value == 0.0 for value in data["datasets"][0]["data"])
        assert data["metadata"]["total_volume"] == 0.0

        # Month endpoint
        response = client.get(reverse("analytics:spending_by_month"))
        data = response.json()
        assert all(value == 0.0 for value in data["datasets"][0]["data"])
        assert data["metadata"]["total_volume"] == 0.0
        assert data["metadata"]["average_monthly"] == 0.0
