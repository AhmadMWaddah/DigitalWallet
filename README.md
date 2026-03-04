# Digital Wallet Dashboard

![Digital Wallet Dashboard](Digital_Wallet.png)

A secure, production-ready **Fintech Digital Wallet Dashboard** built with Django 5.2 (LTS), HTMX, and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2.LTS-green)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/tests-52%20passed-brightgreen)

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Phase Progress](#phase-progress)
- [Contributing](#contributing)

---

## ✨ Features

### **Dual-Portal System**
- **Staff Portal**: Admin and labor access with fraud monitoring tools
- **Client Portal**: User dashboard for wallet management

### **Financial Operations**
- 💰 **Deposits**: Add funds to wallet
- 💸 **Withdrawals**: Remove funds from wallet
- 🔄 **Transfers**: Send money between users
- 📊 **Transaction History**: Infinite-scroll ledger with real-time updates

### **Security & Compliance**
- 🔒 **Email-based Authentication**: No usernames, secure email login
- 🚨 **Fraud Detection**: Automated flagging of suspicious transactions
  - Transfers > $10,000
  - > 5 transfers per hour
- ❄️ **Account Freezing**: Staff can freeze suspicious accounts

### **Advanced Features**
- 📄 **PDF Statements**: Async generation with HTMX progress bars
- 📈 **Analytics Dashboard**: Spending visualization with Chart.js
- ⚡ **HTMX Interactivity**: Real-time balance updates, no page reloads
- 🎨 **Custom Modular CSS**: No Bootstrap/Tailwind, clean separation of concerns

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
│   └── wsgi.py                   # WSGI application
│
├── accounts/                     # User authentication & profiles
│   ├── models.py                 # CustomUser, StaffProfile, ClientProfile
│   ├── managers.py               # CustomUserManager
│   ├── signals.py                # Auto-profile creation signals
│   ├── views.py                  # Login/logout views
│   ├── admin.py                  # Admin registration
│   └── tests/                    # Authentication tests
│       ├── test_models.py
│       └── test_views.py
│
├── wallet/                       # Core financial engine
│   ├── models.py                 # Wallet, Transaction models
│   ├── services.py               # Atomic financial operations
│   ├── views.py                  # Dashboard & transaction views
│   └── tests/                    # Wallet & transaction tests
│
├── analytics/                    # Data visualization & reports
│   ├── views.py                  # Analytics endpoints
│   └── tests/                    # Analytics tests
│
├── admin_dashboard/              # Staff back-office tools
│   ├── views.py                  # Staff dashboard views
│   ├── fraud_engine.py           # Fraud detection rules
│   └── tests/                    # Staff tools tests
│
├── static/
│   ├── css/
│   │   └── modules/              # Modular CSS files
│   │       ├── layout.css
│   │       ├── navigation.css
│   │       └── forms.css
│   └── js/
│       └── modules/              # Modular JavaScript files
│
├── templates/
│   ├── base.html                 # Base template with responsive shell
│   ├── __snippets__/             # Reusable snippets (navbar, sidebar, footer)
│   └── components/               # Reusable components
│       ├── balance_card.html
│       ├── transaction_item.html
│       └── alert.html
│
├── scripts/                      # Automation scripts
│   ├── git-phase-commit.sh       # Commit to phase branch
│   ├── git-phase-merge.sh        # Merge phase to master
│   └── setup.sh                  # Project setup automation
│
└── media/                        # User uploads (PDFs, KYC documents)
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

   This will:
   - Activate the virtual environment
   - Install dependencies
   - Run database migrations

3. **Create a superuser:**
   ```bash
   python manage.py createsuperuser --settings=core.settings.dev
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver 8500 --settings=core.settings.dev
   ```

5. **Start Celery worker (optional, for async tasks):**
   ```bash
   celery -A core worker -l info
   ```

6. **Start Redis (required for Celery):**
   ```bash
   redis-server
   ```

---

## 🔄 Development Workflow

### **Phase-Based Development**

This project follows a strict phase-based development workflow with automated Git scripts.

#### **Commit to a Phase Branch:**

```bash
# Usage: ./scripts/git-phase-commit.sh <phase_number> "<title>" "<description>"
./scripts/git-phase-commit.sh 4 "Implemented Custom User Model" "Replaced username with email and added user_type field. Verified with tests."
```

#### **Merge Phase to Master:**

```bash
# Usage: ./scripts/git-phase-merge.sh <phase_number>
./scripts/git-phase-merge.sh 4
```

### **Branch Naming Convention**

| Phase | Branch Name                |
|-------|----------------------------|
|   1   | `phase-setup-automation`   |
|   2   | `phase-identity-auth`      |
|   3   | `phase-frontend-core`      |
|   4   | `phase-wallet-engine`      |
|   5   | `phase-dashboard-htmx`     |
|   6   | `phase-async-reporting`    |
|   7   | `phase-staff-analytics`    |
|   8   | `phase-qa-deployment`      |

### **Zero-Error Policy**

Before every commit:
1. Run tests: `pytest`
2. Verify manually (if UI changes)
3. Only then commit

---

## 🧪 Testing

### **Run All Tests:**

```bash
pytest
```

### **Run Specific Test File:**

```bash
pytest accounts/tests/test_models.py -v
```

### **Run with Coverage:**

```bash
pytest --cov=. --cov-report=html
```

### **Testing Mandate**

**Every feature must have corresponding tests.** No exceptions.

---

## 🌐 Deployment

### **Production Settings**

1. Set environment variables on Render:
   - `SECRET_KEY`
   - `DATABASE_URL` (SupaBase PostgreSQL)
   - `CELERY_BROKER_URL` (Redis)
   - `ALLOWED_HOSTS`

2. Configure `core/settings/prod.py`:
   - `DEBUG = False`
   - WhiteNoise for static files
   - Secure cookie settings

3. Deploy to Render:
   - Connect GitHub repository
   - Set build command: `./scripts/setup.sh`
   - Set start command: `gunicorn core.wsgi --bind 0.0.0.0:$PORT`

4. Run migrations:
   ```bash
   python manage.py migrate --settings=core.settings.prod
   ```

---

## 📊 Phase Progress (Optimized 8-Phase Structure)

| Phase | Name                         | Status      | Branch | Tests      |
|-------|------------------------------|-------------|--------|------------|
| **1** | Foundation & Automation      | ✅ Complete | Merged | 13 passing |
| **2** | Identity & Access Management | ✅ Complete | Merged | 39 passing |
| **3** | Frontend Foundation          | ✅ Complete | Merged | -          |
| **4** | Wallet Engine                | ⏳ Pending  | -      | -          |
| **5** | HTMX Dashboard               | ⏳ Pending  | -      | -          |
| **6** | Async & Reporting            | ⏳ Pending  | -      | -          |
| **7** | Staff & Analytics            | ⏳ Pending  | -      | -          |
| **8** | Performance & Deployment     | ⏳ Pending  | -      | -          |

> **Note:** The original 18 phases have been consolidated into 8 practical phases for better workflow efficiency. See `Constitution_Digital_Wallet.md` for details.

### **Completed Features:**

**Phase 1 - Foundation:**
- ✅ Django 5.2 project with settings package (base/dev/prod)
- ✅ Git workflow with automated phase scripts
- ✅ Pre-commit hooks (black, flake8, isort)
- ✅ Pytest configuration with 13 passing tests
- ✅ GitHub repository setup

**Phase 2 - Identity & Access:**
- ✅ CustomUser model with email-based authentication
- ✅ StaffProfile and ClientProfile with auto-creation signals
- ✅ Portal separation (Staff → /admin/, Client → /dashboard/)
- ✅ StaffOnlyMixin and ClientOnlyMixin for access control
- ✅ Custom login view with EmailAuthenticationForm
- ✅ Session & CSRF security hardening
- ✅ 39 passing pytest tests

**Phase 3 - Frontend Foundation:**
- ✅ Responsive base.html with navbar, sidebar, main content, footer
- ✅ Modular CSS architecture (layout, navigation, forms, utilities, dashboard)
- ✅ HTMX integration via CDN
- ✅ Reusable components (balance card, transaction item, alert, modal)
- ✅ Navigation snippets (navbar, sidebar, footer)
- ✅ DashboardView for testing components

---

## 🤝 Contributing

This is a private project. For questions or issues, contact **Ahmad**.

### **Code Standards**

- **Docstrings**: Use `"""Docstring content"""` for classes and complex functions
- **Comments**: Explain **why**, not **what**
- **Section Headers**: Use `# -- Section Name` for major code sections
- **Views**: CBVs for structure, FBVs for HTMX actions
- **CSS**: Modular approach in `static/css/modules/`
- **JS**: Modular approach in `static/js/modules/`

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Repository

**GitHub**: https://github.com/AhmadMWaddah/DigitalWallet

---

*Last Updated: March 5, 2026*
