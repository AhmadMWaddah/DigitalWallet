# Fintech Digital Wallet Dashboard - Professional Project Plan

## How to Use This Plan

- **Work sequentially** through each phase — do not skip ahead.
- **Testing Mandate:** Every feature must include corresponding `pytest` test cases. Run tests before every commit.
- **Git Mandate:** Use `scripts/git-phase-commit.sh` and `scripts/git-phase-merge.sh` for all phase work.
- **Views Architecture:** **CBVs** for structural views, **FBVs** for lightweight HTMX actions.
- **Frontend Architecture:** CSS in `static/css/modules/`, JS in `static/js/modules/`, HTML snippets in `templates/components/`.
- **Zero-Error Policy:** Never confirm completion without manual or automated verification.

## Code Commenting & Documentation Standards

- **Docstrings:** Use `"""Docstring content"""` for classes and complex functions only.
- **Logic Comments:** Explain **why**, not **what**. Use `# Comment content`.
- **Section Headers:** Use clean, scannable headers:
  - Python/Bash: `# -- Header Section Name`
  - HTML: `<!-- --#-- Header Section Name -->`
  - CSS/JS: `/* --#-- Header Section Name */`

---

## Project Overview

Build a secure, production-ready **Digital Wallet Dashboard** with dual-portal access, atomic financial operations, and real-time HTMX interactivity.

### Key Features

- **Dual-Portal System:** Staff (Admin/Labor) vs Client (User) environments
- **Atomic Transactions:** Secure deposit, withdrawal, transfer with rollback protection
- **HTMX Interactivity:** Real-time balance updates, infinite-scroll history, no page reloads
- **Fraud Detection:** Automated flagging of suspicious transfers (> $10K, > 5/hour)
- **Async Processing:** Celery + Redis for PDF generation with HTMX progress bars
- **Analytics Dashboard:** Spending visualization with Chart.js

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, Django 5.2 (LTS) |
| **Database** | PostgreSQL (SupaBase for production) |
| **Frontend** | HTMX, Custom Modular CSS, Vanilla JS |
| **Async** | Celery + Redis |
| **PDF** | ReportLab |
| **Testing** | Pytest, pytest-django |
| **Deployment** | Render, Gunicorn, WhiteNoise |

---

## Phase Structure Overview

| Phase | Name | Branch | Original Phases |
|-------|------|--------|-----------------|
| **1** | Foundation & Automation | `phase-setup-automation` | 1, 2, 3 |
| **2** | Identity & Access Management | `phase-identity-auth` | 4, 5, 6 |
| **3** | Frontend Foundation | `phase-frontend-core` | 7, 8 |
| **4** | Wallet Engine | `phase-wallet-engine` | 9, 10 |
| **5** | HTMX Dashboard | `phase-dashboard-htmx` | 11, 12 |
| **6** | Async & Reporting | `phase-async-reporting` | 13, 14 |
| **7** | Staff & Analytics | `phase-staff-analytics` | 15, 16 |
| **8** | Performance & Deployment | `phase-qa-deployment` | 17, 18 |

---

## Phase 1: Foundation & Automation

**Goal:** Initialize project with professional settings structure, Git workflow, pre-commit quality hooks, and automation scripts.

**Concepts:** Virtual environments, Django project structure, settings modularization, Git automation, Code Linting.

### Tasks

1. Create virtual environment `.env_digital_wallet` with Python 3.12
2. Install dependencies: `django==5.2.*`, `django-environ`, `psycopg2-binary`, `pre-commit`, `black`, `flake8`, `isort`
3. Start Django project `core` in current directory
4. Create settings package: `core/settings/` with `base.py`, `dev.py`, `prod.py`
5. Configure `django-environ` for environment-based settings
6. Initialize Git: `git init`, `.gitignore`, `.env.example`
7. Create GitHub repository: `gh repo create DigitalWallet --public`
8. Create automation scripts:
   - `scripts/git-phase-commit.sh` — Phase commits with branch management
   - `scripts/git-phase-merge.sh` — Merge phase to master with cleanup
   - `scripts/setup.sh` — One-command project setup (Must include `pre-commit install`)
9. Configure pytest with `pytest.ini` and `conftest.py`
10. **Code Quality Setup:** 
    - Create `.pre-commit-config.yaml` with hooks for black, flake8, isort, and trailing-whitespace.
    - Run `pre-commit install` to activate the hooks.
