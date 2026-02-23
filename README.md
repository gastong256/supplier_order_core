# Supplier Order Core

A production-ready FastAPI service skeleton.

## Stack

| Layer | Library |
|---|---|
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 (async) |
| Driver | asyncpg (PostgreSQL) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | python-jose + passlib/bcrypt |
| Logging | structlog |
| Testing | pytest + pytest-asyncio + httpx |
| Linting | ruff + mypy |

## Project Structure

```
app/
├── api/
│   ├── deps.py              # Shared FastAPI dependencies (DB session, auth)
│   └── v1/
│       ├── router.py        # Aggregate v1 routes
│       └── endpoints/       # One file per domain resource
├── core/
│   ├── config.py            # Pydantic-settings (reads .env)
│   ├── exceptions.py        # Domain exceptions + HTTP shortcuts
│   ├── logging.py           # structlog setup
│   └── security.py          # JWT + password hashing
├── db/
│   ├── base.py              # DeclarativeBase + mixins (UUID PK, timestamps)
│   └── session.py           # Async engine + session factory + get_db
├── models/                  # SQLAlchemy ORM models (import all in __init__.py)
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic layer
├── repositories/            # Data-access layer (raw DB queries)
└── main.py                  # App factory + middleware + exception handlers
alembic/                     # DB migrations
tests/                       # pytest test suite (mirrors app/ structure)
```

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install uv
uv pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and DATABASE_URL at minimum
```

### 3. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

### 4. Run locally

```bash
# Assumes PostgreSQL is already running
alembic upgrade head
uvicorn app.main:app --reload
```

### 5. Run tests

```bash
pytest
```

## Adding a New Domain Resource

1. Create `app/models/my_resource.py` — SQLAlchemy model extending `BaseModel`
2. Import it in `app/models/__init__.py` (Alembic autogenerate picks it up)
3. Create `app/schemas/my_resource.py` — Pydantic request/response schemas
4. Create `app/repositories/my_resource.py` — DB queries
5. Create `app/services/my_resource.py` — business logic calling the repository
6. Create `app/api/v1/endpoints/my_resource.py` — FastAPI router
7. Register the router in `app/api/v1/router.py`
8. Generate and apply migration: `alembic revision --autogenerate -m "add my_resource"`

## Migrations

```bash
# Generate from model changes
alembic revision --autogenerate -m "describe the change"

# Apply
alembic upgrade head

# Rollback one
alembic downgrade -1
```
