from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.group_evaluator import GroupEvaluator

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.participant import Participant
    from app.models.user import User


class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    identifier: str = Field(default="")
    event_id: int = Field(foreign_key="event.id", index=True)

    event: "Event" = Relationship(back_populates="groups")
    participants: list["Participant"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    evaluators: list["User"] = Relationship(
        back_populates="assigned_groups",
        link_model=GroupEvaluator,
    )
