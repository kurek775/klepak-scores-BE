from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db import async_session_maker
from pydantic import BaseModel

api_router = APIRouter()


class SportDTO(BaseModel):
    sport_id: int
    sport_name: str


@api_router.get("/", summary="List sports for a tour")
async def get_sports(tour_id: int):
    async with async_session_maker() as db:
        try:
            query = text(
                """
                SELECT DISTINCT
                    s.id   AS sport_id,
                    s.name AS sport_name
                FROM tour_sports ts
                JOIN sports s ON s.id = ts.sport_id
                WHERE ts.tour_id = :tour_id
                ORDER BY s.name
            """
            )
            result = await db.execute(query, {"tour_id": tour_id})
            rows = [dict(row._mapping) for row in result.fetchall()]
            return {"list": rows, "count": len(rows)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
