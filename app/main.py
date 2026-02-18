from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlmodel import text

from app.core.limiter import limiter
from app.database import engine, init_db
from app.models import Activity, AgeCategory, AuditLog, DiplomaTemplate, Event, Group, GroupEvaluator, Participant, Record, User  # noqa: F401 – register models before create_all
from app.routers import activities, admin, analytics, audit, auth, diplomas, events, groups, records


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Klepak Scores API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(groups.router)
app.include_router(activities.router)
app.include_router(records.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(diplomas.router)


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "ok", "database": "error"}
