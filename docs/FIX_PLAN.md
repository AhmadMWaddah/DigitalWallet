# Digital Wallet — Fix & Upgrade Plan

**Created**: September 2026  
**Status**: EXECUTED (Sept 2026) — Phases 1–4 committed items done, plus
product features 4.7 (QR payments), 4.8 (transfer fees), 4.4 (KYC foundation).
Remaining future: 4.5 virtual cards, 4.6 multi-currency. 3.2 skipped (django-htmx
unused — HTMX is CDN-only).
**Branch naming**: `fix/*` or `feat/*` per task

---

## Phase 1: Critical Fixes + Theme (Priority: NOW)

### 1.1 Staff Review JSON Bug
**File**: `operations/views.py`  
**Problem**: `ReviewTransactionView.post()` falls back to `JsonResponse` when HTMX header not detected → raw JSON on screen.  
**Fix**:  
- Check `request.headers.get("HX-Request") == "true"` explicitly
- Add fallback HTML redirect for non-HTMX requests
- Same issue in `FreezeWalletView`, `UnfreezeWalletView`

**Before**:
```python
if request.headers.get("HX-Request"):
    ...
return JsonResponse(...)
```

**After**:
```python
if request.headers.get("HX-Request") == "true":
    html = render_to_string("operations/partials/transaction_row.html", ...)
    return HttpResponse(html)
# Non-HTMX fallback: redirect with message
messages.success(request, result["message"])
return redirect("operations:staff_dashboard")
```

### 1.2 BalanceCardView Returns Wrong Response Type
**File**: `wallet/views.py:151`  
**Problem**: `return JsonResponse({"html": html})` — HTMX expects raw HTML.  
**Fix**: `return HttpResponse(html)`

### 1.3 Light Theme Default
**File**: `static/css/base_variables.css`  
**Problem**: Dark theme (black forest) is default — 85% dark surface, eye strain, unprofessional.  
**Fix**:  
- Uncomment light mode (lines 48-62) as default
- Swap dark to `[data-theme="dark"]` or `@media (prefers-color-scheme: dark)`
- Update gradient backgrounds
- Update glassmorphism variables
- Fix hardcoded colors in `staff_dashboard.css`, `dashboard.css`, `navigation.css`

**Before**:
```css
:root {
    --bg-primary: var(--black-forest);  /* dark */
}
```

**After**:
```css
:root {
    --bg-primary: var(--cornsilk);  /* light */
    --bg-secondary: #ffffff;
    --bg-tertiary: #f5f5f0;
    --text-primary: var(--black-forest);
}
[data-theme="dark"] {
    --bg-primary: var(--black-forest);
    --bg-secondary: #1a2410;
    --text-primary: var(--cornsilk);
}
```

### 1.4 Dev Docker Compose
**File**: `docker-compose.dev.yml` (new)  
**Purpose**: Local dev with hot reload, SQLite, no Redis required  
**Contents**:
```yaml
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000 --settings=core.settings.dev
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.dev
```

### 1.5 Health Endpoint
**File**: `core/urls.py` + `core/views.py` (new)  
**Add**: `/health/` → `{"status": "healthy", "db": "ok", "cache": "ok"}`  
**Check**: Database connectivity, cache connectivity  
**Return**: 200 if healthy, 503 if not

---

## Phase 2: CI/CD Pipeline

### 2.0 Security & Rate Limiting
**Files**: `core/settings/base.py`, `wallet/views.py`, `accounts/views.py`  
**Already Done**: ACID transactions (`@transaction.atomic`), `SELECT FOR UPDATE`, F() expressions, Decimal types, idempotency via `reference_id` UNIQUE.  
**Missing**: Rate limiting on sensitive endpoints.  
**Fix**:  
- Add `django-ratelimit==6.1.*` to requirements
- Rate limit login: `@ratelimit(key="ip", rate="5/m", method="POST")` → 5 attempts/min per IP
- Rate limit transfer/withdraw: `@ratelimit(key="user", rate="10/m", method="POST")` → 10 per user/min
- Rate limit password reset: `@ratelimit(key="ip", rate="3/m", method="POST")`
- Add `SECURITY.md` documenting security measures

### 2.1 Test Settings
**File**: `core/settings/test.py` (new)  
**Add**:
```python
from .base import *

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
```

### 2.2 Linting & Formatting
**Files**: `pyproject.toml`, `requirements-dev.txt`  
**Add to requirements**:
```
ruff==0.6.*
black==24.8.*
mypy==1.11.*
django-stubs==5.1.*
pytest==8.3.*
pytest-django==4.9.*
coverage==7.9.*
```

**pyproject.toml**:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP", "SIM"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.mypy]
python_version = "3.12"
plugins = ["mypy_django_plugin.main"]
strict = true

