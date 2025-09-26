from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pydantic import BaseModel, Field

from db import async_session_maker
from models import Sport, TourSport, Tour

api_router = APIRouter()


async def get_session():
    async with async_session_maker() as session:
        yield session


class SportDTO(BaseModel):
    sport_id: int | None
    sport_name: str
    sport_metric: str


class SportList(BaseModel):
    list: List[SportDTO]
    count: int


def _norm_name(s: str) -> str:
    return " ".join(s.split()).strip()


@api_router.get("/", response_model=SportList)
async def get_all_sports(db: AsyncSession = Depends(get_session)):
    rows = (
        (
            await db.execute(
                select(
                    Sport.id.label("sport_id"),
                    Sport.name.label("sport_name"),
                    Sport.metric.label("sport_metric"),
                ).order_by(Sport.name)
            )
        )
        .mappings()
        .all()
    )
    items = [SportDTO(**row) for row in rows]
    return SportList(list=items, count=len(items))


@api_router.get("/tour/{tour_id}", response_model=SportList)
async def get_sports(tour_id: int = Path(...), db: AsyncSession = Depends(get_session)):
    rows = (
        (
            await db.execute(
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
        )
        .mappings()
        .all()
    )
    items = [SportDTO(**row) for row in rows]
    return SportList(list=items, count=len(items))


@api_router.post(
    "/", summary="Create/update sports with unique names", response_model=SportList
)
async def upsert_sports(
    payload: List[SportDTO] = Body(...),
    db: AsyncSession = Depends(get_session),
):
    incoming: List[SportDTO] = []
    seen_names_lower: set[str] = set()
    for s in payload or []:
        name = _norm_name(s.sport_name)
        metric = _norm_name(s.sport_metric)
        if not name or not metric:
            continue

        key = name.lower()
        if key in seen_names_lower and s.sport_id is None:
            raise HTTPException(
                status_code=400, detail=f"Duplicate sport name in payload: '{name}'"
            )
        seen_names_lower.add(key)

        incoming.append(
            SportDTO(sport_id=s.sport_id, sport_name=name, sport_metric=metric)
        )

    to_update = [s for s in incoming if s.sport_id is not None]
    to_create = [s for s in incoming if s.sport_id is None]

    create_names_lower = {s.sport_name.lower() for s in to_create}
    if create_names_lower:
        existing = (
            await db.execute(
                select(Sport.id, Sport.name).where(
                    func.lower(Sport.name).in_(create_names_lower)
                )
            )
        ).all()
        if existing:
            collide = [name for (_, name) in existing]
            raise HTTPException(
                status_code=409, detail={"code": "name_exists", "names": collide}
            )

    if to_update:
        desired = {int(s.sport_id): s.sport_name for s in to_update}
        desired_lower = {nid: name.lower() for nid, name in desired.items()}
        rows = (
            await db.execute(
                select(Sport.id, Sport.name).where(
                    func.lower(Sport.name).in_(list(desired_lower.values()))
                )
            )
        ).all()
        for row_id, row_name in rows:
            for upd_id, nm_lower in desired_lower.items():
                if row_name.lower() == nm_lower and row_id != upd_id:
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "name_exists", "names": [desired[upd_id]]},
                    )

    try:
        if to_update:
            ids = [int(s.sport_id) for s in to_update]
            db_rows = (
                (await db.execute(select(Sport).where(Sport.id.in_(ids))))
                .scalars()
                .all()
            )
            by_id = {r.id: r for r in db_rows}
            missing = [i for i in ids if i not in by_id]
            if missing:
                raise HTTPException(
                    status_code=404, detail=f"Sports not found: {missing}"
                )

            for s in to_update:
                row = by_id[int(s.sport_id)]
                row.name = s.sport_name
                row.metric = s.sport_metric

        if to_create:
            await db.execute(
                pg_insert(Sport).values(
                    [
                        {"name": s.sport_name, "metric": s.sport_metric}
                        for s in to_create
                    ]
                )
            )

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail={"code": "name_exists"})

    return await get_all_sports(db)
