# klepak-scores-BE

FastAPI backend for the Klepak Scores competition-management platform. Handles authentication, event/group/participant management, score recording, AI-assisted OCR, leaderboards, diploma templates, and an audit log.

## Tech Stack

| Component | Library / Version |
|---|---|
| Web framework | FastAPI 0.115 |
| ASGI server | Uvicorn 0.34 (with standard extras) |
| ORM / schema | SQLModel 0.0.24 (SQLAlchemy + Pydantic) |
| Database | PostgreSQL 17 |
| Migrations | Alembic 1.14 |
| Cache / rate limits | Redis 7 + redis-py 5.2 |
| Auth | python-jose (JWT HS256) + passlib (bcrypt) |
| AI OCR | google-generativeai 0.8 (`gemini-2.0-flash`) |
| Rate limiting | slowapi 0.1.9 |
| Settings | pydantic-settings 2.9 |
| Tests | pytest 8.3 + httpx 0.27 |
| Runtime | Python 3.13-slim (Docker) |

## Key Features

- **Authentication** — JWT HS256, registration, login, invitation-based onboarding, password reset (token + SMTP)
- **Role-based access** — Super Admin, Admin, Evaluator roles with scoped permissions
- **Events** — CRUD, CSV import with column mapping & preview, age categories
- **Evaluator pools** — Event-level evaluator pool, group assignment requires pool membership
- **Scoring** — Single & bulk record submission, upsert semantics (unique per participant + activity)
- **AI OCR** — Image → Gemini 2.0 Flash → fuzzy-matched participant scores for human review
- **Leaderboard** — Ranked results with tie handling, Redis-cached (300s TTL), CSV export
- **Diploma templates** — Multi-template CRUD per event with JSON-based layout
- **Audit log** — Tracks all significant actions, paginated admin query endpoint
- **Rate limiting** — Per-IP via slowapi + Redis (auth: 5-10/min, OCR: 20/min, CSV: 10/min)
- **Health check** — `GET /health` reports DB + Redis status

## Data Model

```
User ──< EventEvaluator >── Event
User ──< GroupEvaluator >── Group
User ──< InvitationToken
User ──< PasswordResetToken
User ──< AuditLog

Event ──< Group ──< Participant
Event ──< Activity
Event ──< AgeCategory
Event ──< DiplomaTemplate

Participant + Activity ──< Record (unique constraint)
```

**13 models:** User, Event, Group, Participant, Activity, Record, GroupEvaluator, EventEvaluator, AgeCategory, DiplomaTemplate, AuditLog, PasswordResetToken, InvitationToken

## API Endpoints

| Router | Prefix | Key Endpoints |
|---|---|---|
| **auth** | `/auth` | `POST /register`, `POST /login`, `GET /me`, `POST /forgot-password`, `POST /reset-password`, `GET /validate-invitation`, `POST /accept-invitation` |
| **admin** | `/admin` | `GET /users`, `PATCH /users/{id}`, `POST /invitations`, `GET /invitations`, `DELETE /invitations/{id}` |
| **events** | `/events` | `GET /`, `POST /manual`, `GET /{id}`, `DELETE /{id}`, `POST /preview-csv`, `POST /import`, age-category CRUD, evaluator pool CRUD, `POST /{id}/evaluators/move` |
| **groups** | `/groups` | `GET /my-groups`, evaluator assignment CRUD per group |
| **activities** | — | `POST /activities`, `GET /events/{id}/activities`, `DELETE /activities/{id}` |
| **records** | — | `POST /records`, `POST /records/bulk`, `POST /records/process-image`, `GET /activities/{id}/records` |
| **analytics** | — | `GET /events/{id}/leaderboard`, `GET /events/{id}/export-csv` |
| **diplomas** | — | `GET/POST /events/{id}/diplomas`, `GET/PUT/DELETE /events/{id}/diplomas/{tid}` |
| **audit** | — | `GET /admin/audit-logs` (paginated) |

Interactive docs: `/docs` (Swagger UI) or `/redoc` (ReDoc).

## Project Structure

