from pydantic import BaseModel


class AgeCategoryCreate(BaseModel):
    name: str
    min_age: int
    max_age: int


class AgeCategoryRead(BaseModel):
    id: int
    event_id: int
    name: str
    min_age: int
    max_age: int

    model_config = {"from_attributes": True}
