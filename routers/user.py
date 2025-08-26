# routers/users.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel , ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from models import User, Crew, crew_leaders
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
    crew_id: int  


@api_router.get("", response_model=List[UserWithCrewOut])
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
            Crew.id.label("crew_id"),
        )
        .select_from(User)
        .join(crew_leaders, crew_leaders.c.user_id == User.id)
        .join(Crew, Crew.id == crew_leaders.c.crew_id)
        .where(User.is_admin == False)           
        .where(Crew.tour_id == tour_id)           
        .order_by(User.created_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )

    res = await db.execute(stmt)
    rows = res.mappings().all()
    return [UserWithCrewOut(**row) for row in rows]


@api_router.get("/pending", response_model=list[UserOut])
async def list_pending_users_for_tour(
    tour_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin_ok: bool = Depends(require_admin),
):
    assigned_exists = (
        select(crew_leaders.c.user_id)
        .join(Crew, Crew.id == crew_leaders.c.crew_id)
        .where(Crew.tour_id == tour_id)
        .where(crew_leaders.c.user_id == User.id)
    ).exists()

    stmt = (
        select(User)
        .where(User.is_admin == False)
        .where(~assigned_exists) 
        .order_by(User.created_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )

    res = await db.execute(stmt)
    users = res.scalars().all() 
    return [UserOut.model_validate(u, from_attributes=True) for u in users]