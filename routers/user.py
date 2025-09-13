from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models import User
from utils.admin import require_admin
from db import get_db

api_router = APIRouter()


class UserOut(BaseModel):
    id: int
    sub: Optional[str] = None
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None
    is_admin: bool
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class UserWithCrewOut(UserOut):
    crew_id: Optional[int] = None


@api_router.get("/pending", response_model=List[UserOut])
async def list_users_without_tour(
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    stmt = (
        select(User)
        .where(User.is_admin == False)
        .where(User.tour_id.is_(None))
        .order_by(User.created_at.desc().nullslast())
    )
    users = (await db.execute(stmt)).scalars().all()
    return [UserOut.model_validate(u, from_attributes=True) for u in users]


class PendingUserUpdate(BaseModel):
    id: int
    tour_id: Optional[int] = None


@api_router.put("/pending", response_model=List[UserOut])
async def update_users_without_tour(
    updates: List[PendingUserUpdate] = Body(...),
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    if not updates:
        return {"updated": 0}

    ids = [u.id for u in updates]
    users = await db.execute(select(User).where(User.id.in_(ids)))
    by_id = {u.id: u for u in users.scalars().all()}

    missing = [i for i in ids if i not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail=f"Users not found: {missing}")

    updated = 0
    for item in updates:
        u = by_id[item.id]
        if u.is_admin:
            raise HTTPException(status_code=400, detail=f"User {u.id} is admin")

        u.tour_id = item.tour_id
        updated += 1

    await db.commit()
    return await list_users_without_tour(db)


@api_router.get("/tours/{tour_id}", response_model=List[UserWithCrewOut])
async def list_users_for_tour(
    tour_id: int,
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    stmt = (
        select(
            User.id,
            User.sub,
            User.email,
            User.name,
            User.picture_url,
            User.is_admin,
            User.created_at,
            User.last_login_at,
            User.crew_id.label("crew_id"),
        )
        .where(User.is_admin == False)
        .where(User.tour_id == tour_id)
        .order_by(User.created_at.desc().nullslast())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [UserWithCrewOut(**row) for row in rows]


@api_router.put("/tours/{tour_id}", response_model=List[UserWithCrewOut])
async def update_users_without_crew(
    tour_id: int,
    updates: List[UserWithCrewOut] = Body(...),
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    if not updates:
        return {"updated": 0}

    ids = [u.id for u in updates]
    users = await db.execute(
        select(User).where(User.tour_id == tour_id).where(User.id.in_(ids))
    )
    by_id = {u.id: u for u in users.scalars().all()}

    missing = [i for i in ids if i not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail=f"Users not found: {missing}")

    updated = 0
    for item in updates:
        u = by_id[item.id]
        if u.is_admin:
            raise HTTPException(status_code=400, detail=f"User {u.id} is admin")

        u.crew_id = item.crew_id
        updated += 1

    await db.commit()
    return await list_users_for_tour(tour_id, db)
