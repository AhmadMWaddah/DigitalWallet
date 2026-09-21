"""
Tests for KYC document upload, staff review, and the transfer gate.

Uploads are isolated to tmp_path via override_settings (test settings
do not override MEDIA_ROOT).
"""

from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from accounts.models import ClientProfile, CustomUser, KYCStatus, UserType
from wallet.exceptions import KYCRequiredError
from wallet.models import Wallet
from wallet.services import transfer_funds


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


def _make_staff(email):
    """Create a staff user."""
    return CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.STAFF,
    )


def _pdf(name="id.pdf"):
    """Return a fake PDF upload."""
    return SimpleUploadedFile(name, b"%PDF-1.4 fake-id-document", content_type="application/pdf")


class TestKYCUpload:
    """Test client document upload."""

    def test_upload_sets_pending(self, client, db, tmp_path):
        """Test valid upload moves profile to PENDING with stored document."""
        _make_client("kyc-up@test.com")
        client.login(email="kyc-up@test.com", password="testpass123")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = client.post(reverse("accounts:kyc_upload"), {"document": _pdf()})

        assert response.status_code == 302
        profile = ClientProfile.objects.get(user__email="kyc-up@test.com")
        assert profile.kyc_status == KYCStatus.PENDING
        assert profile.kyc_document
        assert profile.kyc_submitted_at is not None

    def test_upload_rejects_non_document(self, client, db, tmp_path):
        """Test .txt upload is rejected, status stays UNVERIFIED."""
        _make_client("kyc-bad@test.com")
        client.login(email="kyc-bad@test.com", password="testpass123")
        bad = SimpleUploadedFile("id.txt", b"not a document", content_type="text/plain")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = client.post(reverse("accounts:kyc_upload"), {"document": bad})

        assert response.status_code == 200
        profile = ClientProfile.objects.get(user__email="kyc-bad@test.com")
        assert profile.kyc_status == KYCStatus.UNVERIFIED
        assert not profile.kyc_document

    def test_reupload_after_reject_resets_pending(self, client, db, tmp_path):
        """Test rejected client can re-upload, returning to PENDING."""
        user = _make_client("kyc-re@test.com")
        profile = user.client_profile
        profile.kyc_status = KYCStatus.REJECTED
        profile.kyc_rejection_reason = "Blurry photo"
        profile.save()
        client.login(email="kyc-re@test.com", password="testpass123")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = client.post(reverse("accounts:kyc_upload"), {"document": _pdf()})

        assert response.status_code == 302
        profile.refresh_from_db()
        assert profile.kyc_status == KYCStatus.PENDING
        assert profile.kyc_rejection_reason == ""

    def test_staff_cannot_upload(self, client, db, tmp_path):
        """Test staff hitting the client upload page get 403."""
        _make_staff("kyc-staff-up@test.com")
        client.login(email="kyc-staff-up@test.com", password="testpass123")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = client.post(reverse("accounts:kyc_upload"), {"document": _pdf()})

        assert response.status_code == 403


class TestKYCReview:
    """Test staff approve/reject flow."""

    def _pending_profile(self):
        """Create a client with a PENDING profile."""
        user = _make_client("kyc-pend@test.com")
        profile = user.client_profile
        profile.kyc_status = KYCStatus.PENDING
        profile.save()
        return profile

    def test_approve_verifies(self, client, db):
        """Test staff approval marks profile VERIFIED with timestamp."""
        profile = self._pending_profile()
        _make_staff("kyc-appr@test.com")
        client.login(email="kyc-appr@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_kyc", args=[profile.id]), {"action": "approve"}
        )

        assert response.status_code == 302
        profile.refresh_from_db()
        assert profile.kyc_status == KYCStatus.VERIFIED
        assert profile.kyc_verified is True
        assert profile.kyc_verified_at is not None

    def test_reject_needs_reason(self, client, db):
        """Test reject without reason is refused, status unchanged."""
        profile = self._pending_profile()
        _make_staff("kyc-rej@test.com")
        client.login(email="kyc-rej@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_kyc", args=[profile.id]), {"action": "reject"}
        )

        assert response.status_code == 302
        profile.refresh_from_db()
        assert profile.kyc_status == KYCStatus.PENDING

    def test_reject_with_reason(self, client, db):
        """Test reject with reason marks REJECTED and stores it."""
        profile = self._pending_profile()
        _make_staff("kyc-rej2@test.com")
        client.login(email="kyc-rej2@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_kyc", args=[profile.id]),
            {"action": "reject", "reason": "Expired document"},
        )

        assert response.status_code == 302
        profile.refresh_from_db()
        assert profile.kyc_status == KYCStatus.REJECTED
        assert profile.kyc_rejection_reason == "Expired document"
        assert profile.kyc_verified is False

    def test_client_cannot_review(self, client, db):
        """Test clients hitting staff review get 403."""
        profile = self._pending_profile()
        _make_client("kyc-nosy@test.com")
        client.login(email="kyc-nosy@test.com", password="testpass123")

        response = client.post(
            reverse("operations:review_kyc", args=[profile.id]), {"action": "approve"}
        )

        assert response.status_code == 403
        profile.refresh_from_db()
        assert profile.kyc_status == KYCStatus.PENDING


class TestKYCTransferGate:
    """Test the $10,000 transfer gate in transfer_funds."""

    def test_large_transfer_unverified_blocked(self, db):
        """Test >$10k transfer without VERIFIED status raises."""
        _make_client("kyc-gate-s@test.com", balance=Decimal("50000.00"))
        _make_client("kyc-gate-r@test.com", balance=Decimal("100.00"))

        with pytest.raises(KYCRequiredError):
            transfer_funds(
                sender_wallet=Wallet.objects.get(client_profile__user__email="kyc-gate-s@test.com"),
                receiver_wallet=Wallet.objects.get(
                    client_profile__user__email="kyc-gate-r@test.com"
                ),
                amount=Decimal("15000.00"),
                reference_id="KYC-GATE-1",
            )

    def test_large_transfer_verified_allowed(self, db):
        """Test >$10k transfer with VERIFIED status succeeds."""
        sender = _make_client("kyc-ok-s@test.com", balance=Decimal("50000.00"))
        _make_client("kyc-ok-r@test.com", balance=Decimal("100.00"))
        sender.client_profile.kyc_status = KYCStatus.VERIFIED
        sender.client_profile.save()

        transfer_funds(
            sender_wallet=Wallet.objects.get(client_profile__user__email="kyc-ok-s@test.com"),
            receiver_wallet=Wallet.objects.get(client_profile__user__email="kyc-ok-r@test.com"),
            amount=Decimal("15000.00"),
            reference_id="KYC-GATE-2",
        )

        assert Wallet.objects.get(
            client_profile__user__email="kyc-ok-s@test.com"
        ).balance == Decimal("34774.80")

    def test_small_transfer_no_kyc_needed(self, db):
        """Test transfers at/below $10k work without verification."""
        _make_client("kyc-small-s@test.com", balance=Decimal("50000.00"))
        _make_client("kyc-small-r@test.com", balance=Decimal("100.00"))

        transfer_funds(
            sender_wallet=Wallet.objects.get(client_profile__user__email="kyc-small-s@test.com"),
            receiver_wallet=Wallet.objects.get(client_profile__user__email="kyc-small-r@test.com"),
            amount=Decimal("100.00"),
            reference_id="KYC-GATE-3",
        )

        assert Wallet.objects.get(
            client_profile__user__email="kyc-small-s@test.com"
        ).balance == Decimal("49898.30")
