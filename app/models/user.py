import enum
from datetime import datetime

from sqlmodel import Field, SQLModel


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EVALUATOR = "EVALUATOR"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str
    role: UserRole = Field(default=UserRole.EVALUATOR)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
