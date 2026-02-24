from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.diploma_template import DiplomaOrientation


class DiplomaItem(BaseModel):
    type: Literal["STATIC", "DYNAMIC"]
    key: str | None = Field(default=None, max_length=255)
    text: str | None = Field(default=None, max_length=1000)
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    fontSize: int = Field(ge=1, le=200)
    fontWeight: str = Field(default="normal", max_length=50)
    color: str = Field(max_length=50, pattern=r"^#[0-9a-fA-F]{3,8}$")
    centerH: bool = False
    centerV: bool = False


class DiplomaFont(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    data: str = Field(max_length=5_000_000)


class DiplomaTemplateCreate(BaseModel):
    name: str = Field(default="Default", min_length=1, max_length=255)
    bg_image_url: str | None = None
    orientation: DiplomaOrientation = DiplomaOrientation.LANDSCAPE
    items: list[DiplomaItem] = []
    fonts: list[DiplomaFont] = []
    default_font: str | None = Field(default=None, max_length=255)


class DiplomaTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    bg_image_url: str | None = None
    orientation: DiplomaOrientation | None = None
    items: list[DiplomaItem] | None = None
    fonts: list[DiplomaFont] | None = None
    default_font: str | None = Field(default=None, max_length=255)


class DiplomaTemplateRead(BaseModel):
    id: int
    event_id: int
    name: str
    bg_image_url: str | None
    orientation: DiplomaOrientation
    items: list[dict]
    fonts: list[dict]
    default_font: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
