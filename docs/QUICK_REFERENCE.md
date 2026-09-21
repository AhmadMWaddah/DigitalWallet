# Quick Reference — Fix Plan Execution

> **Status: executed Sept 2026.** Actual branch names used `fix-`/`feat-`/`chore-`
> with dashes (not slashes). Kept here as the historical record.

## Branch Naming (as executed)
```
fix-staff-review-json-bug
fix-balance-card-response
fix-light-theme-default
feat-dev-docker-compose
feat-health-endpoint
feat-rate-limiting
feat-test-settings
feat-linting-setup
feat-github-actions-ci
feat-security-scanning
feat-architecture-diagram
feat-edge-case-tests
chore-uv-migration (+ fix-ci-prod-deps, fix-ci-test-env)
feat-structured-logging
feat-drf-api-layer
feat-qr-payments
feat-transfer-fees
feat-kyc-foundation
```

## Commands to Run After Each Fix
```bash
# System check
python manage.py check --settings=core.settings.dev

# Lint
ruff check .
black --check --line-length 100 .
mypy .

# Tests (always with test settings)
pytest --ds=core.settings.test

# Security scan
pip-audit
ruff check --select S
bandit -r . -c pyproject.toml

# Docker build
docker build -t digital-wallet .
```

## Files to Edit (Phase 1)
| File | Fix |
|------|-----|
| `operations/views.py` | 1.1 — HTMX check + fallback redirect |
| `wallet/views.py` | 1.2 — HttpResponse instead of JsonResponse |
| `static/css/base_variables.css` | 1.3 — Uncomment light mode |
| `docker-compose.dev.yml` | 1.4 — New file |
| `core/urls.py` + `core/views.py` | 1.5 — Health endpoint |

## Files to Edit (Phase 2)
| File | Purpose |
|------|---------|
| `requirements.txt` | 2.0 — Add django-ratelimit |
| `wallet/views.py` + `accounts/views.py` | 2.0 — Add @ratelimit decorators |
| `core/settings/test.py` | CI-optimized settings |
| `requirements-dev.txt` | Dev dependencies |
| `pyproject.toml` | Ruff + Black + Mypy + Bandit config |
| `.github/workflows/ci.yml` | CI pipeline + security scan |
| `docs/ARCHITECTURE.md` | Mermaid.js diagram |
| `wallet/tests/test_edge_cases.py` | Edge case tests |

## Files to Edit (Phase 4 — DRF API, committed)
| File | Purpose |
|------|---------|
| `requirements.txt` | 4.2.1 — Add djangorestframework + drf-spectacular |
| `core/settings/base.py` | 4.2.2 — INSTALLED_APPS + REST_FRAMEWORK + SPECTACULAR_SETTINGS |
| `wallet/serializers.py` | 4.2.3 — New: Wallet/Transaction + Deposit/Withdraw/Transfer inputs |
| `wallet/api.py` | 4.2.4 — New: 5 DRF views reusing wallet/services.py |
| `wallet/api_urls.py` | 4.2.5 — New: /api/v1/* routes |
| `core/urls.py` | 4.2.5 + 4.3 — Mount api/v1/ + api/schema/ + api/docs/ |
| `wallet/tests/test_api.py` | 4.2.6 — New: auth, ownership, validation, idempotency tests |
| `accounts/models.py` | KYC status fields (future) |
| `wallet/models.py` | VirtualCard model, currency field |
| `wallet/services.py` | FX conversion, fee calculation |
