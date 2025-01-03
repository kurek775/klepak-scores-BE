from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.person_controller import api_router as person_router
from controllers.crew_controller import api_router as crew_router
from db import initialize_database

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
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

# Initialize database during startup
@app.on_event("startup")
async def startup_event():
    await initialize_database()

# Include routers
app.include_router(person_router, prefix="/api/persons")
app.include_router(crew_router, prefix="/api/crews")
