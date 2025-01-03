from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.person_controller import api_router as person_router
from controllers.crew_controller import api_router as crew_router
from db import initialize_database
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup tasks
    print("Initializing database...")
    await initialize_database()
    yield  # Yield control to allow the app to start
    # Perform cleanup tasks if needed
    print("Application shutdown...")

# Initialize FastAPI app with lifespan context
app = FastAPI(
    lifespan=lifespan,
    openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(person_router, prefix="/api/persons")
app.include_router(crew_router, prefix="/api/crews")