11. Write tests for settings structure
12. Verify: Server runs on port 8500, all tests pass, and `pre-commit` runs on a dummy commit.

### Deliverables

- [ ] Virtual environment `.env_digital_wallet`
- [ ] Django 5.2 project `core`
- [ ] Settings package (base/dev/prod)
- [ ] `.gitignore`, `.env.example`, `.pre-commit-config.yaml`
- [ ] GitHub repository setup
- [ ] Automation scripts in `scripts/`
- [ ] Pytest configuration
- [ ] Quality hooks (Black, Flake8, Isort) active

### Verification

```bash
# Run tests
pytest

# Run server
python manage.py runserver 8500 --settings=core.settings.dev
```

---

## Phase 2: Identity & Access Management

**Goal:** Implement secure email-based authentication with user profiles and portal separation.

**Concepts:** `AbstractBaseUser`, custom managers, Django signals, permission mixins.

### Tasks

1. Create `accounts` app: `python manage.py startapp accounts`
2. Define `CustomUser` model extending `AbstractBaseUser`:
   - Remove `username`, use `email` as unique identifier and `USERNAME_FIELD`
   - Add `user_type` field (choices: `STAFF`, `CLIENT`)
   - Add `is_verified` field for email verification
3. Create `CustomUserManager` for `create_user()` and `create_superuser()`
4. Update `settings/base.py`: `AUTH_USER_MODEL = 'accounts.CustomUser'`
5. Define profile models:
   - `StaffProfile`: `role` (Admin, Labor), `assigned_permissions`
   - `ClientProfile`: `full_name`, `company`, `job_title`, `phone`, `address`, `kyc_verified`
6. Implement `post_save` signals to auto-create profiles based on `user_type`
7. Register signals in `accounts/apps.py`, models in `accounts/admin.py`
8. Implement `CustomLoginView` (CBV) with portal-based redirects:
   - Staff → `/admin/` only
   - Client → `/dashboard/` only
9. Create `StaffOnlyMixin` and `ClientOnlyMixin` for view protection
10. Configure `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, `LOGIN_URL`
11. **Testing:** Write comprehensive tests for:
    - User/superuser creation with email
    - Profile auto-creation on user creation
    - Login redirect logic based on `user_type`
    - Access denial for unauthorized portal access (403/redirect)

### Deliverables

- [ ] `accounts/` app with CustomUser model
- [ ] StaffProfile and ClientProfile models with signals
- [ ] Custom login view with portal separation
- [ ] StaffOnlyMixin and ClientOnlyMixin
- [ ] 15+ pytest tests covering auth layer
- [ ] Admin registration for all models

### Verification

```bash
# Run auth tests
pytest accounts/tests/ -v

# Test login flow manually
python manage.py createsuperuser --settings=core.settings.dev
```

---

## Phase 3: Frontend Foundation

**Goal:** Build responsive UI skeleton with modular static file structure.

**Concepts:** Template inheritance, CSS Grid/Flexbox, HTMX integration, component-based architecture.

### Tasks

1. Create directory structure:
   - `templates/`, `templates/__snippets__/`, `templates/components/`
   - `static/css/modules/`, `static/js/modules/`
2. Create `templates/base.html` with responsive shell:
   - Navbar (logo, user menu, notifications)
   - Sidebar (navigation links, collapsible on mobile)
   - Main content area with proper padding
   - Footer (copyright, links)
3. Create modular CSS files:
   - `layout.css` — Grid system, container, spacing utilities
   - `navigation.css` — Navbar, sidebar, mobile menu
   - `forms.css` — Input styles, buttons, validation states
   - `utilities.css` — Helper classes (text, visibility, flex)
4. Integrate HTMX via CDN in `base.html`
5. Configure `STATICFILES_DIRS` and `TEMPLATES` in `settings/base.py`
6. Create reusable components:
   - `templates/components/balance_card.html` — Wallet balance display
   - `templates/components/transaction_item.html` — Transaction list item
   - `templates/components/alert.html` — Success/error messages
   - `templates/components/modal.html` — Reusable modal dialog
7. Create `templates/__snippets__/` for partial includes:
   - `navbar.html`, `sidebar.html`, `footer.html`
8. Create dummy `DashboardView` to verify all components render correctly
9. **Testing:** Write tests for component rendering and responsive behavior

### Deliverables

- [ ] `base.html` with responsive layout
- [ ] Modular CSS structure (layout, navigation, forms, utilities)
- [ ] HTMX integrated via CDN
- [ ] Reusable components (balance card, transaction item, alert, modal)
- [ ] Navigation snippets (navbar, sidebar, footer)
- [ ] Component rendering tests

### Verification

```bash
# Run frontend tests
pytest --tb=short

