import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.event_evaluator import EventEvaluator

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.age_category import AgeCategory
    from app.models.group import Group
    from app.models.user import User


class EventStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    status: EventStatus = Field(default=EventStatus.DRAFT)
    config_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_by_id: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    groups: list["Group"] = Relationship(
        back_populates="event",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    activities: list["Activity"] = Relationship(
        back_populates="event",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    age_categories: list["AgeCategory"] = Relationship(
        back_populates="event",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    event_evaluators: list["EventEvaluator"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
