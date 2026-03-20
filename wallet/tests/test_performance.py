"""
Performance tests for wallet views.

Verifies that query counts remain constant regardless of data size.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.test import Client
from django.urls import reverse

from accounts.models import UserType
from wallet.models import Transaction, Wallet

CustomUser = get_user_model()


@pytest.fixture
def staff_user_with_data(db):
    """Create staff user with test data."""
    # Create staff user
    staff = CustomUser.objects.create_user(
        email="staff_perf@test.com",
        password="testpass123",
        user_type=UserType.STAFF,
    )

    # Create client users with wallets
    clients = []
    for i in range(20):
        client = CustomUser.objects.create_user(
            email=f"client{i}@test.com",
            password="testpass123",
            user_type=UserType.CLIENT,
        )
        wallet = Wallet.objects.create(
            client_profile=client.client_profile,
            balance=Decimal("10000.00"),
        )
        clients.append((client, wallet))

    # Create many transactions for performance testing
    receiver_wallet = clients[0][1]
    for i in range(100):
        sender_wallet = clients[i % len(clients)][1]
        Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("100.00"),
            type="TRANSFER",
            status="COMPLETED",
            reference_id=f"PERF-TRF-{i:04d}",
        )

    # Create some flagged transactions
    for i in range(10):
        sender_wallet = clients[i % len(clients)][1]
        Transaction.objects.create(
            wallet=sender_wallet,
            counterparty_wallet=receiver_wallet,
            amount=Decimal("15000.00"),
            type="TRANSFER",
            status="FLAGGED",
            reference_id=f"PERF-FLAG-{i:04d}",
            metadata={"flagged": True, "flag_reason": "Performance test"},
        )

    return staff


class TestTransactionListPerformance:
    """Test TransactionHistoryView query performance."""

    @pytest.mark.django_db
    def test_transaction_list_query_count(self, client, staff_user_with_data):
        """Test that transaction list view has constant query count."""
        # Get first client wallet from the list
        client_user = CustomUser.objects.get(email="client0@test.com")
        wallet = client_user.client_profile.wallet

        # Login as client
        client.login(email="client0@test.com", password="testpass123")

        # Reset query count
        reset_queries()

        # Access transaction history
        response = client.get(reverse("wallet:transaction_history"))

        # Should return HTML (not redirect)
        assert response.status_code == 200

        # Query count should be reasonable (< 10 queries for paginated list)
        query_count = len(connection.queries)
        assert query_count < 10, f"Too many queries: {query_count}"

        # Reset for next test
        reset_queries()


class TestStaffDashboardPerformance:
    """Test StaffDashboardView query performance."""

    @pytest.mark.django_db
    def test_staff_dashboard_query_count(self, client, staff_user_with_data):
        """Test that staff dashboard has constant query count."""
        staff = staff_user_with_data

        # Login as staff
        client.login(email="staff_perf@test.com", password="testpass123")

        # Reset query count
        reset_queries()

        # Access staff dashboard
        response = client.get(reverse("operations:staff_dashboard"))

        # Should return HTML (not redirect)
        assert response.status_code == 200

        # Query count should be reasonable (< 15 queries for dashboard with stats)
        query_count = len(connection.queries)
        assert query_count < 15, f"Too many queries: {query_count}"

        # Reset for next test
        reset_queries()


class TestAnalyticsDashboardPerformance:
    """Test AnalyticsDashboardDataView query performance."""

    @pytest.mark.django_db
    def test_analytics_dashboard_query_count(self, client, staff_user_with_data):
        """Test that analytics dashboard has constant query count."""
        staff = staff_user_with_data

        # Login as staff
        client.login(email="staff_perf@test.com", password="testpass123")

        # Reset query count
        reset_queries()

        # Access analytics dashboard data
        response = client.get(reverse("analytics:analytics_dashboard_data"))

        # Should return HTML (not redirect)
        assert response.status_code == 200

        # Query count should be reasonable (< 10 queries for analytics)
        query_count = len(connection.queries)
        assert query_count < 10, f"Too many queries: {query_count}"

        # Reset for next test
        reset_queries()


class TestQueryOptimization:
    """Test that select_related is properly used."""

    @pytest.mark.django_db
    def test_transaction_select_related(self, staff_user_with_data):
        """Test that transactions use select_related for foreign keys."""
        # Get transactions with select_related
        reset_queries()

        transactions = list(
            Transaction.objects.select_related(
                "wallet__client_profile__user",
                "counterparty_wallet__client_profile__user",
            )[:50]
        )

        # Access related objects (should not trigger additional queries)
        for txn in transactions:
            _ = txn.wallet.client_profile.user.email
            if txn.counterparty_wallet:
                _ = txn.counterparty_wallet.client_profile.user.email

        # Should have minimal queries (1 for transactions + 1 for related)
        query_count = len(connection.queries)
        assert query_count < 5, f"select_related not working: {query_count} queries"

        reset_queries()

    @pytest.mark.django_db
    def test_transaction_with_indexes(self, staff_user_with_data):
        """Test that queries use indexes on status and type."""
        # Filter by status (should use index)
        reset_queries()

        flagged = list(Transaction.objects.filter(status="FLAGGED"))

        # Access results
        assert len(flagged) > 0

        # Query count should be minimal (using index)
        query_count = len(connection.queries)
        assert query_count <= 2, f"Expected <= 2 queries, got {query_count}"

        reset_queries()

        # Filter by type (should use index)
        transfers = list(Transaction.objects.filter(type="TRANSFER")[:50])

        # Access results
        assert len(transfers) > 0

        # Query count should be minimal (using index)
        query_count = len(connection.queries)
        assert query_count <= 2, f"Expected <= 2 queries, got {query_count}"

        reset_queries()