# Manual verification
python manage.py runserver 8500 --settings=core.settings.dev
# Visit http://localhost:8500/dashboard/ and test responsiveness
```

---

## Phase 4: Wallet Engine

**Goal:** Define financial data models and implement atomic transaction logic.

**Concepts:** `DecimalField`, ForeignKeys, `transaction.atomic()`, service layer pattern.

### Tasks

1. Create `wallet` app: `python manage.py startapp wallet`
2. Define `Wallet` model:
   - `client_profile` (OneToOne to ClientProfile)
   - `balance` (DecimalField, max_digits=12, decimal_places=2, default=0)
   - `created_at`, `updated_at` (auto_now_add, auto_now)
   - `is_frozen` (BooleanField, default=False)
3. Define `Transaction` model:
   - `wallet` (ForeignKey to Wallet, related_name='transactions')
   - `counterparty_wallet` (ForeignKey to Wallet, null=True for deposits/withdrawals)
   - `amount` (DecimalField, max_digits=12, decimal_places=2)
   - `type` (Choices: DEPOSIT, WITHDRAWAL, TRANSFER)
   - `status` (Choices: PENDING, COMPLETED, FAILED, FLAGGED)
   - `description` (TextField, blank=True)
   - `reference_id` (CharField, unique, for idempotency)
   - `metadata` (JSONField, blank=True, for audit trail)
   - `created_at` (DateTimeField, auto_now_add, indexed)
4. Run migrations: `makemigrations wallet`, `migrate`
5. Create `wallet/services.py` for business logic:
   - `deposit_funds(wallet, amount, description, reference_id)`
   - `withdraw_funds(wallet, amount, description, reference_id)`
   - `transfer_funds(sender_wallet, receiver_wallet, amount, description)`
   - All functions wrapped in `@transaction.atomic()`
   - Implement idempotency checks using `reference_id`
   - Implement insufficient funds validation
   - Implement self-transfer prevention
6. Create `wallet/exceptions.py` for custom errors:
   - `InsufficientFundsError`
   - `SelfTransferError`
   - `DuplicateTransactionError`
   - `FrozenWalletError`
7. **Testing:** Write comprehensive pytest cases:
   - Successful deposit/withdrawal/transfer
   - Insufficient funds (verify no money moved)
   - Self-transfer prevention
   - Atomic rollback on error
   - Idempotency (duplicate reference_id rejection)
   - Frozen wallet operations blocked

### Deliverables

- [ ] Wallet and Transaction models
- [ ] Service layer functions (deposit, withdraw, transfer)
- [ ] Custom exceptions module
- [ ] Database indexes on Transaction.timestamp
- [ ] 20+ pytest tests for financial operations

### Verification

```bash
# Run wallet tests
pytest wallet/tests/ -v

# Test atomic rollback
pytest wallet/tests/test_services.py::test_transfer_atomic_rollback -v
```

---

## Phase 5: HTMX Dashboard

**Goal:** Build dynamic client dashboard with real-time HTMX interactions.

**Concepts:** HTMX `hx-get`, `hx-post`, partial templates, OOB swaps, infinite scroll.

### Tasks

1. Create `DashboardView` (CBV) for client dashboard:
   - Display wallet balance
   - Display recent transactions (last 20)
   - Quick action buttons (deposit, withdraw, transfer)
2. Create `TransactionHistoryView` (FBV) returning HTML partial:
   - Use `hx-trigger="load"` for initial fetch
   - Support pagination with cursor-based infinite scroll
   - Return `transaction_item.html` components
3. Implement infinite scroll:
   - Add `hx-get` on last transaction item
   - Pass `?cursor=<timestamp>` for next page
   - Return empty state when no more data
4. Create `TransferForm` (ModelForm) with validation:
   - Recipient email or account number
   - Amount with min/max validation
   - Prevent self-transfers
5. Create `TransferView` (CBV) handling HTMX POST:
   - Valid: Process transfer, return success message + OOB balance update
   - Invalid: Return form partial with errors
6. Create `BalanceCardView` (FBV) for OOB balance updates:
   - Return `balance_card.html` with new balance
7. Implement HTMX OOB swaps:
   - Update balance card after successful transfer
   - Show/hide error alerts
8. Add loading states with `htmx-indicator`
9. **Testing:** Write tests for:
   - Dashboard view context data
   - Transaction history partial rendering
   - Infinite scroll pagination
   - Form validation and OOB swaps

### Deliverables

- [ ] DashboardView with balance and transactions
- [ ] TransactionHistoryView with infinite scroll
- [ ] TransferForm and TransferView with HTMX
- [ ] OOB balance updates
- [ ] Loading indicators
- [ ] 15+ pytest tests for HTMX views

### Verification

```bash
# Run dashboard tests
pytest wallet/tests/test_views.py -v

