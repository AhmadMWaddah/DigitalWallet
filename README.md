# Digital Wallet Dashboard

**Production-ready Django fintech wallet with atomic transactions, fraud detection, and HTMX dashboard.**

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

## Documentation

| Document | Contents |
|----------|----------|
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, running, testing, code quality |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules, tech stack, business rules, project structure |
| [Constitution_Digital_Wallet.md](Constitution_Digital_Wallet.md) | Project plan, phases, AI collaboration model |
| [.env.example](.env.example) | Environment variable template |
| [scripts/setup.sh](scripts/setup.sh) | One-command project setup |

---

## License

This repository is licensed under the terms of the included [LICENSE](LICENSE).
