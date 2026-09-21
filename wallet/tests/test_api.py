"""
Tests for the DRF wallet API (v1).

Covers auth, ownership isolation, happy paths, validation errors,
and reference_id idempotency.
"""

from decimal import Decimal

from django.urls import reverse

from accounts.models import CustomUser, UserType
from wallet.models import TransactionStatus, Wallet


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


class TestWalletApiAuth:
    """Test API authentication and ownership isolation."""

    def test_wallet_requires_auth(self, client, db):
        """Test unauthenticated wallet request returns 403."""
        response = client.get(reverse("wallet_api:wallet-detail"))
        assert response.status_code == 403

    def test_client_sees_only_own_wallet(self, client, db):
        """Test client A cannot see client B's balance."""
        _make_client("api-a@test.com", balance=Decimal("111.11"))
        _make_client("api-b@test.com", balance=Decimal("222.22"))
        client.login(email="api-a@test.com", password="testpass123")

        response = client.get(reverse("wallet_api:wallet-detail"))

        assert response.status_code == 200
        assert response.json()["balance"] == "111.11"

    def test_transactions_only_own(self, client, db):
        """Test transaction list contains only own transactions."""
        _make_client("api-c@test.com")
        _make_client("api-d@test.com")
        client.login(email="api-c@test.com", password="testpass123")

        response = client.get(reverse("wallet_api:transaction-list"))

        assert response.status_code == 200
        assert response.json()["results"] == []


class TestWalletApiWrites:
    """Test deposit/withdraw/transfer happy paths and balances."""

    def test_deposit(self, client, db):
        """Test deposit returns 201 and moves the balance."""
        _make_client("api-dep@test.com", balance=Decimal("100.00"))
        client.login(email="api-dep@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:deposit"),
            {"amount": "25.50", "description": "api test"},
            content_type="application/json",
        )

        assert response.status_code == 201
        wallet = Wallet.objects.get(client_profile__user__email="api-dep@test.com")
        assert wallet.balance == Decimal("125.50")

    def test_withdraw(self, client, db):
        """Test withdraw returns 201 and moves the balance."""
        _make_client("api-wdr@test.com", balance=Decimal("100.00"))
        client.login(email="api-wdr@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:withdraw"),
            {"amount": "40.00"},
            content_type="application/json",
        )

        assert response.status_code == 201
        wallet = Wallet.objects.get(client_profile__user__email="api-wdr@test.com")
        assert wallet.balance == Decimal("60.00")

    def test_transfer(self, client, db):
        """Test transfer returns 201 and moves both balances."""
        _make_client("api-snd@test.com", balance=Decimal("100.00"))
        _make_client("api-rcv@test.com", balance=Decimal("10.00"))
        client.login(email="api-snd@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:transfer"),
            {"recipient_email": "api-rcv@test.com", "amount": "30.00"},
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["status"] == TransactionStatus.COMPLETED
        sender = Wallet.objects.get(client_profile__user__email="api-snd@test.com")
        receiver = Wallet.objects.get(client_profile__user__email="api-rcv@test.com")
        assert sender.balance == Decimal("70.00")
        assert receiver.balance == Decimal("40.00")


class TestWalletApiValidation:
    """Test invalid operations return 400 with usable errors."""

    def test_deposit_negative_amount(self, client, db):
        """Test negative deposit returns 400."""
        _make_client("api-neg@test.com")
        client.login(email="api-neg@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:deposit"),
            {"amount": "-5.00"},
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_withdraw_insufficient_funds(self, client, db):
        """Test over-balance withdraw returns 400."""
        _make_client("api-poor@test.com", balance=Decimal("5.00"))
        client.login(email="api-poor@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:withdraw"),
            {"amount": "500.00"},
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_transfer_to_self(self, client, db):
        """Test self-transfer returns 400."""
        _make_client("api-self@test.com")
        client.login(email="api-self@test.com", password="testpass123")

        response = client.post(
            reverse("wallet_api:transfer"),
            {"recipient_email": "api-self@test.com", "amount": "10.00"},
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_duplicate_reference_id(self, client, db):
        """Test reusing a reference_id returns 400 (idempotency)."""
        _make_client("api-dup@test.com", balance=Decimal("100.00"))
        client.login(email="api-dup@test.com", password="testpass123")
        url = reverse("wallet_api:deposit")
        payload = {"amount": "10.00", "reference_id": "API-DUP-1"}

        first = client.post(url, payload, content_type="application/json")
        assert first.status_code == 201

        second = client.post(url, payload, content_type="application/json")
        assert second.status_code == 400
