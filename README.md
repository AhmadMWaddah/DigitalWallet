# Digital Wallet Dashboard

![Digital Wallet Dashboard](Digital_Wallet.png)

A secure, production-ready **Fintech Digital Wallet Dashboard** built with Django 5.2 (LTS), HTMX, and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2.LTS-green)
![Tests](https://img.shields.io/badge/tests-160+%20passed-brightgreen)

---

## ✨ Features (v2.0 - Current)

### **Dual-Portal System**
- **Staff Portal**: Full dashboard for transaction monitoring, fraud review, and wallet management.
- **Client Portal**: Dedicated dashboard for secure wallet operations and PDF reporting.

### **Financial Operations & Integrity**
- 🛡️ **Atomic Integrity**: All operations use `select_for_update()` and `transaction.atomic()` to prevent double-spending.
- 🔄 **Auto-Reversal**: Rejected flagged transfers automatically restore funds to the sender.
- 💰 **Wallet Lifecycle**: Secure deposits, withdrawals, and peer-to-peer transfers.
- 📊 **Transaction Ledger**: Infinite-scroll history with cursor-based pagination.

### **Async & Fraud Protection**
- 🚨 **Fraud Engine**: Automated flagging for large transfers (> $10K) or high frequency.
- 📄 **Async PDF Reports**: Statement generation via Celery & ReportLab with real-time progress bars.
- 📈 **Analytics**: Spending visualization for both Staff and Clients using Chart.js.

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
| **7** | Staff & Analytics            | ✅ Complete | Merged | 20+ passing|
| **8** | Performance & Deployment     | 🚧 In Progress | `phase-8` | 5+ passing |

---

## 🔄 Development Workflow

### **Git Identity (Multi-Agent)**
This project uses a role-based commit system. Use `./scripts/git-phase-commit.sh` with the appropriate role:
- `dev`: Qwen-Coder
- `consult`: Gemini-CLI
- `review`: OpenAI-Codex
- `mgr`: Ahmad (Manager)

---

## 🧪 Testing

```bash
# Run all tests
pytest
```

---

*Last Updated: March 21, 2026*
