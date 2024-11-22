from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text
from db import engine, get_db

app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url="/api/redoc")

api_router = APIRouter(prefix="/api")


async def check_if_db_initialized() -> bool:
    """Check if the required tables exist in the database."""
    async with engine.connect() as conn:
        def check_tables(connection):
            inspector = Inspector.from_engine(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(check_tables)
        # Check for any table that indicates the database is initialized
        return "persons" in tables


async def execute_sql_script(file_path: str):
    """Executes an SQL script on the database."""
    async with engine.connect() as conn:
        with open(file_path, "r") as sql_file:
            sql_commands = sql_file.read()
        for command in sql_commands.split(";"):
            command = command.strip()
            if command:
                try:
                    async with conn.begin():  # Start a new transaction for each command
                        await conn.execute(text(command))
                except Exception as e:
                    print(f"Error executing command: {command}\n{e}")


@app.on_event("startup")
async def initialize_database():
    """Run the SQL script during application startup if the database is not initialized."""
    try:
        db_initialized = await check_if_db_initialized()
        if not db_initialized:
            print("Database is not initialized. Running initialization scripts...")
            await execute_sql_script("KLEPAK.sql")
            await execute_sql_script("mock.sql")
            print("Database initialized successfully!")
        else:
            print("Database is already initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")


@api_router.get("/persons")
async def get_persons(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM persons"))
        rows = result.fetchall()
        return {"data": [dict(row._mapping) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/tours/{tourId}/crews/{crewId}/upload-photo")
def upload_file(tourId: int, crewId: int):
    return {"message": f"Photo uploaded for tour {tourId} and crew {crewId}"}


@api_router.post("/tours/{tourId}/crews/{crewId}/sports/{sportId}/results")
def create_results(tourId: int, crewId: int, sportId: int):
    return {"message": "Results created"}


@api_router.get("/results")
def get_results():
    return {"data": "data"}


@api_router.put("/results")
def update_results():
    return {"data": "data"}


@api_router.get("/crews")
def get_crew():
    return {"data": "data"}


@api_router.get("/sports")
def get_sports():
    return {"data": "data"}


# Include the router in the main app
app.include_router(api_router)
