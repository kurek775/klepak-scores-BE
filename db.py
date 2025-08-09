from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text
from collections.abc import AsyncGenerator

DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mydb"

# Create an async engine
engine = create_async_engine(DATABASE_URL, echo=True)


DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mydb"

engine = create_async_engine(DATABASE_URL, echo=True)

# ✅ jediný způsob, jak tvořit session (async)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def initialize_database():
    async with engine.connect() as conn:

        def check_tables(connection):
            inspector = Inspector.from_engine(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(check_tables)
        if "persons" not in tables:
            await execute_sql_script("create_db.sql")
            await execute_sql_script("insert_mock_data.sql")


async def execute_sql_script(file_path: str):
    async with engine.connect() as conn:
        with open(file_path, "r") as sql_file:
            sql_commands = sql_file.read()
        for command in sql_commands.split(";"):
            command = command.strip()
            if command:
                async with conn.begin():
                    await conn.execute(text(command))
