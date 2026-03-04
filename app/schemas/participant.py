from pydantic import BaseModel, Field


class ParticipantRead(BaseModel):
    id: int
    display_name: str
    external_id: str | None = None
    gender: str | None = None
    age: int | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ParticipantCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=0, le=200)


class ParticipantUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=0, le=200)


class ParticipantMoveRequest(BaseModel):
    group_id: int
