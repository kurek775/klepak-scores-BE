from datetime import datetime

from pydantic import BaseModel, Field

from app.models.activity import EvaluationType


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
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
    value_raw: str | int = Field(max_length=500)


class RecordCreate(BaseModel):
    value_raw: str | int = Field(max_length=500)
    participant_id: int
    activity_id: int


class RecordRead(BaseModel):
    id: int
    value_raw: str | int
    participant_id: int
    activity_id: int
    evaluator_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkRecordCreate(BaseModel):
    activity_id: int
    records: list[RecordEntry]
