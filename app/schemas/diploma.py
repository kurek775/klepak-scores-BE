from datetime import datetime

from pydantic import BaseModel

from app.models.diploma_template import DiplomaOrientation


class DiplomaTemplateCreate(BaseModel):
    name: str = "Default"
    bg_image_url: str | None = None
    orientation: DiplomaOrientation = DiplomaOrientation.LANDSCAPE
    items: list[dict] = []
    fonts: list[dict] = []
    default_font: str | None = None


class DiplomaTemplateUpdate(BaseModel):
    name: str | None = None
    bg_image_url: str | None = None
    orientation: DiplomaOrientation | None = None
    items: list[dict] | None = None
    fonts: list[dict] | None = None
    default_font: str | None = None


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
