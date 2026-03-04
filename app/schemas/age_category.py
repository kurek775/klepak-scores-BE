from pydantic import BaseModel, Field, model_validator


class AgeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    min_age: int = Field(ge=0, le=999)
    max_age: int = Field(ge=0, le=999)

    @model_validator(mode="after")
    def check_age_range(self):
        if self.min_age > self.max_age:
            raise ValueError("min_age must be less than or equal to max_age")
        return self


class AgeCategoryRead(BaseModel):
    id: int
    event_id: int
    name: str
    min_age: int
    max_age: int

    model_config = {"from_attributes": True}
