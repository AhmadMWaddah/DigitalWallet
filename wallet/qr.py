"""
QR code payloads and PNG rendering for scan-to-pay.

Payloads are TimestampSigner-signed wallet IDs (salt "wallet-qr"),
so forged or tampered codes fail verification instead of pointing
at an attacker's wallet.
"""

import io

import qrcode
from django.core.signing import BadSignature, TimestampSigner

QR_PREFIX = "DW1:"
QR_SALT = "wallet-qr"

_signer = TimestampSigner(salt=QR_SALT)


def build_qr_payload(wallet_id):
    """Build a signed QR payload for the given wallet ID."""
    return f"{QR_PREFIX}{_signer.sign(str(wallet_id))}"


def parse_qr_payload(code):
    """
    Verify a QR payload and return the wallet ID it points to.

    Raises BadSignature for foreign/tampered codes, ValueError for
    non-integer wallet IDs.
    """
    code = (code or "").strip()
    if not code.startswith(QR_PREFIX):
        raise BadSignature("Not a wallet QR code.")
    return int(_signer.unsign(code[len(QR_PREFIX) :]))


def qr_png_bytes(payload):
    """Render a QR payload as PNG bytes (never stored, generated per request)."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
