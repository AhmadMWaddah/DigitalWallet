# Security Measures — Digital Wallet

Concrete controls in this repo, with file pointers. No aspirational items.

## Rate Limiting (`django-ratelimit==4.1.*`)

| Endpoint | View | Key | Rate | Why |
|----------|------|-----|------|-----|
| `accounts:login` | `accounts/views.py::CustomLoginView` | ip | 5/min POST | brute-force |
| `wallet:transfer` | `wallet/views.py::TransferView` | user | 10/min POST | fund-drain automation |
| `wallet:qr_pay` | `wallet/views.py::QRPayView` | user | 10/min POST | fund-drain automation |
| `wallet:withdraw` | `wallet/views.py::WithdrawView` | user | 10/min POST | fund-drain automation |
| `accounts:password_reset_client` | `accounts/views_reset.py::ClientPasswordResetView` | ip | 3/min POST | reset-email spam |

Exceeded limits return HTTP 403 (`block=True`). Tests disable limits
globally (`conftest.py::pytest_configure` sets `RATELIMIT_ENABLE=False`)
and re-enable per case (`accounts/tests/test_rate_limits.py`,
`wallet/tests/test_rate_limits.py`).

## Money Safety (`wallet/services.py`)

- `@transaction.atomic` on `deposit_funds`, `withdraw_funds`, `transfer_funds`.
- `SELECT FOR UPDATE` row locks + `F()` balance updates (no lost updates).
- `reference_id` UNIQUE → idempotent retries raise `DuplicateTransactionError`.
- `Decimal` everywhere; amounts must be `> 0` (`InvalidAmountError`).
- Frozen wallets rejected (`FrozenWalletError`); self-transfers rejected.
- Transfers above $10,000 require `VERIFIED` KYC (`KYCRequiredError`,
  threshold `KYC_REQUIRED_ABOVE` in settings).
- QR payloads are `TimestampSigner`-signed (`wallet/qr.py`); tampered codes
  fail closed before any money moves.
- Ledger append-only; fraud review via `process_fraud_review` only.

## Auth & Sessions (`core/settings/base.py`, `accounts/`)

- Custom user model, email login (`accounts/views.py::EmailAuthenticationForm`).
- Portal separation: `StaffOnlyMixin` / `ClientOnlyMixin` → 403 + custom
  `custom_permission_denied` page with smart redirect.
- `SESSION_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE=Lax`, expire on browser close.
- `CSRF_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE=Lax`.
- Django password validators (similarity, length, common, numeric).
- Password reset never reveals account existence; staff-only reset excluded
  (`ClientPasswordResetView` serves CLIENT users only).

## Fraud (`operations/`, `wallet/services.py`)

- `FraudEngine` flags transfers (e.g. large amounts) → `FLAGGED` status.
- Staff approve/reject via `ReviewTransactionView`; reviewer + timestamp in
  `Transaction.metadata`. Freeze/unfreeze wallet controls in
  `FreezeWalletView` / `UnfreezeWalletView`.

## Known Gaps (not yet done)

- API v1 (`/api/v1/`, `wallet/api.py`) uses session auth + `IsClientUser`
  (own-wallet-only) + `transfer` throttle scope; no JWT yet — add token
  auth when a mobile client lands.
- `ALLOWED_HOSTS` / `SECRET_KEY` come from `.env` — verify in prod deploy.
- Redis has no password in `docker-compose.yml` — fine for local, not for prod.
