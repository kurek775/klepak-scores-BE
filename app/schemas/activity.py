from datetime import datetime

from pydantic import BaseModel

from app.models.activity import EvaluationType


class ActivityCreate(BaseModel):
    name: str
    description: str | None = None
    evaluation_type: EvaluationType
    event_id: int


class ActivityRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    evaluation_type: EvaluationType
    event_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordEntry(BaseModel):
    participant_id: int
    value_raw: str | int


class RecordCreate(BaseModel):
    value_raw: str | int
    participant_id: int
    activity_id: int


class RecordRead(BaseModel):
    id: int
    value_raw: str | int
    participant_id: int
    activity_id: int
    evaluator_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkRecordCreate(BaseModel):
    activity_id: int
    records: list[RecordEntry]
