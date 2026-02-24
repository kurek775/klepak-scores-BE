import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.group_evaluator import GroupEvaluator
from app.models.event_evaluator import EventEvaluator

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.group import Group


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    EVALUATOR = "EVALUATOR"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str
    role: UserRole = Field(default=UserRole.EVALUATOR)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    assigned_groups: list["Group"] = Relationship(
        back_populates="evaluators",
        link_model=GroupEvaluator,
    )
    assigned_events: list["Event"] = Relationship(
        link_model=EventEvaluator,
        sa_relationship_kwargs={"overlaps": "event_evaluators"},
    )