```
klepak-scores-BE/
├── app/
│   ├── main.py               # FastAPI app, CORS, middleware, lifespan, router registration
│   ├── config.py             # Pydantic settings (reads env vars / .env)
│   ├── database.py           # SQLAlchemy engine, get_session, init_db()
│   ├── models/               # 13 SQLModel table classes
│   │   ├── user.py           # User, UserRole enum (SUPER_ADMIN, ADMIN, EVALUATOR)
│   │   ├── event.py          # Event, EventStatus enum
│   │   ├── group.py
│   │   ├── participant.py
│   │   ├── activity.py       # Activity, EvaluationType enum
│   │   ├── record.py         # Record (unique per participant+activity)
│   │   ├── group_evaluator.py
│   │   ├── event_evaluator.py    # Phase 8: event-level evaluator pool
│   │   ├── age_category.py
│   │   ├── diploma_template.py
│   │   ├── audit_log.py
│   │   ├── password_reset_token.py  # Phase 8: token-based password reset
│   │   └── invitation_token.py      # Phase 8: invitation-based registration
│   ├── schemas/              # Pydantic response/request schemas
│   │   ├── auth.py
│   │   ├── event.py
│   │   ├── activity.py
│   │   ├── age_category.py
│   │   ├── group.py
│   │   ├── leaderboard.py
│   │   ├── diploma.py
│   │   └── audit.py
│   ├── routers/              # FastAPI route handlers (9 routers)
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── events.py
│   │   ├── groups.py
│   │   ├── activities.py
│   │   ├── records.py
│   │   ├── analytics.py
│   │   ├── diplomas.py
│   │   └── audit.py
│   └── core/
│       ├── security.py       # JWT encode/decode, bcrypt helpers
│       ├── dependencies.py   # get_current_user, get_current_active_user, get_current_admin
│       ├── audit.py          # log_action() helper
│       ├── email.py          # SMTP / dev-console email sender
│       ├── redis_client.py   # Redis connection singleton
│       └── limiter.py        # slowapi Limiter instance
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/             # 7 versioned migration files
│       ├── 001_initial_schema.py
│       ├── 002_diploma_multi_template.py
│       ├── 003_event_evaluator.py
│       ├── 004_password_reset_token.py
│       ├── 005_add_foreign_key_indexes.py
│       ├── 006_invitation_token.py
│       └── 007_cascade_and_indexes.py
├── tests/
│   ├── conftest.py           # In-memory SQLite engine + test client fixtures
│   ├── test_auth.py          # 9 tests
│   ├── test_events.py        # 10 tests
│   ├── test_records.py       # 6 tests
│   └── test_analytics.py     # 6 tests
├── alembic.ini
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

## Environment Variables

All variables are read by `app/config.py` (pydantic-settings) or `os.getenv()`. Supply them via `docker-compose.yml` (dev) or a secrets manager (production).

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql://klepak:klepak_dev@localhost:5432/klepak_scores` | PostgreSQL connection string |
| `SECRET_KEY` | **yes** | — | JWT signing secret (`openssl rand -hex 32`) |
| `GEMINI_API_KEY` | yes | — | Google AI API key for OCR |
| `REDIS_URL` | no | `redis://localhost:6379` | Redis URL for caching and rate limiting |
| `CORS_ORIGINS` | no | `http://localhost:4200` | Comma-separated allowed CORS origins |
| `ALGORITHM` | no | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | JWT lifetime in minutes |
| `SMTP_HOST` | no | `""` (dev mode) | SMTP server host (empty = print emails to console) |
| `SMTP_PORT` | no | `587` | SMTP port |
| `SMTP_USER` | no | `""` | SMTP username |
| `SMTP_PASSWORD` | no | `""` | SMTP password |
| `SMTP_FROM` | no | `""` | Sender email address |
| `SMTP_USE_TLS` | no | `true` | Use STARTTLS (port 587) |
| `SMTP_USE_SSL` | no | `false` | Use implicit SSL (port 465) |
| `FRONTEND_URL` | no | `http://localhost:4200` | Base URL for links in emails |
| `SUPER_ADMIN_EMAIL` | no | `""` | Auto-create invitation for this email on startup |
| `INVITATION_EXPIRE_DAYS` | no | `7` | Invitation token lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES` | no | `60` | Password reset token lifetime |

## Running Locally

The full stack (Postgres, Redis, Mailpit, API) is managed from the **repo root** via Docker Compose:

```bash
# From the repo root:
docker compose up --build

# API:          http://localhost:8001
# Swagger UI:   http://localhost:8001/docs
# ReDoc:        http://localhost:8001/redoc
# Mailpit UI:   http://localhost:8025
```

Migrations run automatically via the `migrate` service before the API starts.

## Database Migrations

Migrations are managed with **Alembic** (7 versioned files in `alembic/versions/`).

```bash
# Run migrations (inside the BE directory):
alembic upgrade head

# Create a new migration:
alembic revision -m "description_here"

# Check current revision:
alembic current
```

In Docker Compose, migrations run automatically via the `migrate` service before the API starts.

## Running Tests

Tests use an in-memory SQLite database and the FastAPI `TestClient` — no running Docker services needed.

```bash
# Via Docker Compose (from repo root):
docker compose run --rm test

# Or directly with pytest:
cd klepak-scores-BE
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

31 tests across 4 test files. Configuration in `pytest.ini`.

## Key Design Decisions

- **JWT Authentication** — Stateless HS256 tokens, 30-minute expiry. `get_current_active_user` dependency decodes and verifies `is_active`.
- **Three-tier roles** — `SUPER_ADMIN` (user management), `ADMIN` (full event access), `EVALUATOR` (scoped to assigned groups).
- **Evaluator scoping** — Evaluators must be in the event pool (`EventEvaluator`) before group assignment (`GroupEvaluator`). One group per event max.
- **Invitation-based registration** — Admins create `InvitationToken` entries; users register via invitation link. Super-admin bootstrap on first startup.
- **Password reset** — SHA-256 hashed tokens with 60-minute expiry. SMTP for production, console output for development.
- **AI OCR** — Images sent to Gemini 2.0 Flash with structured prompt. Returns `{name, value}` pairs, fuzzy-matched against participants for human review.
- **Leaderboard caching** — Redis-cached with 300s TTL, invalidated on record writes.
- **Audit logging** — `log_action()` writes to `AuditLog` for significant actions. Paginated admin query endpoint.
- **Cascade deletes** — DB-level `ON DELETE CASCADE` for all parent-child relationships (migration 007).
