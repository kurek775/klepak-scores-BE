from pydantic import BaseModel, Field

from app.schemas.participant import ParticipantCreate, ParticipantRead


class AssignEvaluatorRequest(BaseModel):
    user_id: int


class EvaluatorRead(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class MyGroupRead(BaseModel):
    id: int
    name: str
    identifier: str
    event_id: int
    event_name: str
    participant_count: int


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


class GroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str = Field(default="", max_length=255)
    participants: list[ParticipantCreate] = []


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str = Field(default="", max_length=255)


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=255)
