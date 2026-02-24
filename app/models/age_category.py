from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.event import Event


class AgeCategory(SQLModel, table=True):
    __tablename__ = "age_category"
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    name: str
    min_age: int = Field(default=0)
    max_age: int = Field(default=999)

    event: "Event" = Relationship(back_populates="age_categories")
