# Digital Wallet Dashboard

![Digital Wallet Dashboard](Digital_Wallet.png)

A secure, production-ready **Fintech Digital Wallet Dashboard** built with Django 5.2 (LTS), HTMX, and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2.LTS-green)
![License](https://img.shields.io/badge/License-MIT-red)
![Tests](https://img.shields.io/badge/tests-144%20passed-brightgreen)

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Demo Data & Seeding](#demo-data--seeding)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Phase Progress](#phase-progress)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## ✨ Features (v1.2 - Current)

### **Dual-Portal System**
- **Staff Portal**: Django Admin integration for user and wallet management.
- **Client Portal**: Dedicated dashboard for wallet operations and history.

### **Financial Operations**
- 💰 **Deposits**: Add funds to wallet via HTMX-powered forms.
- 💸 **Withdrawals**: Securely remove funds with balance validation.
- 🔄 **Transfers**: Atomic peer-to-peer transfers with rollback protection.
- 📊 **Transaction History**: Infinite-scroll ledger with cursor-based pagination.

### **Async & Reporting (Latest!)**
- 📄 **PDF Statements**: Professional transaction reports generated asynchronously via Celery & ReportLab.
- ⌛ **Real-time Progress**: HTMX-powered state-machine UI for background tasks.
- 📉 **Running Balance**: Accurate historical balance tracking and "Opening Balance" calculations.

### **Identity & Security**
- 🔒 **Email-based Authentication**: Secure login using email instead of usernames.
- 👤 **Automated Profiles**: Client and Staff profiles auto-created via Django signals.
- 🛡️ **Atomic Integrity**: All financial operations use `transaction.atomic()` and idempotency checks.

### **HTMX Interactivity**
- ⚡ **Real-time Balance**: Out-of-Band (OOB) updates refresh balance card without page reloads.
- 🔄 **Inline Forms**: Deposit, Withdraw, and Transfer forms render and submit via HTMX.
- ⌛ **Loading States**: Visual feedback during transaction processing using `htmx-indicator`.

---

## 🛠️ Tech Stack

| Layer               | Technology                               |
|---------------------|------------------------------------------|
| **Backend**         | Python 3.12, Django 5.2 (LTS)            |
| **Database**        | PostgreSQL (SupaBase for production)     |
| **Frontend**        | HTMX, Custom Modular CSS, Vanilla JS     |
| **Async Tasks**     | Celery + Redis                           |
| **PDF Generation**  | ReportLab                                |
| **Testing**         | Pytest, pytest-django                    |
| **Deployment**      | Render, Gunicorn, WhiteNoise             |
| **Version Control** | Git, GitHub CLI                          |

---

## 📁 Project Structure

```
DigitalWallet/
├── .env                          # Local environment variables (NEVER COMMIT)
├── .env.example                  # Template for environment variables
├── .gitignore                    # Git ignore rules
├── .pre-commit-config.yaml       # Code quality hooks (black, flake8, isort)
├── manage.py                     # Django management script
├── pytest.ini                    # Pytest configuration
├── conftest.py                   # Pytest fixtures
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── README.md                     # This file
├── Constitution_Digital_Wallet.md # Project constitution & phase plan
├── LICENSE                       # MIT License
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
│   ├── asgi.py                   # ASGI application
│   └── wsgi.py                   # WSGI application
│
├── accounts/                     # User authentication & profiles
│   ├── models.py                 # CustomUser, StaffProfile, ClientProfile
│   ├── managers.py               # CustomUserManager
│   ├── signals.py                # Auto-profile creation signals
│   ├── views.py                  # Login/logout views
│   ├── admin.py                  # Admin registration
│   └── tests/                    # Authentication tests
│
├── wallet/                       # Core financial engine
│   ├── models.py                 # Wallet, Transaction models
│   ├── services.py               # Atomic financial operations
│   ├── views.py                  # Dashboard & transaction views
│   ├── forms.py                  # Transaction forms
│   ├── tasks.py                  # Celery background tasks
│   ├── exceptions.py             # Financial logic exceptions
│   ├── utils/
│   │   └── pdf_generator.py      # PDF generation service
│   └── tests/                    # Wallet & transaction tests
│
├── static/
│   ├── css/                      # Modular CSS files (layout, navigation, forms, dashboard)
│   └── js/                       # Modular JavaScript files
│
├── templates/
│   ├── base.html                 # Base template with responsive shell
│   ├── __snippets__/             # Reusable snippets (navbar, sidebar, footer)
│   ├── components/               # Reusable components (balance_card, modal)
│   ├── accounts/                 # Auth templates
│   └── wallet/                   # Dashboard templates
│
├── scripts/                      # Automation scripts
│   ├── git-phase-commit.sh       # Commit to phase branch
│   ├── git-phase-merge.sh        # Merge phase to master
│   └── setup.sh                  # Project setup automation
│
└── media/                        # User uploads (PDF statements)
```

---

## 🚀 Getting Started

### **Prerequisites**

- Python 3.12+
- PostgreSQL (for production)
- Redis (for Celery)
- Git

### **Installation**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AhmadMWaddah/DigitalWallet.git
   cd DigitalWallet
   ```

2. **Run the setup script:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Create a superuser:**
   ```bash
   python manage.py createsuperuser --settings=core.settings.dev
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver 8500 --settings=core.settings.dev
   ```

---

## 💎 Demo Data & Seeding

To quickly populate the application with realistic data for testing or demonstration, use the built-in seed command:

```bash
# Create 5 dummy users with funded wallets and random transactions
python manage.py seed_wallets --settings=core.settings.dev
```

---

## 🔄 Development Workflow

### **Phase-Based Development**

This project follows a strict phase-based development workflow with automated Git scripts.

#### **Commit to a Phase Branch:**

```bash
# Usage: ./scripts/git-phase-commit.sh <phase_number> "<title>" "<description>"
./scripts/git-phase-commit.sh 6 "Async & Reporting" "Implemented PDF generation and HTMX polling."
```

#### **Merge Phase to Master:**

```bash
# Usage: ./scripts/git-phase-merge.sh <phase_number>
./scripts/git-phase-merge.sh 6
```

#### **Master Merge Best Practices:**

- **Master is the Truth:** The `master` branch is our production-ready source of truth. It must never contain failing tests or incomplete features.
- **Branch Iteration:** Work iteratively within `phase-n` or `fix-` branches. Generate code, test, fix errors, and add modifications in the branch as many times as needed before proposing a merge.
- **Manager-Led Approval:** Merging to `master` is **not automatic**. It occurs only after the Manager (Ahmad) confirms that all tasks, fixes, and additional requirements for the milestone are complete.
- **Atomic Releases:** Treat the merge of a full phase as a formal release. Once merged, `master` should be fully functional and stable.

---

## 🧪 Testing

### **Run All Tests:**

```bash
pytest
```

### **Run with Coverage:**

```bash
pytest --cov=. --cov-report=html
```

### **Testing Mandate**

**Every feature must have corresponding tests.** Total currently: **144 passed**.

---

## 📊 Phase Progress (Optimized 8-Phase Structure)

| Phase | Name                         | Status      | Branch | Tests      |
|-------|------------------------------|-------------|--------|------------|
| **1** | Foundation & Automation      | ✅ Complete | Merged | 13 passing |
| **2** | Identity & Access Management | ✅ Complete | Merged | 46 passing |
| **3** | Frontend Foundation          | ✅ Complete | Merged | 9 passing  |
| **4** | Wallet Engine                | ✅ Complete | Merged | 37 passing |
| **5** | HTMX Dashboard               | ✅ Complete | Merged | 26 passing |
| **6** | Async & Reporting            | ✅ Complete | Merged | 13 passing |
| **7** | Staff & Analytics            | ⏳ Next Up  | -      | -          |
| **8** | Performance & Deployment     | ⏳ Planned  | -      | -          |

---

## 🛤️ Roadmap (Upcoming Features)

### **Phase 7: Staff & Analytics**
- 🚨 **Fraud Detection**: Automated flagging of transfers > $10K or > 5/hour.
- ❄️ **Account Management**: Staff ability to freeze/unfreeze wallets.
- 📈 **Analytics Dashboard**: Spending visualization with Chart.js.

### **Phase 8: Performance & Deployment**
- 🚀 **Optimization**: Select related/prefetch related for N+1 fixes.
- ☁️ **Deployment**: Production-ready setup on Render with WhiteNoise.

---

## 🤝 Contributing

This is a private project. For questions or issues, contact **Ahmad M. Waddah**.

---

## 📝 License

This project is licensed under the **MIT License**.

---

## 🔗 Repository

**GitHub**: https://github.com/AhmadMWaddah/DigitalWallet

---

*Last Updated: March 15, 2026*
