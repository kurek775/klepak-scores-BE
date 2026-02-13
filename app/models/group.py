from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.participant import Participant


class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    identifier: str = Field(default="")
    event_id: int = Field(foreign_key="event.id")

    event: "Event" = Relationship(back_populates="groups")
    participants: list["Participant"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
