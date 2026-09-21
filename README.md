# Digital Wallet Dashboard

**Production-ready Django fintech wallet with atomic transactions, fraud detection, REST API, QR payments, transfer fees, KYC verification, and HTMX dashboard.**

![Digital Wallet Dashboard](Digital_Wallet.png)

A full-stack fintech wallet application built with Django, DRF, HTMX, Celery, Redis, and PostgreSQL-oriented settings. The project is designed around strict portal separation, secure wallet operations, fraud review workflows, KYC-gated large transfers, async PDF statements, staff analytics, and a versioned REST API with OpenAPI docs.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![DRF](https://img.shields.io/badge/API-DRF_v1-orange)
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
- Secure deposit, withdrawal, and transfer flows (sender-paid fee: 1.5% + $0.20)
- QR scan-to-pay: signed personal QR code + scan-and-pay page
- KYC identity verification (required for transfers above $10,000)
- Infinite-scroll transaction history
- Profile page and account security page
- Password reset flow
- Password change flow with Django validation
- PDF statement request and download flow
- REST API v1 (`/api/v1/`) + interactive Swagger UI (`/api/docs/`)

### Staff Features

- Staff-only operations dashboard
- Review queue for flagged transactions
- KYC application queue (approve/reject with reason)
- Approve or reject suspicious transfers
- Automatic reversal on rejected flagged transfers (transfer amount; earned fee stays)
- Wallet freeze and unfreeze actions
- Analytics dashboard with Chart.js visualizations

### Security & Integrity Features

- Dual-portal separation between client and staff access
- Custom `CustomUser` model with `STAFF` and `CLIENT` user types
- `StaffOnlyMixin` and `ClientOnlyMixin` access control
- Atomic balance updates using service-layer logic
- Sender-paid transfer fees recorded as `FEE` ledger entries
- KYC gate: transfers above $10,000 require `VERIFIED` status
- Fraud detection for large or high-frequency transfers
- Session-aware security page showing current session metadata
- Password validation using Django auth validators
- Custom 403 handling with role-aware redirects

---

## Recommended Demo Flow

If you want to present the project locally, the fastest path is:

1. Run migrations and create a superuser
2. Start Django on port `8500`
3. Start Redis and Celery
4. Create a client account
5. Demonstrate deposit, withdrawal, transfer (note the fee), and transaction history
6. Show QR scan-to-pay between two clients
7. Upload a KYC document, approve it from the staff dashboard
8. Trigger a flagged transfer
9. Review it from the staff dashboard
10. Open analytics
11. Request and download a PDF statement
12. Browse the REST API at `/api/docs/`

---

## Current Status

### Complete

- application architecture
- authentication and portal separation
- wallet engine and transaction workflows (fees, KYC gate, QR pay)
- REST API v1 with OpenAPI docs
- HTMX dashboard behavior
- fraud review tooling + KYC review tooling
- analytics
- async PDF statement generation
- rate limiting + security scanning in CI
- structured JSON logging + health endpoint
- uv dependency management with lockfile
- local development workflow
- automated tests (295) and quality tooling

### Intentionally Not Finished

- production deployment
- paid hosting rollout
- final infrastructure spend

This repository can still serve as a strong local demonstration, portfolio project, and reference implementation for secure Django wallet workflows.

---

## Documentation

| Document | Contents |
|----------|----------|
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, running, testing, code quality |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules, tech stack, business rules, project structure |
| [SECURITY.md](docs/SECURITY.md) | Security controls with file pointers |
| [FIX_PLAN.md](docs/FIX_PLAN.md) | Executed fix & upgrade plan (historical record) |
| [CONSTITUTION.md](docs/CONSTITUTION.md) | Original project plan, phases, AI collaboration model |
| [.env.example](.env.example) | Environment variable template |
| [scripts/setup.sh](scripts/setup.sh) | One-command project setup |

---

## License

This repository is licensed under the terms of the included [LICENSE](LICENSE).
