import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.group_evaluator import GroupEvaluator

if TYPE_CHECKING:
    from app.models.group import Group


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

    assigned_groups: list["Group"] = Relationship(
        back_populates="evaluators",
        link_model=GroupEvaluator,
    )