# Manual HTMX testing
python manage.py runserver 8500 --settings=core.settings.dev
# Test real-time balance updates and infinite scroll
```

---

## Phase 6: Async & Reporting

**Goal:** Set up Celery for background tasks and implement PDF statement generation.

**Concepts:** Task queues, Redis broker, ReportLab, HTMX polling, task status tracking.

### Tasks

1. Install dependencies: `celery==5.4.*`, `redis==5.2.*`, `reportlab==4.3.*`
2. Create `core/celery.py` configuration:
   - Auto-discover tasks
   - Configure broker and backend
3. Update `core/__init__.py` to load Celery app
4. Configure Celery settings in `settings/dev.py`:
   - `CELERY_BROKER_URL = 'redis://localhost:6379/0'`
   - `CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'`
   - `CELERY_TASK_TRACK_STARTED = True`
5. Create test task `debug_task` and verify with `celery -A core worker -l info`
6. Create `generate_statement_pdf` Celery task:
   - Use ReportLab to create professional PDF
   - Include: transactions for date range, balance summary, company branding
   - Save to `media/statements/`
7. Create `StatementRequestView` to trigger PDF generation:
   - Accept date range parameters
   - Return progress bar partial
8. Create `TaskStatusView` for polling:
   - Check `AsyncResult(task_id).status`
   - Return: PENDING/STARTED → progress bar, SUCCESS → download button, FAILURE → error
9. Implement HTMX polling:
   - `hx-get` with `hx-trigger="every 2s"` on progress bar
   - Replace with download button on SUCCESS
10. Create download view for generated PDFs
11. **Testing:** Write tests for:
    - Celery task execution (use `CELERY_TASK_ALWAYS_EAGER` for testing)
    - PDF generation content verification
    - Polling lifecycle (PENDING → SUCCESS)
    - Download view authorization

### Deliverables

- [ ] Celery configuration and worker setup
- [ ] PDF generation task with ReportLab
- [ ] HTMX progress bar with polling
- [ ] Statement download functionality
- [ ] 10+ pytest tests for async operations

### Verification

```bash
# Start Redis
redis-server

# Start Celery worker
celery -A core worker -l info

# Run async tests
pytest wallet/tests/test_async.py -v
```

---

## Phase 7: Staff & Analytics

**Goal:** Build staff back-office tools and analytics dashboard.

**Concepts:** Data aggregation, fraud detection, Chart.js, staff-only views.

### Tasks

1. Create `admin_dashboard` app: `python manage.py startapp admin_dashboard`
2. Implement `StaffDashboardView` (CBV):
   - List all transactions with filters (date, type, status)
   - Display flagged transactions prominently
   - Show system statistics (total users, transaction volume)
3. Create `FraudEngine` module (`admin_dashboard/fraud_engine.py`):
   - Rule 1: Flag transfers > $10,000
   - Rule 2: Flag users with > 5 transfers in 1 hour
   - Rule 3: Flag new accounts (< 7 days) with large transfers
   - Run fraud check on every transaction
4. Implement staff actions:
   - `ReviewTransactionView` — Mark transaction as reviewed/cleared
   - `FreezeWalletView` — Freeze/unfreeze client wallet
   - `UnfreezeWalletView` — Restore wallet access