[tool.django-stubs]
django_settings_module = "core.settings.dev"
```

### 2.3 GitHub Actions CI
**File**: `.github/workflows/ci.yml` (new)  
**Steps**:
1. Checkout
2. Setup Python 3.12
3. Install uv
4. Install deps from lock file
5. Run `ruff check`
6. Run `black --check`
7. Run `mypy`
8. Run `pytest` with `--settings=core.settings.test`
9. Run `coverage report`

### 2.4 Security Scanning in CI
**File**: `.github/workflows/ci.yml` (add step)  
**Purpose**: Catch vulnerabilities before merge  
**Steps**:
- `pip-audit` — scan Python deps for known CVEs
- `ruff check --select S` — security-specific lint rules (hardcoded secrets, dangerous patterns)
- Bandit scan — `bandit -r . -c pyproject.toml` for common security issues

### 2.5 Architecture Diagram
**File**: `docs/ARCHITECTURE.md` (update existing)  
**Add**: Mermaid.js diagram showing:
```
Client Request → Auth Middleware → Django Views → Services Layer → Database
                                    ↓
                              HTMX Partials → Browser
                                    ↓
                              Celery Worker → Redis → PDF/Email
```
**Include**: Auth flow, transaction processing flow, fraud detection flow, storage layer  
**Purpose**: Visual system blueprint for onboarding + README link

### 2.6 Edge Case Tests
**File**: `wallet/tests/test_edge_cases.py` (new)  
**Test cases**:
- Concurrent transfers (simulate race condition)
- Transfer to self (should fail)
- Negative amounts (should fail)
- Zero amount (should fail)
- Frozen wallet operations (should fail)
- Insufficient funds (should fail)
- Duplicate reference_id (should fail — idempotency)
- Ledger balance consistency (balance == sum of completed transactions)

---

## Phase 3: Dependency Modernization

### 3.1 Migrate to uv
**Steps**:
```bash
uv venv .venv --python 3.12
uv pip install -r requirements.txt
uv pip compile requirements.txt -o requirements.lock
# Commit requirements.lock
```

**Update**:
- `.gitignore`: add `.venv/` (if not present)
- `AGENTS.md`: update activation command
- CI workflow: use `uv sync` instead of `pip install`

### 3.2 Add Missing Dev Dependencies — NOT NEEDED (skipped)
**File**: `requirements-dev.txt` (already exists, complete without django-htmx)  
**Why skipped**: the project uses HTMX via CDN `<script>` tag in the base template.
Zero `import django_htmx` anywhere; views read `request.headers.get("HX-Request")`
directly. The `django-htmx` pip package (middleware + `HtmxResponse` helpers) would
be dead weight — nothing consumes it.
```
-r requirements.txt
ruff==0.6.*
black==24.8.*
mypy==1.11.*
django-stubs==5.1.*
pytest==8.3.*
pytest-django==4.9.*
coverage==7.9.*
```

---

## Phase 4: Architecture Improvements

### 4.1 Structured JSON Logging
**File**: `core/settings/base.py` → `LOGGING`  
**Change**: Add JSON formatter, stdout handler  
**Output**: Each log line as JSON → collectible by any agent (Loki, CloudWatch, etc.)

### 4.2 API Layer (Committed — DRF)
**Purpose**: REST endpoints for mobile/SPA + machine consumers, reusing `wallet/services.py` as single source of truth. Web templates + HTMX stay untouched; API is additive under `/api/v1/`.
**Stack**: `djangorestframework==3.15.*`, `drf-spectacular==0.28.*`
**Reuse**: `deposit_funds`, `withdraw_funds`, `transfer_funds` (`wallet/services.py`), `Wallet` / `Transaction` / `TransactionStatus` (`wallet/models.py`), `ClientOnlyMixin` semantics (client-own-wallet-only) ported to DRF permissions.

**4.2.1 Dependencies**
**File**: `requirements.txt`
**Add**:
```
djangorestframework==3.15.*
drf-spectacular==0.28.*
```

**4.2.2 Settings**
**File**: `core/settings/base.py` → `INSTALLED_APPS` += `"rest_framework"`, `"drf_spectacular"`
**Add**:
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "100/min",
        "transfer": "10/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Digital Wallet API",
    "VERSION": "1.0.0",
}
```
**Why SessionAuth first**: reuses existing login + CSRF, no JWT infra yet (YAGNI). Token auth added only when mobile client lands.

