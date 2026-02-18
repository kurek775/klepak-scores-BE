from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.participant import Participant
    from app.models.user import User


class Record(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("participant_id", "activity_id", name="uq_record_participant_activity"),
    )

    id: int | None = Field(default=None, primary_key=True)
    value_raw: str
    participant_id: int = Field(foreign_key="participant.id")
    activity_id: int = Field(foreign_key="activity.id")
    evaluator_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    participant: "Participant" = Relationship()
    activity: "Activity" = Relationship(back_populates="records")
    evaluator: "User" = Relationship()
