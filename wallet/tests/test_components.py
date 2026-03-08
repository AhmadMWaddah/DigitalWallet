"""
Tests for Phase 3 frontend components.

Verifies component rendering and template structure.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from accounts.models import UserType
from wallet.views import DashboardView

CustomUser = get_user_model()


@pytest.mark.django_db
class TestComponentRendering:
    """Test reusable component rendering."""

    def test_balance_card_component_renders(self):
        """Test that balance_card.html component renders correctly."""
        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/balance_card.html' with wallet=wallet %}
        """)

        context = Context(
            {"wallet": type("Wallet", (), {"balance": "1000.00", "is_frozen": False})()}
        )

        rendered = template.render(context)

        assert "Available Balance" in rendered
        assert "1000.00" in rendered
        assert "Active" in rendered

    def test_balance_card_frozen_state(self):
        """Test that balance_card shows frozen state."""
        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/balance_card.html' with wallet=wallet %}
        """)

        context = Context(
            {"wallet": type("Wallet", (), {"balance": "500.00", "is_frozen": True})()}
        )

        rendered = template.render(context)

        assert "Frozen" in rendered

    def test_transaction_item_component_renders(self):
        """Test that transaction_item.html component renders correctly."""
        from datetime import datetime

        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/transaction_item.html' with transaction=transaction %}
        """)

        transaction = type(
            "Transaction",
            (),
            {
                "type": "DEPOSIT",
                "get_type_display": "Deposit",
                "amount": "250.00",
                "created_at": datetime.now(),
                "status": "COMPLETED",
                "get_status_display": "Completed",
                "description": "Test deposit",
                "wallet": None,
                "counterparty_wallet": None,
            },
        )()

        context = Context({"transaction": transaction})
        rendered = template.render(context)

        assert "Deposit" in rendered
        assert "$250.00" in rendered
        assert "Completed" in rendered

    def test_alert_component_renders_success(self):
        """Test that alert.html component renders success message."""
        from django.contrib.messages import Message
        from django.contrib.messages.constants import SUCCESS
        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/alert.html' with message=message %}
        """)

        message = Message(level=SUCCESS, message="Operation successful!")

        context = Context({"message": message})
        rendered = template.render(context)

        assert "alert-success" in rendered
        assert "Operation successful!" in rendered

    def test_alert_component_renders_error(self):
        """Test that alert.html component renders error message."""
        from django.contrib.messages import Message
        from django.contrib.messages.constants import ERROR
        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/alert.html' with message=message %}
        """)

        message = Message(level=ERROR, message="Operation failed!")

        context = Context({"message": message})
        rendered = template.render(context)

        assert "alert-error" in rendered or "alert-danger" in rendered
        assert "Operation failed!" in rendered

    def test_modal_component_renders(self):
        """Test that modal.html component renders correctly."""
        from django.template import Context, Template

        template = Template("""
            {% load static %}
            {% include 'components/modal.html' with title="Test Modal" content="Test content" %}
        """)

        context = Context({"title": "Test Modal", "content": "Test content"})

        rendered = template.render(context)

        assert "modal-overlay" in rendered
        assert "Test Modal" in rendered
        assert "Test content" in rendered


@pytest.mark.django_db
class TestDashboardViewComponents:
    """Test DashboardView renders all components correctly."""

    def test_dashboard_view_uses_correct_template(self):
        """Test that DashboardView uses wallet/dashboard.html."""
        user = CustomUser.objects.create_user(
            email="dashboard-test@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        factory = RequestFactory()
        request = factory.get("/dashboard/")
        request.user = user

        view = DashboardView()
        view.setup(request)
        response = view.get(request)

        assert "wallet/dashboard.html" in response.template_name

    def test_dashboard_view_context_data(self):
        """Test that DashboardView provides correct context."""
        user = CustomUser.objects.create_user(
            email="dashboard-context@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        factory = RequestFactory()
        request = factory.get("/dashboard/")
        request.user = user

        view = DashboardView()
        view.setup(request)
        context = view.get_context_data()

        assert "wallet" in context
        assert "transactions" in context
        assert "deposit_form" in context  # Forms are in context

    def test_dashboard_view_requires_login(self):
        """Test that DashboardView requires authentication."""
        from django.contrib.auth.mixins import LoginRequiredMixin

        assert issubclass(DashboardView, LoginRequiredMixin)
