from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel, Field
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from db import async_session_maker
from models import Sport, TourSport, Tour
from sqlalchemy.dialects.postgresql import insert as pg_insert

api_router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# --- DTOs ---
class SportDTO(BaseModel):
    sport_id: int | None
    sport_name: str
    sport_metric: str


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
                Sport.metric.label("sport_metric"),
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


# --- POST payload ---
class TourSportInput(BaseModel):
    name: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)


class TourSportsCreateRequest(BaseModel):
    sports: List[TourSportInput]


@api_router.post(
    "/",
    summary="Create/link sports and add them to a tour",
    response_model=SportListResponse,
)
async def add_sports_to_tour(
    tour_id: int,
    payload: TourSportsCreateRequest,
    db: AsyncSession = Depends(get_session),
):
    # 0) Validate tour exists (avoid FK error)
    tour_row = await db.get(Tour, tour_id)
    if tour_row is None:
        raise HTTPException(status_code=404, detail=f"Tour {tour_id} not found")

    # 1) Normalize + dedupe input
    seen = set()
    inputs = []
    for item in payload.sports or []:
        n = item.name.strip()
        m = item.metric.strip()
        if n and m and n not in seen:
            inputs.append(TourSportInput(name=n, metric=m))
            seen.add(n)

    # If empty payload, just return current state (works even if tour has no sports yet)
    if not inputs:
        return await get_sports(tour_id=tour_id, db=db)

    try:
        # 2) Find existing sports by name
        names = [i.name for i in inputs]
        existing_rows = (
            (await db.execute(select(Sport).where(Sport.name.in_(names))))
            .scalars()
            .all()
        )
        existing_by_name = {s.name: s for s in existing_rows}

        # 3) Create missing sports
        to_create = [i for i in inputs if i.name not in existing_by_name]
        for i in to_create:
            db.add(Sport(name=i.name, metric=i.metric))
        if to_create:
            await db.flush()  # get IDs

            # Refresh mapping with newly created sports
            created_rows = (
                (
                    await db.execute(
                        select(Sport).where(Sport.name.in_([i.name for i in to_create]))
                    )
                )
                .scalars()
                .all()
            )
            for s in created_rows:
                existing_by_name[s.name] = s

        # 4) Link all to the tour (idempotent)
        link_values = [
            {"tour_id": tour_id, "sport_id": existing_by_name[i.name].id}
            for i in inputs
        ]
        if link_values:
            insert_stmt = pg_insert(TourSport).values(link_values)
            await db.execute(
                insert_stmt.on_conflict_do_nothing(
                    index_elements=["tour_id", "sport_id"]
                )
            )

        # 5) Commit before reading back
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # 6) Return the current list for the tour (can be empty if there were none before)
    return await get_sports(tour_id=tour_id, db=db)
