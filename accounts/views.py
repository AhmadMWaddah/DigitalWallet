"""
Accounts app views.

Handles user authentication with portal-based redirects.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.generic import CreateView, TemplateView, View

from .forms import ClientPasswordChangeForm, ClientRegistrationForm
from .models import UserType

CustomUser = get_user_model()


def _get_client_ip(request):
    """Extract the best available client IP address from request metadata."""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "Unavailable")


def _get_browser_name(user_agent):
    """Return a readable browser name from the user agent string."""
    user_agent = (user_agent or "").lower()

    browser_signatures = (
        ("edg/", "Microsoft Edge"),
        ("opr/", "Opera"),
        ("chrome/", "Google Chrome"),
        ("firefox/", "Mozilla Firefox"),
        ("safari/", "Safari"),
        ("trident/", "Internet Explorer"),
        ("msie ", "Internet Explorer"),
    )

    for signature, browser_name in browser_signatures:
        if signature in user_agent:
            return browser_name

    return "Unknown Browser"


def _get_device_name(user_agent):
    """Return a readable device category from the user agent string."""
    user_agent = (user_agent or "").lower()

    if any(token in user_agent for token in ("ipad", "tablet")):
        return "Tablet"
    if any(token in user_agent for token in ("iphone", "android", "mobile")):
        return "Mobile Device"
    if user_agent:
        return "Desktop Browser"
    return "Unknown Device"


def _build_session_snapshot(request, logged_in_at=None):
    """Build a normalized session snapshot for display on the security page."""
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    return {
        "logged_in_at": (logged_in_at or timezone.now()).isoformat(),
        "ip_address": _get_client_ip(request),
        "browser": _get_browser_name(user_agent),
        "device": _get_device_name(user_agent),
    }


def _normalize_session_snapshot(snapshot):
    """Normalize a session snapshot stored in the session for template rendering."""
    if not snapshot:
        return None

    logged_in_at = snapshot.get("logged_in_at")
    if isinstance(logged_in_at, str):
        snapshot = dict(snapshot)
        snapshot["logged_in_at"] = parse_datetime(logged_in_at)

    return snapshot


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

        # SuperUsers go to Django Admin
        if user.is_superuser:
            return "/admin/"

        # Staff users go to Staff Dashboard (NOT admin)
        if user.user_type == UserType.STAFF or user.is_staff:
            return "/staff/dashboard/"

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
        previous_session_snapshot = self.request.session.get("current_session_snapshot")
        previous_login_at = form.get_user().last_login

        response = super().form_valid(form)

        if previous_session_snapshot:
            self.request.session["previous_session_snapshot"] = previous_session_snapshot
        elif previous_login_at:
            self.request.session["previous_session_snapshot"] = {
                "logged_in_at": previous_login_at.isoformat(),
                "ip_address": "Unavailable",
                "browser": "Unavailable",
                "device": "Previous Session",
            }

        self.request.session["current_session_snapshot"] = _build_session_snapshot(
            self.request,
            logged_in_at=timezone.now(),
        )
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

    Redirects users based on their user type:
    - SuperUser: /admin/ (Django Admin)
    - Staff: /staff/dashboard/ (Staff operations)
    - Client: /dashboard/ (Client wallet)
    - Anonymous: /accounts/login/
    """

    def get(self, request):
        """Handle redirect logic."""
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        user = request.user

        # SuperUsers go to Django Admin (full system control)
        if user.is_superuser:
            return redirect("/admin/")

        # Staff users go to Staff Dashboard (business operations)
        if user.user_type == UserType.STAFF or user.is_staff:
            return redirect("operations:staff_dashboard")

        # Client users go to Wallet Dashboard
        if user.user_type == UserType.CLIENT:
            return redirect("wallet:dashboard")

        # Fallback
        return redirect("wallet:dashboard")

    @staticmethod
    def get_redirect_url(user):
        """
        Get redirect URL for a user (static helper for 403 page).

        Args:
            user: User instance

        Returns:
            str: Redirect URL based on user type
        """
        if not user or not user.is_authenticated:
            return "accounts:login"

        if user.is_superuser:
            return "/admin/"

        if user.user_type == UserType.STAFF or user.is_staff:
            return "operations:staff_dashboard"

        if user.user_type == UserType.CLIENT:
            return "wallet:dashboard"

        return "wallet:dashboard"


def custom_permission_denied(request, exception=None):
    """
    Custom 403 error handler with smart redirect.

    Args:
        request: HTTP request
        exception: Exception object (optional)

    Returns:
        HttpResponse: Rendered 403 template with context
    """
    from django.urls import reverse

    # Get smart redirect URL based on user type (resolve to actual URL)
    redirect_url_name = LoginRedirectView.get_redirect_url(request.user)

    # Resolve URL name to actual path
    try:
        redirect_url = reverse(redirect_url_name)
    except NoReverseMatch:
        redirect_url = "/dashboard/"  # Fallback

    # Custom message based on user type
    message = None
    if request.user.is_authenticated:
        if request.user.user_type == UserType.STAFF or request.user.is_staff:
            message = "Staff users should access the Staff Dashboard, not the Client Portal."
        elif request.user.is_superuser:
            message = "Administrators should access Django Admin for system management."
        else:
            message = "This area is restricted to authorized users only."

    context = {
        "exception": message or exception,
        "redirect_url": redirect_url,
        "user": request.user,
    }

    return render(request, "403.html", context, status=403)


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


class ProfileView(LoginRequiredMixin, ClientOnlyMixin, TemplateView):
    """
    Client profile view.

    Displays and allows editing of client profile information.
    """

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        """Add profile data to context."""
        context = super().get_context_data(**kwargs)
        client_profile = self.request.user.client_profile
        context["profile"] = client_profile
        context["page_title"] = "My Profile"
        return context


class SecurityView(LoginRequiredMixin, ClientOnlyMixin, PasswordChangeView):
    """
    Client security settings view.

    Displays security settings and handles password change.
    """

    template_name = "accounts/security.html"
    form_class = ClientPasswordChangeForm
    success_url = reverse_lazy("accounts:security")

    def form_valid(self, form):
        """Persist the password change and show a success message."""
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been updated successfully.")
        return response

    def form_invalid(self, form):
        """Show a generic error message when validation fails."""
        messages.error(self.request, "Please correct the password errors below.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add security data to context."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Security Settings"
        context["current_session"] = self.get_current_session()
        context["previous_session"] = self.get_previous_session()
        return context

    def get_current_session(self):
        """Get current session information for display."""
        snapshot = self.request.session.get("current_session_snapshot")
        if snapshot:
            snapshot = dict(snapshot)
            snapshot.update(
                _build_session_snapshot(
                    self.request, logged_in_at=parse_datetime(snapshot["logged_in_at"])
                )
            )
            return _normalize_session_snapshot(snapshot)

        return _normalize_session_snapshot(
            _build_session_snapshot(
                self.request, logged_in_at=self.request.user.last_login or timezone.now()
            )
        )

    def get_previous_session(self):
        """Get previous session information for display."""
        return _normalize_session_snapshot(self.request.session.get("previous_session_snapshot"))
