from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.crew import api_router as crew_router
from routers.sport import api_router as sport_router
from routers.tour import api_router as tours_router
from routers.me import api_router as me_router
from routers.auth import api_router as auth_router
from db import initialize_database
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from core.config import settings

from starlette.middleware.sessions import SessionMiddleware

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    await initialize_database()
    yield
    print("Application shutdown...")


# Initialize FastAPI app with lifespan context
app = FastAPI(
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware, secret_key=settings.SESSION_SECRET, same_site="lax"
)
# Include routers
app.include_router(crew_router, prefix="/api/tours/{tour_id}/crews")
app.include_router(sport_router, prefix="/api/tours/{tour_id}/sports")
app.include_router(tours_router, prefix="/api/tours")
app.include_router(auth_router, prefix="/auth/google")
app.include_router(me_router, prefix="/api/me")