**4.2.3 Serializers**
**File**: `wallet/serializers.py` (new)
- `WalletSerializer`: `id`, `balance` (Decimal as string, `coerce_to_string=True`, no floats), `is_frozen`, `updated_at` — read-only.
- `TransactionSerializer`: `id`, `amount`, `type`, `status`, `description`, `reference_id`, `created_at`, `counterparty_wallet` (id only) — read-only.
- `DepositInputSerializer`: `amount` (Decimal, `min_value=0.01`, `max_digits=12`, `decimal_places=2`), `description` (optional, `max_length=500`).
- `WithdrawInputSerializer`: same as deposit.
- `TransferInputSerializer`: `recipient_email` (EmailField), `amount`, `description`. Recipient lookup mirrors `TransferView.post()` via `ClientProfile.objects.select_related("wallet")`.
- Map service exceptions to `serializers.ValidationError`: `InsufficientFundsError`, `FrozenWalletError`, `SelfTransferError`, `InvalidAmountError`, `DuplicateTransactionError` → HTTP 400 with `{"detail": ...}`.

**4.2.4 Views**
**File**: `wallet/api.py` (new)
- `WalletDetailView (RetrieveAPIView)`: `GET /api/v1/wallet/` → own wallet only (`request.user.client_profile.wallet`, 404 if none). Permission: `IsAuthenticated` + client-only check (mirror `ClientOnlyMixin.test_func`: `user_type == CLIENT`).
- `TransactionListView (ListAPIView)`: `GET /api/v1/transactions/` → `wallet.transactions.order_by("-created_at")`, paginated. Filter: `?type=DEPOSIT|WITHDRAWAL|TRANSFER&status=COMPLETED|...` (mirrors `TransactionListView.get_queryset` client branch only — no staff cross-user leak).
- `DepositAPIView (CreateAPIView)`: `POST /api/v1/deposit/` → calls `deposit_funds(wallet, amount, description, reference_id=f"DEP-{wallet.id}-{uuid4hex}")`. Throttle scope: `transfer`.
- `WithdrawAPIView (CreateAPIView)`: `POST /api/v1/withdraw/` → calls `withdraw_funds(...)`, same reference pattern `WDR-...`.
- `TransferAPIView (CreateAPIView)`: `POST /api/v1/transfer/` → calls `transfer_funds(sender, receiver, ...)`, reference `TRF-{sender}-{receiver}-{uuid4hex}`.
- All write views return `TransactionSerializer` with HTTP 201 on success.

**4.2.5 URLs**
**File**: `wallet/api_urls.py` (new) + `core/urls.py` (modify: `path("api/v1/", include("wallet.api_urls"))`)
```python
# wallet/api_urls.py
app_name = "wallet_api"
urlpatterns = [
    path("wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("deposit/", DepositAPIView.as_view(), name="deposit"),
    path("withdraw/", WithdrawAPIView.as_view(), name="withdraw"),
    path("transfer/", TransferAPIView.as_view(), name="transfer"),
]
```

**4.2.6 Tests**
**File**: `wallet/tests/test_api.py` (new)
- Auth required → 403/401 unauthenticated.
- Client A cannot see Client B wallet/transactions (ownership).
- Deposit/withdraw/transfer happy path → 201 + balance delta correct (Decimal).
- Negative/zero amount → 400. Transfer to self → 400. Frozen wallet → 400. Insufficient funds → 400.
- Idempotency: re-POST same `reference_id` (pass explicit `reference_id` field, optional) → 400 duplicate.

