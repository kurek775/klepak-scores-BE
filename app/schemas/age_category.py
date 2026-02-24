from pydantic import BaseModel, Field


class AgeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    min_age: int = Field(ge=0, le=999)
    max_age: int = Field(ge=0, le=999)


class AgeCategoryRead(BaseModel):
    id: int
    event_id: int
    name: str
    min_age: int
    max_age: int

    model_config = {"from_attributes": True}
