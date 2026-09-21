# Development Guide

Local setup, running, testing, and code quality for Digital Wallet Dashboard.

---

## Prerequisites

- Python `3.12`
- Redis
- Virtual environment support (`uv` recommended)

---

## Setup

### Option 1: Use The Project Setup Script

```bash
source .env_digital_wallet/bin/activate
./scripts/setup.sh
```

### Option 2: Manual Setup With uv (Recommended)

```bash
uv venv .venv --python 3.12
uv pip install -r requirements-dev.txt
cp .env.example .env
pre-commit install
.venv/bin/python manage.py migrate --settings=core.settings.dev
.venv/bin/python manage.py createsuperuser --settings=core.settings.dev
.venv/bin/python manage.py runserver 8500 --settings=core.settings.dev
```

### Option 3: Manual Setup With venv + pip

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

> Both `.venv` (uv) and `.env_digital_wallet` (pip) are gitignored. CI uses
> `uv` with `requirements.lock`.

---

## Dependency Rule

CI installs **exclusively** from `requirements.lock`. Any branch that touches
`requirements.txt` or `requirements-dev.txt` must recompile the lock in the
same branch:

```bash
uv pip compile requirements-dev.txt -o requirements.lock
```

---

## Environment Variables

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

1. Create or activate a virtual environment (`.venv` or `.env_digital_wallet`)
2. Update `.env`
3. Run migrations
4. Create a superuser
5. Start Django on port `8500`
6. Start Redis and Celery if you want statement generation
7. Run tests before committing

---

## Testing

Tests run against `core.settings.test` (in-memory SQLite, fast hashers,
eager Celery). Always pass `--ds=core.settings.test`:

### Run All Tests

```bash
pytest --ds=core.settings.test
```

### Run By App

```bash
pytest accounts/tests/ --ds=core.settings.test -v
pytest wallet/tests/ --ds=core.settings.test -v
pytest operations/tests/ --ds=core.settings.test -v
pytest analytics/tests/ --ds=core.settings.test -v
pytest core/tests/ --ds=core.settings.test -v
```

### Coverage

```bash
pytest --ds=core.settings.test --cov
```

### Django System Check

```bash
python manage.py check --settings=core.settings.dev
```

---

## Code Quality

### Formatting & Linting

```bash
pre-commit run --all-files
black --line-length 100 .
ruff check .
mypy .
flake8 --max-line-length 100 --extend-ignore E203,W503,E501
isort --profile black --line-length 100 .
```

Pre-commit hooks are installed automatically via `setup.sh` or `pre-commit install`. They run on every commit.
