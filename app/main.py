import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, delete, select, text

from app.core.limiter import limiter
from app.core.redis_client import redis_client
from app.database import engine
from app.routers import activities, admin, analytics, audit, auth, diplomas, events, groups, records

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate connections
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.error("Database connection failed on startup")

    try:
        redis_client.ping()
        logger.info("Redis connection verified")
    except Exception:
        logger.warning("Redis connection failed on startup — caching will be unavailable")

    # Cleanup expired password reset tokens
    try:
        from app.models.password_reset_token import PasswordResetToken

        with Session(engine) as session:
            result = session.exec(
                delete(PasswordResetToken).where(
                    (PasswordResetToken.expires_at < datetime.now(timezone.utc))
                    | (PasswordResetToken.used == True)  # noqa: E712
                )
            )
            session.commit()
            logger.info("Cleaned up %s expired/used password reset tokens", result.rowcount)
    except Exception:
        logger.warning("Failed to cleanup expired password reset tokens")

    # Bootstrap super admin if configured and not yet in DB
    try:
        from app.config import settings
        from app.models.invitation_token import InvitationToken
        from app.models.user import User
        from app.core.email import send_onboarding_email
        import hashlib
        import secrets

        if settings.SUPER_ADMIN_EMAIL:
            with Session(engine) as session:
                sa = session.exec(
                    select(User).where(User.email == settings.SUPER_ADMIN_EMAIL)
                ).first()
                if not sa:
                    existing_inv = session.exec(
                        select(InvitationToken).where(
                            InvitationToken.email == settings.SUPER_ADMIN_EMAIL,
                            InvitationToken.used == False,  # noqa: E712
                        )
                    ).first()
                    if not existing_inv:
                        raw_token = secrets.token_urlsafe(48)
                        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                        now = datetime.now(timezone.utc)
                        inv = InvitationToken(
                            email=settings.SUPER_ADMIN_EMAIL,
                            role="SUPER_ADMIN",
                            token_hash=token_hash,
                            expires_at=now + timedelta(hours=settings.BOOTSTRAP_TOKEN_EXPIRE_HOURS),
                        )
                        session.add(inv)
                        session.commit()
                        send_onboarding_email(settings.SUPER_ADMIN_EMAIL, raw_token)
                        logger.info("Super admin onboarding email sent to %s", settings.SUPER_ADMIN_EMAIL)
                    else:
                        logger.info("Super admin invitation already pending for %s", settings.SUPER_ADMIN_EMAIL)
                else:
                    logger.info("Super admin %s already exists", settings.SUPER_ADMIN_EMAIL)
    except Exception:
        logger.warning("Failed to bootstrap super admin", exc_info=True)

    yield

    # Shutdown: cleanup
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception:
        logger.warning("Error disposing database engine")

    try:
        redis_client.close()
        logger.info("Redis connection closed")
    except Exception:
        logger.warning("Error closing Redis connection")


app = FastAPI(title="Klepak Scores API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.1fms [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


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
    db_ok = False
    redis_ok = False

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    body = {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }

    if not db_ok:
        return JSONResponse(status_code=503, content=body)
    return body
