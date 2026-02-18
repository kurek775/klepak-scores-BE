from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.group import Group


class Participant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    display_name: str
    external_id: str | None = Field(default=None)
    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))
    gender: str | None = Field(default=None)
    age: int | None = Field(default=None)
    group_id: int = Field(foreign_key="group.id")

    group: "Group" = Relationship(back_populates="participants")
