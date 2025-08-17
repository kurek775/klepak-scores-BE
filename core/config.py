from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseModel):
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_me")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "change_me")

settings = Settings()
