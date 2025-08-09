from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from db import async_session_maker
from models import Sport, TourSport

api_router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# --- DTOs ---
class SportDTO(BaseModel):
    sport_id: int
    sport_name: str


class SportListResponse(BaseModel):
    list: List[SportDTO]
    count: int


@api_router.get("/", summary="List sports for a tour", response_model=SportListResponse)
async def get_sports(tour_id: int, db: AsyncSession = Depends(get_session)):
    try:
        stmt = (
            select(
                Sport.id.label("sport_id"),
                Sport.name.label("sport_name"),
            )
            .join(TourSport, TourSport.sport_id == Sport.id)
            .where(TourSport.tour_id == tour_id)
            .order_by(Sport.name)
            .distinct()
        )

        # Use mappings() to get dict-like rows
        rows = (await db.execute(stmt)).mappings().all()
        items = [SportDTO(**row) for row in rows]
        return SportListResponse(list=items, count=len(items))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
