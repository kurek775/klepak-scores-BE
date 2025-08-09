from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ---- Base DTOs ----


class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None
    is_admin: bool = False


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CrewBase(BaseModel):
    number: Optional[int] = None


class CrewCreate(CrewBase):
    pass


class CrewRead(CrewBase):
    id: int
    # just IDs of leaders to keep it light; or embed UserRead if you prefer
    leader_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)


class PersonBase(BaseModel):
    name: Optional[str] = None
    crew_id: Optional[int] = None


class PersonCreate(PersonBase):
    pass


class PersonRead(PersonBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SportBase(BaseModel):
    name: str
    metric: Optional[str] = None


class SportCreate(SportBase):
    pass


class SportRead(SportBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TemplateBase(BaseModel):
    text_position: Optional[str] = None


class TemplateCreate(TemplateBase):
    bg_image: Optional[bytes] = None
    font: Optional[bytes] = None


class TemplateRead(TemplateBase):
    id: int
    # omit large binaries by default

    model_config = ConfigDict(from_attributes=True)


class TourBase(BaseModel):
    year: Optional[int] = None
    part: Optional[str] = None
    theme: Optional[str] = None
    template_id: Optional[int] = None


class TourCreate(TourBase):
    pass


class TourRead(TourBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TourSportBase(BaseModel):
    tour_id: int
    sport_id: int
    position: Optional[int] = None
    is_optional: bool = False


class TourSportCreate(TourSportBase):
    pass


class TourSportRead(TourSportBase):
    model_config = ConfigDict(from_attributes=True)


class ResultBase(BaseModel):
    tour_id: int
    sport_id: int
    person_id: int
    score: Optional[float] = None


class ResultCreate(ResultBase):
    pass


class ResultRead(ResultBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