5. Create `analytics` app: `python manage.py startapp analytics`
6. Implement aggregation views:
   - `SpendingByCategoryView` — Aggregate by transaction type
   - `SpendingByMonthView` — Monthly spending trends
   - Return JSON data for Chart.js
7. Create Chart.js dashboard component:
   - Bar chart for spending by category
   - Line chart for monthly trends
   - Date range filter with HTMX refresh
8. Integrate analytics into client dashboard (optional view)
9. **Testing:** Write tests for:
   - Fraud detection rules triggering correctly
   - Staff action authorization (only STAFF can access)
   - Aggregation query accuracy
   - Chart data format validation

### Deliverables

- [ ] Staff dashboard with transaction list
- [ ] FraudEngine with 3 detection rules
- [ ] Staff actions (review, freeze, unfreeze)
- [ ] Analytics app with aggregation views
- [ ] Chart.js integration with HTMX refresh
- [ ] 20+ pytest tests for staff tools and analytics

### Verification

```bash
# Run staff & analytics tests
pytest admin_dashboard/tests/ analytics/tests/ -v

# Manual staff testing
python manage.py createsuperuser --settings=core.settings.dev
# Login as staff, verify fraud detection and freeze functionality
```

---

## Phase 8: Performance & Deployment

**Goal:** Optimize queries, add indexes, and deploy to production.

**Concepts:** N+1 queries, `select_related`, `prefetch_related`, database indexes, WhiteNoise, Gunicorn.

### Tasks

1. Install `django-debug-toolbar==5.1.*`
2. Configure debug toolbar in `settings/dev.py`
3. Audit transaction history page for N+1 queries
4. Optimize queries:
   - Use `select_related` for ForeignKey (User, Wallet)
   - Use `prefetch_related` for reverse lookups
5. Add database indexes:
   - `Transaction.timestamp` (already indexed in Phase 4)
   - `CustomUser.email`
   - `Transaction.status`
   - `Transaction.type`
6. Write performance tests with `django-test-migrations` or manual query counting:
   - Verify constant query count regardless of list size
7. Configure `settings/prod.py` for production:
   - `DEBUG = False`
   - `ALLOWED_HOSTS` from environment
   - WhiteNoise: `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
   - Secure cookie settings
   - Database: SupaBase PostgreSQL via `DATABASE_URL`
8. Create `Procfile` for Render:
   ```
   web: gunicorn core.wsgi --bind 0.0.0.0:$PORT
   worker: celery -A core worker -l info
   ```
9. Create `requirements.txt` with all production dependencies
10. Set up Render deployment:
    - Connect GitHub repository
    - Set environment variables
    - Configure PostgreSQL (SupaBase)
    - Configure Redis (Render Redis or external)
11. Run production migrations
12. **Verification:**
    - Test live URL
    - Verify HTMX, Celery, static files work
    - Run full test suite on production-like environment

### Deliverables

- [ ] django-debug-toolbar configured
- [ ] Query optimization (select_related, prefetch_related)
- [ ] Database indexes on key fields
- [ ] Production settings (prod.py) with WhiteNoise
- [ ] Procfile for Render
- [ ] Deployed application on Render
- [ ] Performance test suite

### Verification

```bash
# Run performance tests
pytest --tb=short

# Check query count
pytest wallet/tests/test_performance.py::test_transaction_list_query_count -v

