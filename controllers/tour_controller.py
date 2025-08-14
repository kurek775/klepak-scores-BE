from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from db import async_session_maker
from models import Tour

api_router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# ---------- DTOs ----------
class TourDTO(BaseModel):
    id: int
    year: Optional[int] = None
    part: Optional[str] = None
    theme: Optional[str] = None
    template_id: Optional[int] = None


class TourCreate(BaseModel):
    year: int = Field(..., ge=1, le=9999)
    part: Optional[str] = None
    theme: Optional[str] = None
    template_id: Optional[int] = None


class TourUpdate(BaseModel):
    # PUT will do a partial update of only provided fields
    year: Optional[int] = Field(None, ge=1, le=9999)
    part: Optional[str] = None
    theme: Optional[str] = None
    template_id: Optional[int] = None


# ---------- Endpoints ----------
@api_router.get("/", response_model=List[TourDTO], summary="List all tours")
async def list_tours(db: AsyncSession = Depends(get_session)):
    rows = (
        (
            await db.execute(
                select(
                    Tour.id, Tour.year, Tour.part, Tour.theme, Tour.template_id
                ).order_by(Tour.year.desc(), Tour.id.asc())
            )
        )
        .mappings()
        .all()
    )
    return [TourDTO(**row) for row in rows]


@api_router.post(
    "/", response_model=TourDTO, status_code=201, summary="Create a new tour"
)
async def create_tour(payload: TourCreate, db: AsyncSession = Depends(get_session)):
    t = Tour(
        year=payload.year,
        part=payload.part,
        theme=payload.theme,
        template_id=payload.template_id,
    )
    db.add(t)
    try:
        await db.commit()
        await db.refresh(t)
        return TourDTO(
            id=t.id, year=t.year, part=t.part, theme=t.theme, template_id=t.template_id
        )
    except IntegrityError as e:
        await db.rollback()
        # e.g., invalid template_id (FK) -> 400
        raise HTTPException(status_code=400, detail=str(e))


@api_router.put("/{tour_id}", response_model=TourDTO, summary="Edit an existing tour")
async def update_tour(
    tour_id: int, payload: TourUpdate, db: AsyncSession = Depends(get_session)
):
    t = await db.get(Tour, tour_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Tour {tour_id} not found")

    # For Pydantic v1 use: data = payload.dict(exclude_unset=True)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(t, key, value)

    try:
        await db.commit()
        await db.refresh(t)
        return TourDTO(
            id=t.id, year=t.year, part=t.part, theme=t.theme, template_id=t.template_id
        )
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
