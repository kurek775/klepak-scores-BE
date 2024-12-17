from fastapi import FastAPI, APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text
from db import engine, get_db
from dotenv import load_dotenv
import os
import utils.openai as fileHelper
import openai
load_dotenv()

app = FastAPI(
    openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url="/api/redoc"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)
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
async def upload_file(tourId: int, crewId: int, file: UploadFile = File(...)):
    """
    Endpoint to upload a photo for a specific tour and crew.
    """
    image = await fileHelper.encode_image(file)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Read data in this image, there will be names on the left side and scores on right and on top there will be sport i need you to return it to me in JSON format {sport:,results:[{name:,score:}]} please just return JSON format no extra text, if the image doesnt look like i described return to me string 'false'",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                    },
                ],
            },
        ],
    )
    res = completion.choices[0].message.content
    if res == 'false':
        return {"message": 'Obrázek je ve špatném formátu.'}

    return {"message": fileHelper.format_openai_resp(res)}


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