# Deploy to Render
# Follow Render deployment guide
```

---

## Project Structure

```
DigitalWallet/
├── .env                          # Local secrets (NEVER COMMIT)
├── .env.example                  # Template for environment variables
├── .gitignore                    # Git ignore rules
├── manage.py                     # Django management script
├── pytest.ini                    # Pytest configuration
├── conftest.py                   # Pytest fixtures
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── README.md                     # Project documentation
├── Constitution_Digital_Wallet.md # This file
├── Procfile                      # Render deployment config
│
├── .env_digital_wallet/          # Python virtual environment
│
├── core/                         # Django project settings
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py               # Shared settings
│   │   ├── dev.py                # Development settings
│   │   └── prod.py               # Production settings
│   ├── celery.py                 # Celery configuration
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py                   # WSGI application
│
├── accounts/                     # User authentication & profiles
│   ├── models.py                 # CustomUser, StaffProfile, ClientProfile
│   ├── managers.py               # CustomUserManager
│   ├── signals.py                # Auto-profile creation signals
│   ├── views.py                  # Login/logout views
│   ├── admin.py                  # Admin registration
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_signals.py
│
├── wallet/                       # Core financial engine
│   ├── models.py                 # Wallet, Transaction models
│   ├── services.py               # Atomic financial operations
│   ├── exceptions.py             # Custom exceptions
│   ├── forms.py                  # Transaction forms
│   ├── views.py                  # Dashboard & transaction views
│   ├── admin.py                  # Admin registration
│   └── tests/
│       ├── test_models.py
│       ├── test_services.py
│       ├── test_views.py
│       └── test_async.py
│
├── analytics/                    # Data visualization & reports
│   ├── views.py                  # Analytics endpoints
│   └── tests/
│       └── test_views.py
│
├── admin_dashboard/              # Staff back-office tools
│   ├── views.py                  # Staff dashboard views
│   ├── fraud_engine.py           # Fraud detection rules
│   └── tests/
│       └── test_fraud.py
│
├── static/
│   ├── css/
│   │   └── modules/              # Modular CSS files
│   │       ├── layout.css
│   │       ├── navigation.css
│   │       ├── forms.css
│   │       └── utilities.css
│   └── js/
│       └── modules/              # Modular JavaScript files
│           ├── charts.js
│           └── utils.js
│
├── templates/
│   ├── base.html                 # Base template
│   ├── __snippets__/             # Reusable snippets
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   └── footer.html
│   └── components/               # Reusable components
│       ├── balance_card.html
│       ├── transaction_item.html
│       ├── alert.html
│       ├── modal.html
│       └── progress_bar.html
│
├── scripts/                      # Automation bash scripts
│   ├── git-phase-commit.sh       # Commit to phase branch
│   ├── git-phase-merge.sh        # Merge phase to master
│   └── setup.sh                  # Project setup automation
│
└── media/                        # User uploads
    ├── statements/               # Generated PDF statements
    └── kyc/                      # KYC documents
```

---

## Git Workflow

### Branch Naming Convention

| Phase | Branch Name |
|-------|-------------|
| 1 | `phase-setup-automation` |
| 2 | `phase-identity-auth` |
| 3 | `phase-frontend-core` |
| 4 | `phase-wallet-engine` |
| 5 | `phase-dashboard-htmx` |
| 6 | `phase-async-reporting` |
| 7 | `phase-staff-analytics` |
| 8 | `phase-qa-deployment` |

### Commit to Phase Branch

```bash
# Usage: ./scripts/git-phase-commit.sh <phase_number> "<title>" "<description>"
./scripts/git-phase-commit.sh 2 "Identity & Access Management" "Implemented CustomUser, profiles, and login separation"
```

### Merge Phase to Master

```bash
# Usage: ./scripts/git-phase-merge.sh <phase_number>
./scripts/git-phase-merge.sh 2
```

---

## Testing Strategy

### Test Organization

- Tests live in `app/tests/` directories
- One test file per module: `test_models.py`, `test_views.py`, `test_services.py`
- Use pytest fixtures in `conftest.py` for common setup

### Running Tests

```bash
# All tests
pytest

# Specific app
pytest accounts/tests/ -v

# With coverage
pytest --cov=. --cov-report=html

# Fail fast
pytest -x
```

### Test Coverage Requirements

- **Models:** 100% field and method coverage
- **Services:** 100% path coverage (success, failure, rollback)
- **Views:** 90%+ coverage (success, error, permission denied)
- **Integration:** Critical user flows (login, transfer, PDF generation)

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] No console errors in browser
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Database migrations applied
- [ ] Environment variables set in production

### Production Environment Variables

```bash
SECRET_KEY=<secure-random-key>
DEBUG=False
ALLOWED_HOSTS=<your-domain.com>
DATABASE_URL=postgresql://user:pass@host:port/dbname
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0
```

### Post-Deployment Verification

- [ ] Homepage loads (HTTPS)
- [ ] Login works
- [ ] Dashboard displays balance
- [ ] Transactions process correctly
- [ ] HTMX updates work (no page reloads)
- [ ] Celery worker running (PDF generation)
- [ ] Static files served correctly
- [ ] Error pages customized (404, 500)

---

*Last Updated: March 4, 2026*
*Version: 2.0 (Reorganized for practical workflow)*
