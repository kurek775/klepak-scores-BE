from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db import async_session_maker

api_router = APIRouter()


@api_router.get("/")
async def get_persons(tour_id: int):
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                text("SELECT * FROM persons where crew_id=" + str(tour_id))
            )
            rows = result.fetchall()
            resp = [dict(row._mapping) for row in rows]
            return {"list": resp, "count": len(resp)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
