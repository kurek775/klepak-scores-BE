import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.record import Record


class EvaluationType(str, enum.Enum):
    NUMERIC_HIGH = "NUMERIC_HIGH"
    NUMERIC_LOW = "NUMERIC_LOW"
    BOOLEAN = "BOOLEAN"
    SCORE_SET = "SCORE_SET"


class Activity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None)
    evaluation_type: EvaluationType
    event_id: int = Field(foreign_key="event.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    event: "Event" = Relationship(back_populates="activities")
    records: list["Record"] = Relationship(
        back_populates="activity",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
