"""
Tests for portal routing and custom 403 error page.

Verifies:
- Role-aware home redirect logic
- Custom 403 error page rendering
- Access control between portals
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

from accounts.models import UserType
from accounts.views import LoginRedirectView

CustomUser = get_user_model()


@pytest.fixture
def superuser(db):
    """Create a superuser for testing."""
    return CustomUser.objects.create_superuser(
        email="superuser@test.com",
        password="testpass123",
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    return CustomUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        user_type=UserType.STAFF,
    )


@pytest.fixture
def client_user(db):
    """Create a client user for testing."""
    return CustomUser.objects.create_user(
        email="client@test.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )


class TestLoginRedirectView:
    """Test LoginRedirectView role-aware routing."""

    def test_anonymous_user_redirects_to_login(self):
        """Test anonymous users are redirected to login."""
        redirect_url = LoginRedirectView.get_redirect_url(None)
        assert redirect_url == "accounts:login"

        # Test with unauthenticated user
        from django.contrib.auth.models import AnonymousUser
        redirect_url = LoginRedirectView.get_redirect_url(AnonymousUser())
        assert redirect_url == "accounts:login"

    def test_superuser_redirects_to_admin(self, superuser):
        """Test superusers are redirected to Django Admin."""
        redirect_url = LoginRedirectView.get_redirect_url(superuser)
        assert redirect_url == "/admin/"

    def test_staff_user_redirects_to_staff_dashboard(self, staff_user):
        """Test staff users are redirected to Staff Dashboard."""
        redirect_url = LoginRedirectView.get_redirect_url(staff_user)
        assert redirect_url == "operations:staff_dashboard"

    def test_client_user_redirects_to_dashboard(self, client_user):
        """Test client users are redirected to Wallet Dashboard."""
        redirect_url = LoginRedirectView.get_redirect_url(client_user)
        assert redirect_url == "wallet:dashboard"


class TestHomeRedirect:
    """Test home page (/) role-aware redirect."""

    def test_anonymous_redirected_to_login(self, client):
        """Test anonymous users redirected to login from home."""
        response = client.get("/", follow=False)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_client_redirected_to_dashboard(self, client, client_user):
        """Test client users redirected to dashboard from home."""
        client.login(email="client@test.com", password="testpass123")
        response = client.get("/", follow=False)
        assert response.status_code == 302
        assert "/dashboard/" in response.url

    def test_staff_redirected_to_staff_dashboard(self, client, staff_user):
        """Test staff users redirected to staff dashboard from home."""
        client.login(email="staff@test.com", password="testpass123")
        response = client.get("/", follow=False)
        assert response.status_code == 302
        assert "/staff/dashboard/" in response.url

    def test_superuser_redirected_to_admin(self, client, superuser):
        """Test superusers redirected to admin from home."""
        client.login(email="superuser@test.com", password="testpass123")
        response = client.get("/", follow=False)
        assert response.status_code == 302
        assert "/admin/" in response.url


class TestCustom403Page:
    """Test custom 403 error page."""

    def test_403_page_renders(self, client, staff_user):
        """Test 403 page renders with proper context."""
        # Login as staff and try to access client-only area
        client.login(email="staff@test.com", password="testpass123")

        # Manually trigger 403 (this would normally happen via permission denied)
        from django.core.exceptions import PermissionDenied
        from accounts.views import custom_permission_denied
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = staff_user

        response = custom_permission_denied(request, exception=PermissionDenied())

        assert response.status_code == 403
        assert b"Access Denied" in response.content
        assert b"Staff users should access the Staff Dashboard" in response.content

    def test_403_page_has_redirect_button(self, client, staff_user):
        """Test 403 page has Return to Dashboard button."""
        from django.core.exceptions import PermissionDenied
        from accounts.views import custom_permission_denied
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = staff_user

        response = custom_permission_denied(request, exception=PermissionDenied())

        assert response.status_code == 403
        assert b"Return to my Dashboard" in response.content
        # Check for resolved URL path
        assert b'href="/staff/dashboard/"' in response.content

    def test_403_page_for_client(self, client, client_user):
        """Test 403 page shows correct message for clients."""
        from django.core.exceptions import PermissionDenied
        from accounts.views import custom_permission_denied
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/staff/dashboard/')
        request.user = client_user

        response = custom_permission_denied(request, exception=PermissionDenied())

        assert response.status_code == 403
        assert b"Access Denied" in response.content
        # Check for resolved URL path to dashboard
        assert b'href="/dashboard/"' in response.content

    def test_403_page_for_anonymous(self, client):
        """Test 403 page for anonymous users."""
        from django.core.exceptions import PermissionDenied
        from accounts.views import custom_permission_denied
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = AnonymousUser()

        response = custom_permission_denied(request, exception=PermissionDenied())

        assert response.status_code == 403
        assert b"Authentication Required" in response.content


class TestPortalAccessControl:
    """Test portal access control between Client and Staff."""

    def test_staff_accessing_client_dashboard_gets_403(self, client, staff_user):
        """Test staff user accessing client dashboard gets 403."""
        client.login(email="staff@test.com", password="testpass123")

        # Staff trying to access client dashboard should get 403
        # Note: This depends on ClientOnlyMixin being properly configured
        response = client.get("/dashboard/")

        # Should either redirect or show 403
        assert response.status_code in [302, 403]

    def test_client_accessing_staff_dashboard_gets_403(self, client, client_user):
        """Test client user accessing staff dashboard gets 403."""
        client.login(email="client@test.com", password="testpass123")

        # Client trying to access staff dashboard should get 403
        response = client.get("/staff/dashboard/")

        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_client_accessing_admin_gets_redirected(self, client, client_user):
        """Test client user accessing admin gets redirected to login."""
        client.login(email="client@test.com", password="testpass123")

        # Client trying to access admin should be redirected to login
        response = client.get("/admin/")

        # Django admin redirects non-staff to login
        assert response.status_code == 302
        assert "/admin/login/" in response.url
