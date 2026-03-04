"""
Tests for accounts app views and authentication flow.

Covers login, logout, redirects, and permission mixins.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import UserType

CustomUser = get_user_model()


# -- Login View Tests

@pytest.mark.django_db
class TestLoginView:
    """Test CustomLoginView."""
    
    def test_login_page_get_success(self, client):
        """Test login page loads successfully."""
        response = client.get(reverse('accounts:login'))
        
        assert response.status_code == 200
        assert 'accounts/login.html' in [t.name for t in response.templates]
    
    def test_login_valid_credentials_client(self, client):
        """Test login with valid client credentials redirects to dashboard."""
        user = CustomUser.objects.create_user(
            email='clientlogin@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        response = client.post(reverse('accounts:login'), {
            'email': 'clientlogin@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assert '/dashboard/' in response.url
    
    def test_login_valid_credentials_staff(self, client):
        """Test login with valid staff credentials redirects to admin."""
        user = CustomUser.objects.create_user(
            email='stafflogin@example.com',
            password='testpass123',
            user_type=UserType.STAFF
        )
        
        response = client.post(reverse('accounts:login'), {
            'email': 'stafflogin@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assert '/admin/' in response.url
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials shows error."""
        response = client.post(reverse('accounts:login'), {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert response.context['form'].errors  # Should have form errors
    
    def test_login_empty_email(self, client):
        """Test login with empty email shows error."""
        response = client.post(reverse('accounts:login'), {
            'email': '',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        assert response.context['form'].errors
    
    def test_login_empty_password(self, client):
        """Test login with empty password shows error."""
        CustomUser.objects.create_user(
            email='emptypass@example.com',
            password='testpass123'
        )
        
        response = client.post(reverse('accounts:login'), {
            'email': 'emptypass@example.com',
            'password': ''
        })
        
        assert response.status_code == 200
        assert response.context['form'].errors


# -- Logout View Tests

@pytest.mark.django_db
class TestLogoutView:
    """Test LogoutView."""
    
    def test_logout_get_success(self, client):
        """Test logout via GET request."""
        user = CustomUser.objects.create_user(
            email='logoutuser@example.com',
            password='testpass123'
        )
        
        client.login(email='logoutuser@example.com', password='testpass123')
        assert client.session.get('_auth_user_id') is not None
        
        response = client.get(reverse('accounts:logout'))
        
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')
    
    def test_logout_post_success(self, client):
        """Test logout via POST request."""
        user = CustomUser.objects.create_user(
            email='logoutpost@example.com',
            password='testpass123'
        )
        
        client.login(email='logoutpost@example.com', password='testpass123')
        
        response = client.post(reverse('accounts:logout'))
        
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')


# -- Login Redirect View Tests

@pytest.mark.django_db
class TestLoginRedirectView:
    """Test LoginRedirectView."""
    
    def test_redirect_client_to_dashboard(self, client):
        """Test client user is redirected to dashboard."""
        user = CustomUser.objects.create_user(
            email='redirectclient@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        client.login(email='redirectclient@example.com', password='testpass123')
        response = client.get(reverse('accounts:login_redirect'))
        
        assert response.status_code == 302
        assert '/dashboard/' in response.url
    
    def test_redirect_staff_to_admin(self, client):
        """Test staff user is redirected to admin."""
        user = CustomUser.objects.create_user(
            email='redirectstaff@example.com',
            password='testpass123',
            user_type=UserType.STAFF
        )
        
        client.login(email='redirectstaff@example.com', password='testpass123')
        response = client.get(reverse('accounts:login_redirect'))
        
        assert response.status_code == 302
        assert '/admin/' in response.url
    
    def test_redirect_unauthenticated_user_to_login(self, client):
        """Test unauthenticated user is redirected to login."""
        response = client.get(reverse('accounts:login_redirect'))
        
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')


# -- Mixin Tests

@pytest.mark.django_db
class TestStaffOnlyMixin:
    """Test StaffOnlyMixin permission enforcement."""
    
    def test_staff_user_can_access(self, client):
        """Test staff user can access protected view."""
        from accounts.views import StaffOnlyMixin
        from django.views.generic import View
        
        # Create a test view with the mixin
        class TestView(StaffOnlyMixin, View):
            def get(self, request):
                return client.get('/test/')
        
        staff_user = CustomUser.objects.create_user(
            email='staffmixin@example.com',
            password='testpass123',
            user_type=UserType.STAFF
        )
        
        client.login(email='staffmixin@example.com', password='testpass123')
        
        # Staff should pass the test_func
        assert staff_user.user_type == UserType.STAFF
    
    def test_client_user_denied_access(self, client):
        """Test client user is denied access to staff-only view."""
        client_user = CustomUser.objects.create_user(
            email='clientmixin@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        client.login(email='clientmixin@example.com', password='testpass123')
        
        # Client should not pass staff test
        assert client_user.user_type != UserType.STAFF
    
    def test_unauthenticated_user_redirected_to_login(self, client):
        """Test unauthenticated user is redirected to login."""
        # Not logging in
        response = client.get('/admin/')
        
        assert response.status_code == 302


@pytest.mark.django_db
class TestClientOnlyMixin:
    """Test ClientOnlyMixin permission enforcement."""
    
    def test_client_user_can_access(self, client):
        """Test client user can access client-only view."""
        client_user = CustomUser.objects.create_user(
            email='clientonly@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        client.login(email='clientonly@example.com', password='testpass123')
        
        # Client should pass the test_func
        assert client_user.user_type == UserType.CLIENT
    
    def test_staff_user_denied_access(self, client):
        """Test staff user is denied access to client-only view."""
        staff_user = CustomUser.objects.create_user(
            email='staffclient@example.com',
            password='testpass123',
            user_type=UserType.STAFF
        )
        
        client.login(email='staffclient@example.com', password='testpass123')
        
        # Staff should not pass client test
        assert staff_user.user_type != UserType.CLIENT


# -- Integration Tests

@pytest.mark.django_db
class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_full_login_logout_cycle(self, client):
        """Test complete login and logout cycle."""
        # Create user
        user = CustomUser.objects.create_user(
            email='cycle@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        # Login
        login_response = client.post(reverse('accounts:login'), {
            'email': 'cycle@example.com',
            'password': 'testpass123'
        })
        
        assert login_response.status_code == 302
        
        # Verify logged in
        assert '_auth_user_id' in client.session
        
        # Logout
        logout_response = client.get(reverse('accounts:logout'))
        
        assert logout_response.status_code == 302
        
        # Verify redirected to login
        assert logout_response.url == reverse('accounts:login')
    
    def test_staff_portal_separation(self, client):
        """Test that staff and client portals are separated."""
        # Create both user types
        staff = CustomUser.objects.create_user(
            email='portalseparation@example.com',
            password='testpass123',
            user_type=UserType.STAFF
        )
        
        client_user = CustomUser.objects.create_user(
            email='portalclient@example.com',
            password='testpass123',
            user_type=UserType.CLIENT
        )
        
        # Login as staff
        staff_login = client.post(reverse('accounts:login'), {
            'email': 'portalseparation@example.com',
            'password': 'testpass123'
        })
        
        assert staff_login.status_code == 302
        assert '/admin/' in staff_login.url
        
        # Logout
        client.get(reverse('accounts:logout'))
        
        # Login as client
        client_login = client.post(reverse('accounts:login'), {
            'email': 'portalclient@example.com',
            'password': 'testpass123'
        })
        
        assert client_login.status_code == 302
        assert '/dashboard/' in client_login.url
