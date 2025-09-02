from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from utils.admin import require_admin
from db import get_db

api_router = APIRouter()


# --------- Pydantic models ---------
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
    # v /tours/{tour_id} může být crew_id NULL (uživatel je v tour, ale nemá team)
    crew_id: Optional[int] = None


# --------- Endpoints ---------


# 1) Admin: users bez tour (globální pending)
@api_router.get("/pending", response_model=List[UserOut])
async def list_users_without_tour(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    stmt = (
        select(User)
        .where(User.is_admin == False)
        .where(User.tour_id.is_(None))
        .order_by(User.created_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    users = (await db.execute(stmt)).scalars().all()
    return [UserOut.model_validate(u, from_attributes=True) for u in users]


# 2) Users v konkrétní tour (crew_id může být NULL)
@api_router.get("/tours/{tour_id}", response_model=List[UserWithCrewOut])
async def list_users_for_tour(
    tour_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [UserWithCrewOut(**row) for row in rows]


# 3) Users v tour bez týmu
@api_router.get("/tours/{tour_id}/no-crew", response_model=List[UserOut])
async def list_users_for_tour_without_crew(
    tour_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    stmt = (
        select(User)
        .where(User.is_admin == False)
        .where(User.tour_id == tour_id)
        .where(User.crew_id.is_(None))
        .order_by(User.created_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    users = (await db.execute(stmt)).scalars().all()
    return [UserOut.model_validate(u, from_attributes=True) for u in users]


@api_router.get("/tours/{tour_id}/with-crew", response_model=List[UserWithCrewOut])
async def list_users_for_tour_with_crew(
    tour_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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
        .where(User.crew_id.is_not(None))
        .order_by(User.created_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [UserWithCrewOut(**row) for row in rows]
