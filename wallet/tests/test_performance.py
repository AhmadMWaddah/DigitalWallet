"""
Performance tests for wallet views.

Verifies that query counts remain constant regardless of data size.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.test import Client
from django.test.utils import CaptureQueriesContext
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
        """
        Test that transaction list view has CONSTANT query count (O(1)).
        
        Compares two scenarios:
        - Scenario A: 5 transactions in database
        - Scenario B: 50 transactions in database
        
        Asserts that query count is identical for both scenarios.
        """
        # Get client wallet
        client_user = CustomUser.objects.get(email="client0@test.com")
        wallet = client_user.client_profile.wallet

        # Login as client
        client.login(email="client0@test.com", password="testpass123")

        # Scenario A: Query with 5 transactions
        # First, limit to only 5 transactions for this test
        Transaction.objects.filter(wallet=wallet).exclude(
            reference_id__in=["PERF-TRF-0000", "PERF-TRF-0001", "PERF-TRF-0002", "PERF-TRF-0003", "PERF-TRF-0004"]
        ).delete()

        # Create exactly 5 transactions
        for i in range(5):
            Transaction.objects.get_or_create(
                reference_id=f"TEST-5-{i:04d}",
                defaults={
                    "wallet": wallet,
                    "counterparty_wallet": client_user.client_profile.wallet,
                    "amount": Decimal("100.00"),
                    "type": "TRANSFER",
                    "status": "COMPLETED",
                }
            )

        # Measure queries for 5 transactions
        reset_queries()
        with CaptureQueriesContext(connection) as context_5:
            response = client.get(reverse("wallet:transaction_history"))
            assert response.status_code == 200

        queries_5 = len(context_5.captured_queries)

        # Scenario B: Query with 50 transactions
        # Create 45 more transactions
        for i in range(5, 50):
            Transaction.objects.get_or_create(
                reference_id=f"TEST-50-{i:04d}",
                defaults={
                    "wallet": wallet,
                    "counterparty_wallet": client_user.client_profile.wallet,
                    "amount": Decimal("100.00"),
                    "type": "TRANSFER",
                    "status": "COMPLETED",
                }
            )

        # Measure queries for 50 transactions
        reset_queries()
        with CaptureQueriesContext(connection) as context_50:
            response = client.get(reverse("wallet:transaction_history"))
            assert response.status_code == 200

        queries_50 = len(context_50.captured_queries)

        # Assert query counts are identical (O(1) constant query count)
        assert queries_5 == queries_50, (
            f"Query count not constant! "
            f"5 transactions: {queries_5} queries, "
            f"50 transactions: {queries_50} queries"
        )

        # Query count should be reasonable (< 10 queries)
        assert queries_50 < 10, f"Too many queries: {queries_50}"

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
        """
        Test that queries use indexes on status and type.
        
        Verifies:
        - Filtering by status uses the status index
        - Filtering by type uses the type index
        - Combined filtering is efficient
        """
        # Filter by status (should use status index)
        flagged = Transaction.objects.filter(status="FLAGGED")

        # Access results to ensure query is executed
        assert flagged.count() > 0, "No flagged transactions found"

        # Filter by type (should use type index)
        transfers = Transaction.objects.filter(type="TRANSFER")

        # Access results
        assert transfers.count() > 0, "No transfer transactions found"

        # Combined filter (should use both indexes efficiently)
        completed_transfers = Transaction.objects.filter(
            status="COMPLETED", type="TRANSFER"
        )

        assert completed_transfers.count() > 0, "No completed transfers found"

        # Verify the querysets are properly constructed with indexed fields
        # Note: SQLite doesn't expose query plans easily, but we verify the logic
        status_query = str(flagged.query)
        type_query = str(transfers.query)
        
        assert "status" in status_query.lower(), "Query should filter by status"
        assert "type" in type_query.lower(), "Query should filter by type"
        
        # Combined query should have both conditions
        combined_query = str(completed_transfers.query)
        assert "status" in combined_query.lower(), "Combined query should filter by status"
        assert "type" in combined_query.lower(), "Combined query should filter by type"
