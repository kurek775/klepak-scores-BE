from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mydb"

# Create an async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session maker
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to get a session
async def get_db():
    async with SessionLocal() as session:
        yield session
