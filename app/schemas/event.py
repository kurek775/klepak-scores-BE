from datetime import datetime

from pydantic import BaseModel, Field

from app.models.event import EventStatus
from app.schemas.activity import ActivityRead
from app.schemas.group import EvaluatorRead, GroupDetailRead, GroupInput


class EventRead(BaseModel):
    id: int
    name: str
    status: EventStatus
    created_by_id: int | None
    created_at: datetime
    group_count: int = 0
    participant_count: int = 0

    model_config = {"from_attributes": True}


class EventDetailRead(BaseModel):
    id: int
    name: str
    status: EventStatus
    created_by_id: int | None
    created_at: datetime
    groups: list[GroupDetailRead] = []
    activities: list[ActivityRead] = []
    event_evaluators: list[EvaluatorRead] = []

    model_config = {"from_attributes": True}


class ImportSummary(BaseModel):
    event_id: int
    event_name: str
    groups_created: int
    participants_created: int


class CsvPreviewResponse(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]
    total_rows: int


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: EventStatus | None = None


class ManualEventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    groups: list[GroupInput] = Field(min_length=1)


class EventEvaluatorAdd(BaseModel):
    user_id: int
