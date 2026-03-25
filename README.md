# Digital Wallet Dashboard

![Digital Wallet Dashboard](Digital_Wallet.png)

A full-stack fintech wallet application built with Django, HTMX, Celery, Redis, and PostgreSQL-oriented settings. The project is designed around strict portal separation, secure wallet operations, fraud review workflows, async PDF statements, and staff analytics.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2.LTS-green)
![HTMX](https://img.shields.io/badge/Frontend-HTMX-3366CC)
![Pytest](https://img.shields.io/badge/Tested_with-pytest-brightgreen)

---

## Overview

Digital Wallet Dashboard is a multi-portal financial operations project with:

- a **client portal** for wallet usage
- a **staff portal** for fraud review and operational oversight
- a **custom email-based authentication system**
- **atomic wallet services** to protect balances and transaction consistency
- **async statement generation** for downloadable PDF reports
- **analytics dashboards** for internal operational visibility

The application itself is complete enough for local use and verification. **Deployment is intentionally not completed at this stage** to save time and cost.

---

## What The Project Includes

### Client Features

- Email-based registration and login
- Wallet dashboard with live balance and recent transactions
- Secure deposit, withdrawal, and transfer flows
- Infinite-scroll transaction history
- Profile page and account security page
- Password reset flow
- Password change flow with Django validation
- PDF statement request and download flow

### Staff Features

- Staff-only operations dashboard
- Review queue for flagged transactions
- Approve or reject suspicious transfers
- Automatic reversal on rejected flagged transfers
- Wallet freeze and unfreeze actions
- Analytics dashboard with Chart.js visualizations

### Security & Integrity Features

- Dual-portal separation between client and staff access
- Custom `CustomUser` model with `STAFF` and `CLIENT` user types
- `StaffOnlyMixin` and `ClientOnlyMixin` access control
- Atomic balance updates using service-layer logic
- Fraud detection for large or high-frequency transfers
- Session-aware security page showing current session metadata
- Password validation using Django auth validators
- Custom 403 handling with role-aware redirects

---

## Core Modules

| App          | Purpose                                                                             |
|--------------|-------------------------------------------------------------------------------------|
| `accounts`   | Authentication, custom user model, profiles, password reset, security/profile pages |
| `wallet`     | Wallet model, transactions, dashboard, deposits, withdrawals, transfers, statements |
| `operations` | Staff dashboard, fraud review, wallet freeze/unfreeze                               |
| `analytics`  | Staff analytics dashboards and Chart.js data endpoints                              |
| `core`       | Settings, root URLs, environment configuration, Celery bootstrap                    |

---

## Tech Stack

| Layer        | Technology                                                                  |
|--------------|-----------------------------------------------------------------------------|
| Backend      | Python 3.12, Django 5.2                                                     |
| Database     | SQLite for local development, PostgreSQL-ready configuration for production |
| Frontend     | Django Templates, HTMX, custom modular CSS, Vanilla JavaScript              |
| Auth         | Custom email-based `CustomUser`                                             |
| Async        | Celery, Redis                                                               |
| Reporting    | ReportLab PDF generation                                                    |
| Analytics    | Chart.js                                                                    |
| Testing      | Pytest, pytest-django, pytest-cov                                           |
| Code Quality | pre-commit, black, flake8, isort                                            |

---

## Application Routes

| Area                     | Path           |
|--------------------------|----------------|
| Role-aware home redirect | `/`            |
| Django admin             | `/admin/`      |
| Accounts                 | `/accounts/`   |
| Client wallet portal     | `/dashboard/`  |
| Staff portal             | `/staff/`      |
| Analytics                | `/analytics/`  |

### Important Endpoints

- `/accounts/login/`
- `/accounts/register/`
- `/accounts/profile/`
- `/accounts/security/`
- `/dashboard/`
- `/dashboard/deposit/`
- `/dashboard/withdraw/`
- `/dashboard/transfer/`
- `/dashboard/transactions/`
- `/dashboard/statement/request/`
- `/staff/dashboard/`
- `/analytics/dashboard/`

---

## Local Development Setup

### Prerequisites

- Python `3.12`
- Redis
- virtual environment support

### Option 1: Use The Project Setup Script

```bash
source .env_digital_wallet/bin/activate
./scripts/setup.sh
```

### Option 2: Manual Setup

```bash
python -m venv .env_digital_wallet
source .env_digital_wallet/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
pre-commit install
python manage.py migrate --settings=core.settings.dev
python manage.py createsuperuser --settings=core.settings.dev
python manage.py runserver 8500 --settings=core.settings.dev
```

### Environment Variables

The project reads configuration from `.env`. Start by copying:

```bash
cp .env.example .env
```

Main variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- optional email settings for password reset workflows

By default:

- local development uses `SQLite`
- Celery expects Redis at `redis://localhost:6379/0`
- email uses Django console backend in `core.settings.dev`

---

## Running The Project

### Web App

```bash
source .env_digital_wallet/bin/activate
python manage.py runserver 8500 --settings=core.settings.dev
```

Open:

- `http://127.0.0.1:8500/`

### Redis

```bash
redis-server
```

### Celery Worker

Required for async statement generation:

```bash
source .env_digital_wallet/bin/activate
celery -A core worker -l info
```

If Redis/Celery are not running, the main application still works, but async PDF statement generation will not complete.

---

## Default Development Flow

1. Create or activate `.env_digital_wallet`
2. Update `.env`
3. Run migrations
4. Create a superuser
5. Start Django on port `8500`
6. Start Redis and Celery if you want statement generation
7. Run tests before committing

---

## Testing & Quality

### Run All Tests

```bash
pytest
```

### Run By App

```bash
pytest accounts/tests/ -v
pytest wallet/tests/ -v
pytest operations/tests/ -v
pytest analytics/tests/ -v
pytest core/tests/ -v
```

### Coverage

```bash
pytest --cov
```

### Django System Check

```bash
python manage.py check --settings=core.settings.dev
```

### Formatting & Linting

```bash
pre-commit run --all-files
black .
flake8
isort .
```

---

## Project Structure

```text
DigitalWallet/
├── accounts/                  # Authentication, user model, profiles, security views
├── analytics/                 # Staff analytics dashboard and chart endpoints
├── core/                      # Settings, root URLs, Celery app bootstrap
├── operations/                # Staff dashboard and fraud review tools
├── scripts/                   # Setup, git workflow, manual helper scripts
├── static/                    # CSS, JS, frontend assets
├── templates/                 # Base templates, snippets, account/wallet/staff pages
├── wallet/                    # Wallet models, services, views, PDF tasks
├── .env.example               # Example environment configuration
├── manage.py
├── requirements.txt
└── requirements-dev.txt
```

---

## Business Rules & Technical Notes

### Wallet Operations

- deposits, withdrawals, and transfers are handled through service-layer functions
- transfers isolate funds during fraud review to prevent double-spending problems
- rejected flagged transfers automatically reverse funds back to the sender

### Fraud Review

The fraud engine currently flags suspicious transfers based on rules such as:

- transfer amounts above the configured high-risk threshold
- unusually high transaction frequency

Flagged transfers are routed to the staff dashboard for manual review.

### Statements

- statements are generated asynchronously
- progress is exposed through task status polling
- completed statements can be downloaded after ownership verification

### Portal Separation

- superusers are directed to Django admin
- staff users are directed to the staff dashboard
- client users are directed to the wallet dashboard
- unauthorized cross-portal access returns a custom 403 experience

---

## Git Workflow Used In This Repository

This project uses helper scripts for phase-oriented workflow:

- `scripts/git-phase-commit.sh`
- `scripts/git-phase-merge.sh`

Role-based commit identities supported by the commit script:

- `dev` → Qwen-Coder
- `consult` → Gemini-CLI
- `review` → OpenAI-Codex
- `mgr` → Ahmad

Example:

```bash
./scripts/git-phase-commit.sh 8 "Title" "Description" review
```

---

## AI Collaboration Model

This repository documents a multi-agent workflow in `Constitution_Digital_Wallet.md`.

Primary roles:

- **Ahmad**: manager and final approver
- **Qwen**: implementation-focused developer AI
- **Gem**: consultant AI for architecture and planning
- **Cod**: reviewer AI for regression detection, verification, and support fixes

All AI-generated work is still expected to follow the same branch, testing, and approval rules as any other contribution.

---

## Current Status

### Complete

- application architecture
- authentication and portal separation
- wallet engine and transaction workflows
- HTMX dashboard behavior
- fraud review tooling
- analytics
- async PDF statement generation
- local development workflow
- automated tests and quality tooling

### Intentionally Not Finished

- production deployment
- paid hosting rollout
- final infrastructure spend

This repository can still serve as a strong local demonstration, portfolio project, and reference implementation for secure Django wallet workflows.

---

## Recommended Demo Flow

If you want to present the project locally, the fastest path is:

1. Run migrations and create a superuser
2. Start Django on port `8500`
3. Start Redis and Celery
4. Create a client account
5. Demonstrate deposit, withdrawal, transfer, and transaction history
6. Trigger a flagged transfer
7. Review it from the staff dashboard
8. Open analytics
9. Request and download a PDF statement

---

## Documentation References

- [Constitution_Digital_Wallet.md](Constitution_Digital_Wallet.md)
- [.env.example](.env.example)
- [scripts/setup.sh](scripts/setup.sh)
- [scripts/git-phase-commit.sh](scripts/git-phase-commit.sh)
- [scripts/git-phase-merge.sh](scripts/git-phase-merge.sh)

---

## License

This repository is licensed under the terms of the included [LICENSE](LICENSE).
