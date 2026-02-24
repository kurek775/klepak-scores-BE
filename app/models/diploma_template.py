import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DiplomaOrientation(str, enum.Enum):
    LANDSCAPE = "LANDSCAPE"
    PORTRAIT = "PORTRAIT"


class DiplomaTemplate(SQLModel, table=True):
    __tablename__ = "diplomatemplate"
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    name: str = Field(default="Default")
    bg_image_url: str | None = Field(default=None)
    orientation: DiplomaOrientation = Field(default=DiplomaOrientation.PORTRAIT)
    items: list | None = Field(default=None, sa_column=Column(JSON))
    fonts: list | None = Field(default=None, sa_column=Column(JSON))
    default_font: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
