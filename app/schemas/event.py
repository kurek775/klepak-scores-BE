from datetime import datetime

from pydantic import BaseModel, Field

from app.models.event import EventStatus
from app.schemas.activity import ActivityRead
from app.schemas.group import EvaluatorRead


class ParticipantRead(BaseModel):
    id: int
    display_name: str
    external_id: str | None = None
    gender: str | None = None
    age: int | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")

    model_config = {"from_attributes": True, "populate_by_name": True}


class GroupRead(BaseModel):
    id: int
    name: str
    identifier: str
    participant_count: int = 0

    model_config = {"from_attributes": True}


class GroupDetailRead(BaseModel):
    id: int
    name: str
    identifier: str
    participants: list[ParticipantRead] = []
    evaluators: list[EvaluatorRead] = []

    model_config = {"from_attributes": True}


class EventRead(BaseModel):
    id: int
    name: str
    status: EventStatus
    created_by_id: int | None
    created_at: datetime
    group_count: int = 0
    participant_count: int = 0

    model_config = {"from_attributes": True}


class EventEvaluatorRead(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class EventDetailRead(BaseModel):
    id: int
    name: str
    status: EventStatus
    created_by_id: int | None
    created_at: datetime
    groups: list[GroupDetailRead] = []
    activities: list[ActivityRead] = []
    event_evaluators: list[EventEvaluatorRead] = []

    model_config = {"from_attributes": True}


class ImportSummary(BaseModel):
    event_id: int
    event_name: str
    groups_created: int
    participants_created: int


class MoveEvaluatorsRequest(BaseModel):
    source_event_id: int
    user_ids: list[int]


class CsvPreviewResponse(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]
    total_rows: int


class ParticipantCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=0, le=200)


class GroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str = Field(default="", max_length=255)
    participants: list[ParticipantCreate] = []


class ManualEventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    groups: list[GroupInput] = Field(min_length=1)
