"""
Tests for QR code display and QR scan-to-pay.

Follows TransferView conventions: HTMX requests get alert HTML,
regular requests get JsonResponse with a success flag.
"""

from decimal import Decimal

from django.urls import reverse

from accounts.models import CustomUser, UserType
from wallet.models import Transaction, Wallet
from wallet.qr import build_qr_payload


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


def _wallet_of(email):
    """Return the wallet belonging to the client with this email."""
    return Wallet.objects.get(client_profile__user__email=email)


class TestMyQR:
    """Test the QR display page and PNG endpoint."""

    def test_my_qr_requires_login(self, client, db):
        """Test anonymous users are redirected to login."""
        response = client.get(reverse("wallet:my_qr"))
        assert response.status_code == 302

    def test_my_qr_page_loads(self, client, db):
        """Test logged-in client sees the QR page with image URL."""
        _make_client("qr-me@test.com")
        client.login(email="qr-me@test.com", password="testpass123")

        response = client.get(reverse("wallet:my_qr"))

        assert response.status_code == 200
        assert reverse("wallet:qr_image") in response.context["qr_image_url"]

    def test_qr_image_returns_png(self, client, db):
        """Test QR image endpoint returns a real PNG."""
        _make_client("qr-img@test.com")
        client.login(email="qr-img@test.com", password="testpass123")

        response = client.get(reverse("wallet:qr_image"))

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


class TestQRPay:
    """Test scan-and-pay via pasted QR code."""

    def test_qr_pay_happy_path(self, client, db):
        """Test paying via QR moves both balances and tags metadata."""
        _make_client("qr-snd@test.com", balance=Decimal("100.00"))
        _make_client("qr-rcv@test.com", balance=Decimal("10.00"))
        client.login(email="qr-snd@test.com", password="testpass123")
        code = build_qr_payload(_wallet_of("qr-rcv@test.com").id)

        response = client.post(reverse("wallet:qr_pay"), {"code": code, "amount": "30.00"})

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert _wallet_of("qr-snd@test.com").balance == Decimal("70.00")
        assert _wallet_of("qr-rcv@test.com").balance == Decimal("40.00")
        transaction = Transaction.objects.filter(
            wallet=_wallet_of("qr-snd@test.com"), type="TRANSFER"
        ).latest("created_at")
        assert transaction.metadata.get("payment_method") == "qr_code"

    def test_qr_pay_tampered_code(self, client, db):
        """Test forged QR code is rejected with no balance movement."""
        _make_client("qr-tmp@test.com", balance=Decimal("100.00"))
        _make_client("qr-vic@test.com", balance=Decimal("10.00"))
        client.login(email="qr-tmp@test.com", password="testpass123")
        code = build_qr_payload(_wallet_of("qr-vic@test.com").id) + "forged"

        response = client.post(reverse("wallet:qr_pay"), {"code": code, "amount": "30.00"})

        assert response.status_code == 200
        assert response.json()["success"] is False
        assert _wallet_of("qr-tmp@test.com").balance == Decimal("100.00")
        assert _wallet_of("qr-vic@test.com").balance == Decimal("10.00")

    def test_qr_pay_to_self(self, client, db):
        """Test paying your own code fails."""
        user = _make_client("qr-self@test.com", balance=Decimal("100.00"))
        client.login(email="qr-self@test.com", password="testpass123")
        code = build_qr_payload(user.client_profile.wallet.id)

        response = client.post(reverse("wallet:qr_pay"), {"code": code, "amount": "10.00"})

        assert response.status_code == 200
        assert response.json()["success"] is False
        assert _wallet_of("qr-self@test.com").balance == Decimal("100.00")

    def test_qr_pay_insufficient_funds(self, client, db):
        """Test over-balance QR payment fails."""
        _make_client("qr-poor@test.com", balance=Decimal("5.00"))
        _make_client("qr-rich@test.com", balance=Decimal("10.00"))
        client.login(email="qr-poor@test.com", password="testpass123")
        code = build_qr_payload(_wallet_of("qr-rich@test.com").id)

        response = client.post(reverse("wallet:qr_pay"), {"code": code, "amount": "500.00"})

        assert response.status_code == 200
        assert response.json()["success"] is False
        assert _wallet_of("qr-poor@test.com").balance == Decimal("5.00")
