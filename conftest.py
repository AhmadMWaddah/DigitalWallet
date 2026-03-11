"""
Pytest configuration and fixtures for Digital Wallet project.
"""

import pytest

# -- Pytest Configuration


def pytest_configure():
    """Configure Celery for testing."""
    # Use eager mode for testing (tasks run synchronously)
    from celery import current_app

    current_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=False,  # Don't propagate exceptions, return them
        task_store_eager_result=True,
    )


# -- Fixtures


@pytest.fixture
def db_access():
    """Fixture to enable database access for tests."""
    pass


@pytest.fixture
def client_user(db):
    """
    Create a test client user with profile and wallet.

    Returns:
        tuple: (user, client_profile)
    """
    from django.contrib.auth import get_user_model

    from accounts.models import ClientProfile, UserType

    CustomUser = get_user_model()

    user = CustomUser.objects.create_user(
        email="testclient@example.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    client_profile = ClientProfile.objects.get(user=user)
    return user, client_profile


@pytest.fixture
def auth_client(client_user):
    """
    Create an authenticated test client.

    Returns:
        Client: Logged-in Django test client
    """
    from django.test import Client

    user, client_profile = client_user
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def auth_client_no_wallet(db):
    """
    Create an authenticated client without a wallet.

    Returns:
        Client: Logged-in Django test client
    """
    from django.contrib.auth import get_user_model
    from django.test import Client

    from accounts.models import UserType

    CustomUser = get_user_model()

    user = CustomUser.objects.create_user(
        email="testclient-nowallet@example.com",
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    client = Client()
    client.force_login(user)
    return client