### 4.3 OpenAPI Documentation
**File**: `core/urls.py` + `core/settings/base.py` (SPECTACULAR_SETTINGS above)
**Stack**: `drf-spectacular==0.28.*` (already in 4.2.1)
**Add**:
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
```
**Purpose**: Interactive Swagger UI for frontend/mobile consumers. Schema must render without auth (public docs, endpoints still authed).

### 4.4 KYC/AML Foundation (Future)
**File**: `accounts/models.py`, `accounts/views.py`  
**Purpose**: KYC verification is mandatory for financial apps  
**Scope**:
- Add `kyc_status` field to `ClientProfile` (PENDING / VERIFIED / REJECTED)
- Add `kyc_verified_at`, `kyc_rejection_reason` fields
- Add verification document upload endpoint
- Staff approval flow for KYC (similar to fraud review)
- Integrate with free tier of Sumsub or Persona for identity verification
- Block transactions above threshold until KYC verified

### 4.5 Virtual Cards (Future Product Feature)
**File**: `wallet/models.py` (new model)  
**Purpose**: Competitive differentiator — dynamic single-use cards for secure online shopping  
**Models**:
- `VirtualCard`: card_number (encrypted), expiry, spend_limit, merchant_lock, is_active
- `CardTransaction`: linked to VirtualCard + Transaction  
**Use Case**: Generate temporary card for one-time purchase, auto-deactivate after use

### 4.6 Multi-Currency Support (Future Product Feature)
**File**: `wallet/models.py`, `wallet/services.py`  
**Purpose**: Cross-border payments differentiation  
**Add**:
- `currency` field on Wallet (default: USD)
- `exchange_rate` table with real-time rates (via free API like exchangerate-api.com)
- FX conversion logic in transfer service
- Revenue: 0.5%–1% margin on cross-currency transfers

### 4.7 QR Code Payments (Future Product Feature)
**File**: `wallet/views.py`, templates  
**Purpose**: Merchant scan-to-pay functionality  
**Add**:
- Generate QR code per user/wallet (using `qrcode` library)
- Merchant endpoint: scan → verify → transfer
- Transaction metadata: `"payment_method": "qr_code"`

### 4.8 Monetization Hooks (Business Logic)
**File**: `wallet/services.py`  
**Purpose**: Revenue generation for commercial viability  
**Add**:
- Transaction fee calculation: `fee = amount * 0.015 + 0.20` (1.5% + $0.20)
- Instant cash-out fee: 1–2% for instant payouts vs free standard (2-3 days)
- Subscription tier check: premium users get 0% fee, higher limits
- Fee ledger entry for each transaction

---

## Execution Order

| Task | Depends On | Est. Time |
|------|-----------|-----------|
| 1.1 Staff review JSON fix | — | 30 min |
| 1.2 BalanceCardView fix | — | 15 min |
| 1.3 Light theme default | — | 2 hrs |
| 1.4 Dev docker-compose | — | 30 min |
| 1.5 Health endpoint | — | 30 min |
| 2.0 Security & rate limiting | — | 1 hr |
| 2.1 test.py settings | — | 30 min |
| 2.2 Linting setup | — | 1 hr |
| 2.3 GitHub Actions CI | 2.1, 2.2 | 1 hr |
| 2.4 Security scanning in CI | 2.3 | 30 min |
| 2.5 Architecture diagram | — | 1 hr |
| 2.6 Edge case tests | 2.1 | 2 hrs |
| 3.1 uv migration | — | 1 hr |
| 3.2 Dev requirements | — | 15 min |
| 4.1 JSON logging | — | 1 hr |
| 4.2.1 DRF deps + settings | 2.2 | 30 min |
| 4.2.3 Serializers (`wallet/serializers.py`) | 4.2.1 | 1 hr |
| 4.2.4 Views (`wallet/api.py`) | 4.2.3 | 1 hr 30 min |
| 4.2.5 URLs (`wallet/api_urls.py` + `core/urls.py`) | 4.2.4 | 30 min |
| 4.2.6 API tests (`wallet/tests/test_api.py`) | 4.2.5 | 1 hr |
| 4.3 OpenAPI docs (`/api/schema/`, `/api/docs/`) | 4.2.5 | 30 min |
| **4.4–4.8** | **Future** | **—** |

**Total (Phase 1–4)**: ~17 hours  
**Phase 1 + 2 (Critical)**: ~8 hours  
**Phase 3 + 4 (Modernization)**: ~9 hours

**Recommended**: Phase 1 + 2 in one sprint, Phase 3 + 4 in next sprint.  
**Future (4.4–4.8)**: Product roadmap items — implement when commercializing.

---

## Verification Checklist

After each task:

- [ ] `python manage.py check --settings=core.settings.dev`
- [ ] `python manage.py test --settings=core.settings.test`
- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] Manual test: staff approve/reject transaction
- [ ] Manual test: login as testuser1@example.com
- [ ] Manual test: deposit/withdraw/transfer flow
- [ ] Docker build succeeds
- [ ] Rate limit test: 6 rapid login attempts → 5th blocked
- [ ] Edge case: transfer to self → error message
- [ ] Edge case: frozen wallet → operation blocked
- [ ] API: `GET /api/v1/wallet/` authed → 200 own balance; unauthed → 403
- [ ] API: `POST /api/v1/transfer/` to self → 400; frozen wallet → 400
- [ ] API: `/api/schema/` renders; `/api/docs/` Swagger loads

## What's Already Done (No Action Needed)

The review praised several things we already have:

| Feature | Status | Location |
|---------|--------|----------|
| ACID transactions | ✅ Done | `wallet/services.py` — `@transaction.atomic` |
| Pessimistic locking | ✅ Done | `SELECT FOR UPDATE` on wallet rows |
| Race condition prevention | ✅ Done | F() expressions + deadlock prevention (lock order by ID) |
| Idempotency | ✅ Done | `reference_id` UNIQUE constraint + `DuplicateTransactionError` |
| Decimal precision | ✅ Done | `Decimal` types throughout, no floats |
| Immutable ledger | ✅ Done | `Transaction` model — append-only, status field tracks lifecycle |
| Audit trail | ✅ Done | `Transaction.metadata` stores review_by, reviewed_at, flag_reason |
