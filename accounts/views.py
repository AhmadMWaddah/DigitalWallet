"""
Accounts app views.

Handles user authentication with portal-based redirects.
"""

from django import forms
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, View

from .forms import ClientRegistrationForm
from .models import UserType

CustomUser = get_user_model()

# -- Authentication Form


class EmailAuthenticationForm(forms.Form):
    """
    Custom authentication form using email instead of username.
    """

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput(attrs={"placeholder": "••••••••"})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,  # Django uses username field internally
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid email or password.",
                    code="invalid_login",
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


# -- Mixins for Portal Separation


class StaffOnlyMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to staff users only.

    Returns 403 if a non-staff user tries to access the view.
    """

    def test_func(self):
        """Check if user is staff."""
        user = self.request.user
        return user.is_authenticated and (user.user_type == UserType.STAFF or user.is_staff)

    def handle_no_permission(self):
        """Raise permission denied for non-staff users."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Access denied. Staff access required.")
        return redirect("accounts:login")


class ClientOnlyMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to client users only.

    Returns 403 if a non-client user tries to access the view.
    """

    def test_func(self):
        """Check if user is client."""
        user = self.request.user
        return user.is_authenticated and user.user_type == UserType.CLIENT

    def handle_no_permission(self):
        """Raise permission denied for non-client users."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Access denied. Client access required.")
        return redirect("accounts:login")


# -- Authentication Views


class CustomLoginView(BaseLoginView):
    """
    Custom login view with portal-based redirects.

    Redirects staff users to /admin/ and client users to /dashboard/.
    """

    template_name = "accounts/login.html"
    redirect_field_name = "next"
    form_class = EmailAuthenticationForm
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        """
        Determine redirect URL based on user type.

        Returns:
            str: Redirect URL based on user type
        """
        user = self.request.user

        # Staff users go to admin panel
        if user.user_type == UserType.STAFF or user.is_staff:
            return "/admin/"

        # Client users go to dashboard
        if user.user_type == UserType.CLIENT:
            return "/dashboard/"

        # Default fallback
        return "/dashboard/"

    def form_valid(self, form):
        """
        Handle successful login.

        Logs in the user and redirects to appropriate portal.
        """
        response = super().form_valid(form)
        login(self.request, form.get_user())
        return response


class LogoutView(View):
    """
    Simple logout view.

    Logs out the user and redirects to login page.
    """

    def get(self, request):
        """Handle GET request for logout."""
        logout(request)
        return redirect("accounts:login")

    def post(self, request):
        """Handle POST request for logout."""
        logout(request)
        return redirect("accounts:login")


class LoginRedirectView(View):
    """
    Intermediate redirect view after login.

    Redirects users based on their user type.
    """

    def get(self, request):
        """Handle redirect logic."""
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        user = request.user

        # Staff users go to admin panel
        if user.user_type == UserType.STAFF or user.is_staff:
            return redirect("/admin/")

        # Client users go to dashboard
        if user.user_type == UserType.CLIENT:
            return redirect("wallet:dashboard")

        return redirect("wallet:dashboard")


class ClientRegistrationView(CreateView):
    """
    Client registration view.

    Allows new users to create a client account.
    """

    model = CustomUser
    form_class = ClientRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        """Handle successful registration."""
        user = form.save()

        # Log in the user after registration
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Redirect to dashboard
        return redirect("wallet:dashboard")

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Account"
        return context
