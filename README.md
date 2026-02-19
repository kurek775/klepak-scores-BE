# klepak-scores-BE

FastAPI backend for the Klepak Scores competition-management platform. Handles authentication, event/group/participant management, score recording, AI-assisted OCR, leaderboards, diploma templates, and an audit log.

---

## Tech Stack

| Component | Library / Version |
|---|---|
| Web framework | FastAPI 0.115 |
| ASGI server | Uvicorn (with standard extras) |
| ORM / schema | SQLModel 0.0.24 (SQLAlchemy + Pydantic) |
| Database | PostgreSQL 17 |
| Cache / rate limits | Redis 5 + redis-py 5.2 |
| Auth | python-jose (JWT HS256) + passlib (bcrypt) |
| AI OCR | google-generativeai 0.8 (`gemini-2.0-flash` model) |
| Rate limiting | slowapi 0.1.9 |
| Settings | pydantic-settings 2.9 |
| Tests | pytest 8.3 + httpx 0.27 |

---

## Project Structure

```
klepak-scores-BE/
├── app/
│   ├── main.py               # FastAPI app, CORS, router registration, lifespan
│   ├── config.py             # Pydantic settings (reads env vars / .env)
│   ├── database.py           # SQLAlchemy engine, get_session dependency, init_db()
│   ├── models/               # SQLModel table classes
│   │   ├── user.py           # User, UserRole enum
│   │   ├── event.py          # Event, EventStatus enum
│   │   ├── group.py          # Group
│   │   ├── group_evaluator.py# Link table: Group ↔ User
│   │   ├── participant.py    # Participant
│   │   ├── activity.py       # Activity, EvaluationType enum
│   │   ├── record.py         # Record (unique per participant+activity)
│   │   ├── age_category.py   # AgeCategory
│   │   ├── diploma_template.py
│   │   └── audit_log.py      # AuditLog
│   ├── schemas/              # Pydantic response/request schemas (separate from models)
│   │   ├── auth.py
│   │   ├── event.py
│   │   ├── activity.py
│   │   ├── age_category.py
│   │   ├── group.py
│   │   ├── leaderboard.py
│   │   ├── diploma.py
│   │   └── audit.py
│   ├── routers/              # FastAPI route handlers
│   │   ├── auth.py           # POST /auth/register, /auth/login, GET /auth/me
│   │   ├── admin.py          # GET/PATCH /admin/users
│   │   ├── events.py         # Events, age-category CRUD, CSV import
│   │   ├── groups.py         # Evaluator assignment
│   │   ├── activities.py     # Activity CRUD
│   │   ├── records.py        # Score submission + Gemini OCR
│   │   ├── analytics.py      # Leaderboard + CSV export
│   │   ├── diplomas.py       # Diploma template CRUD
│   │   └── audit.py          # GET /admin/audit-logs
│   └── core/
│       ├── security.py       # JWT encode/decode, bcrypt helpers
│       ├── dependencies.py   # get_current_user / get_current_active_user / get_current_admin
│       ├── audit.py          # log_action() helper
│       ├── cache.py          # In-memory TTLCache (currently unused — see AUDIT.md H-3)
│       ├── redis_client.py   # Redis connection singleton
│       └── limiter.py        # slowapi Limiter instance
├── tests/
│   ├── conftest.py           # In-memory SQLite engine + test client fixtures
│   ├── test_auth.py
│   ├── test_events.py
│   ├── test_analytics.py
│   └── test_records.py
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

---

## How to Run Locally

The entire stack (Postgres + API) is managed from the **root** of the repository via Docker Compose.

```bash
# From the repo root:
docker compose up --build

# API available at:  http://localhost:8000
# Swagger UI:        http://localhost:8000/docs
# ReDoc:             http://localhost:8000/redoc
```

On first startup `init_db()` creates all tables automatically. There is no separate migration step in development.

To follow API logs:

```bash
docker compose logs -f api
```

---

## Environment Variables

All variables are read by `app/config.py` via `pydantic-settings`. Supply them in `docker-compose.yml` (development) or a proper secrets manager (production).

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql://klepak:klepak_dev@localhost:5432/klepak_scores` | PostgreSQL connection string |
| `SECRET_KEY` | **yes (change in prod)** | `dev-secret-key-change-in-production` | JWT signing secret — use `openssl rand -hex 32` |
| `GEMINI_API_KEY` | yes | — | Google AI API key for OCR |
| `REDIS_URL` | no | `redis://localhost:6379` | Redis URL for caching and rate limiting |
| `CORS_ORIGINS` | no | `http://localhost:4200` | Comma-separated list of allowed CORS origins |
| `ALGORITHM` | no | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | JWT lifetime in minutes |

> **Security:** Never commit real values of `SECRET_KEY` or `GEMINI_API_KEY` to version control. See `AUDIT.md` C-1 and C-2.

---

## Running Tests

Tests use an in-memory SQLite database and the FastAPI `TestClient` — no running Docker services needed.

```bash
# Using Docker (same image, no external dependencies):
docker compose run --rm test

# Or directly with pytest (inside the BE directory, with dependencies installed):
cd klepak-scores-BE
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

Test configuration is in `pytest.ini`.

---

## Key Design Decisions

### JWT Authentication
Stateless HS256 JWTs. Tokens expire after 30 minutes. The `get_current_active_user` FastAPI dependency decodes the token and checks `User.is_active`. Admin-only endpoints add a second check for `UserRole.ADMIN`.

### Role Model
Two roles: `ADMIN` (full access) and `EVALUATOR` (scoped to assigned groups). The first registered user is automatically made ADMIN. All others start inactive and must be approved.

### Evaluator Scoping
`GroupEvaluator` is a link table between `Group` and `User`. Evaluators can only submit scores for participants in groups they are assigned to. An evaluator can be assigned to at most one group per event.

### Rate Limiting
`slowapi` enforces per-IP limits using Redis when `REDIS_URL` is set, falling back to in-memory storage. Current limits: auth endpoints 5–10/minute, image upload 20/minute, CSV import 10/minute.

### AI OCR
Images are sent to Google Gemini 2.0 Flash with a structured prompt. The model returns a JSON array of `{name, value}` pairs. These are fuzzy-matched (currently substring; see `AUDIT.md` M-7) against the participant list and returned to the frontend for human review before saving.

### Caching
Leaderboard responses are cached in Redis with a 30-second TTL. Note: cache invalidation on record write is currently broken (see `AUDIT.md` H-3).

### Audit Logging
`core/audit.py:log_action()` writes a row to `AuditLog` for every significant action (register, login failure, role change, event/evaluator deletion). Queryable via `GET /admin/audit-logs`.
