"""
Wallet app forms.

Forms for deposit, withdrawal, transfer, and QR scan-to-pay operations.
"""

from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.signing import BadSignature

from accounts.models import ClientProfile

from .models import Wallet
from .qr import parse_qr_payload

CustomUser = get_user_model()


class DepositForm(forms.Form):
    """
    Form for depositing funds into a wallet.
    """

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0.01",
            }
        ),
        help_text="Minimum deposit: $0.01",
    )

    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Description (optional)",
            }
        ),
    )

    def clean_amount(self):
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")
        if amount <= Decimal("0.00"):
            raise ValidationError("Amount must be greater than zero.")
        return amount


class WithdrawForm(forms.Form):
    """
    Form for withdrawing funds from a wallet.
    """

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0.01",
            }
        ),
        help_text="Minimum withdrawal: $0.01",
    )

    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Description (optional)",
            }
        ),
    )

    def clean_amount(self):
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")
        if amount <= Decimal("0.00"):
            raise ValidationError("Amount must be greater than zero.")
        return amount


class TransferForm(forms.Form):
    """
    Form for transferring funds between wallets.
    """

    recipient_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "recipient@example.com",
                "type": "email",
            }
        ),
        help_text="Enter the recipient's email address",
    )

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0.01",
            }
        ),
        help_text="Minimum transfer: $0.01",
    )

    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Description (optional)",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with sender wallet for validation."""
        self.sender_wallet = kwargs.pop("sender_wallet", None)
        super().__init__(*args, **kwargs)

    def clean_recipient_email(self):
        """Validate recipient email exists and is not sender."""
        email = self.cleaned_data.get("recipient_email")

        if not self.sender_wallet:
            raise ValidationError("Sender wallet not provided.")

        # Check if recipient exists
        try:
            recipient_profile = ClientProfile.objects.select_related("user").get(user__email=email)

            # Check if recipient is sender
            if recipient_profile.user == self.sender_wallet.client_profile.user:
                raise ValidationError("Cannot transfer to yourself.")

            # Check if recipient has a wallet
            if not hasattr(recipient_profile, "wallet"):
                raise ValidationError("Recipient does not have a wallet.")

        except ClientProfile.DoesNotExist:
            raise ValidationError("No user found with this email address.")

        return email

    def clean_amount(self):
        """Validate amount is positive and within sender's balance."""
        amount = self.cleaned_data.get("amount")

        if amount <= Decimal("0.00"):
            raise ValidationError("Amount must be greater than zero.")

        if self.sender_wallet and amount > self.sender_wallet.balance:
            raise ValidationError(
                f"Insufficient funds. Your balance: ${self.sender_wallet.balance:.2f}"
            )

        return amount


class QRPayForm(forms.Form):
    """
    Form for paying by pasted/scanned QR code.

    The code resolves to the receiver wallet (signature-verified);
    amount rules mirror TransferForm.
    """

    code = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "placeholder": "Paste the scanned QR code here",
                "rows": 3,
            }
        ),
        help_text="Scan the recipient's QR code, then paste it here",
    )

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0.01",
            }
        ),
        help_text="Minimum payment: $0.01",
    )

    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Description (optional)",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with sender wallet for validation."""
        self.sender_wallet = kwargs.pop("sender_wallet", None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        """Verify QR signature and resolve the receiver wallet."""
        code = self.cleaned_data.get("code")

        if not self.sender_wallet:
            raise ValidationError("Sender wallet not provided.")

        try:
            wallet_id = parse_qr_payload(code)
        except (BadSignature, ValueError, TypeError) as exc:
            raise ValidationError("Invalid or tampered QR code.") from exc

        try:
            receiver_wallet = Wallet.objects.select_related("client_profile__user").get(
                id=wallet_id
            )
        except Wallet.DoesNotExist as exc:
            raise ValidationError("QR code points to an unknown wallet.") from exc

        if receiver_wallet.id == self.sender_wallet.id:
            raise ValidationError("Cannot pay yourself.")

        return receiver_wallet

    def clean_amount(self):
        """Validate amount is positive and within sender's balance."""
        amount = self.cleaned_data.get("amount")

        if amount <= Decimal("0.00"):
            raise ValidationError("Amount must be greater than zero.")

        if self.sender_wallet and amount > self.sender_wallet.balance:
            raise ValidationError(
                f"Insufficient funds. Your balance: ${self.sender_wallet.balance:.2f}"
            )

        return amount
