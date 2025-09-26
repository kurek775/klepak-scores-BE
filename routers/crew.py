from fastapi import APIRouter, HTTPException, UploadFile, File
from utils.openai import encode_image, format_openai_resp
from sqlalchemy import text
from db import async_session_maker
import os
import openai
from typing import List
from fastapi import APIRouter, HTTPException, Path, Query, Body, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, and_, func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models import Person, Sport, Tour, TourSport, Result
from db import get_db

api_router = APIRouter()


# --------- DTOs ----------
class ResultFromFrontend(BaseModel):
    person_id: int
    score: float


@api_router.put(
    "/{crew_id}/sport/{sport_id}",
    summary="Save results for given crew, sport and tour (bulk upsert)",
)
async def save_results_from_frontend(
    crew_id: int = Path(...),
    sport_id: int = Path(...),
    tour_id: int = Path(...),
    results: List[ResultFromFrontend] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        exists_ts = await db.scalar(
            select(func.count())
            .select_from(TourSport)
            .where(and_(TourSport.tour_id == tour_id, TourSport.sport_id == sport_id))
        )
        if not exists_ts:
            raise HTTPException(
                status_code=404,
                detail="Sport is not part of the specified tour.",
            )

        # 2) Restrict to persons that belong to the crew
        crew_person_ids = {
            pid
            for (pid,) in (
                await db.execute(select(Person.id).where(Person.crew_id == crew_id))
            ).all()
        }
        if not crew_person_ids:
            raise HTTPException(status_code=404, detail="Crew has no persons.")

        # 3) Prepare rows for upsert (tour_id, sport_id, person_id is UNIQUE)
        rows = [
            {
                "tour_id": tour_id,
                "sport_id": sport_id,
                "person_id": r.person_id,
                "score": r.score,
            }
            for r in results
            if r.person_id in crew_person_ids
        ]
        if not rows:
            return {"status": "noop", "updated": 0, "skipped": len(results)}

        # 4) Bulk UPSERT (PostgreSQL)
        stmt = (
            pg_insert(Result)
            .values(rows)
            .on_conflict_do_update(
                index_elements=[Result.tour_id, Result.sport_id, Result.person_id],
                set_={"score": pg_insert(Result).excluded.score},
            )
        )
        await db.execute(stmt)
        await db.commit()
        return {
            "status": "success",
            "updated": len(rows),
            "skipped": len(results) - len(rows),
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ---- incoming row from FE (extra tolerated/ignored) ----
class FrontendResultRow(BaseModel):
    person_id: int
    score: int  # can be "074", "01", number, etc.
    model_config = ConfigDict(extra="ignore")  # ignore person_name, metric, etc.


def normalize_score(value: int) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".")
    if s == "":
        return 0.0
    try:
        return float(Decimal(s))
    except (InvalidOperation, ValueError):
        return 0.0


@api_router.post(
    "/{crew_id}/sport/{sport_id}",
    summary="Create/update results for given crew, sport and tour (bulk upsert)",
)
async def create_results_from_frontend(
    crew_id: int = Path(...),
    sport_id: int = Path(...),
    tour_id: int = Path(...),
    results: List[FrontendResultRow] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1) Validate sport belongs to the tour
        exists_ts = (
            await db.execute(
                select(1)
                .select_from(TourSport)
                .where(
                    and_(TourSport.tour_id == tour_id, TourSport.sport_id == sport_id)
                )
                .limit(1)
            )
        ).first() is not None
        if not exists_ts:
            raise HTTPException(
                status_code=404, detail="Sport is not part of the specified tour."
            )

        # 2) Only allow persons from this crew
        crew_person_ids = {
            pid
            for (pid,) in (
                await db.execute(select(Person.id).where(Person.crew_id == crew_id))
            ).all()
        }
        if not crew_person_ids:
            raise HTTPException(status_code=404, detail="Crew has no persons.")

        # 3) Build rows for upsert, coerce score safely
        rows = []
        for r in results:
            if r.person_id not in crew_person_ids:
                # skip foreign person_id silently
                continue
            rows.append(
                {
                    "tour_id": tour_id,
                    "sport_id": sport_id,
                    "person_id": r.person_id,
                    "score": normalize_score(r.score),
                }
            )

        if not rows:
            return {"status": "noop", "created_or_updated": 0, "skipped": len(results)}

        # 4) Bulk UPSERT (unique on tour_id, sport_id, person_id)
        stmt = (
            pg_insert(Result)
            .values(rows)
            .on_conflict_do_update(
                index_elements=[Result.tour_id, Result.sport_id, Result.person_id],
                set_={"score": pg_insert(Result).excluded.score},
            )
        )
        await db.execute(stmt)
        await db.commit()

        return {
            "status": "success",
            "created_or_updated": len(rows),
            "skipped": len(results) - len(rows),
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get(
    "/{crew_id}/sport/{sport_id}",
    summary="Get persons with result for a given crew, sport and tour",
)
async def get_crew_results(
    crew_id: int, sport_id: int, tour_id: int, db: AsyncSession = Depends(get_db)
):
    try:
        exists_ts = (
            await db.execute(
                select(1)
                .select_from(TourSport)
                .where(
                    and_(
                        TourSport.tour_id == tour_id,
                        TourSport.sport_id == sport_id,
                    )
                )
                .limit(1)
            )
        ).first() is not None

        if not exists_ts:
            raise HTTPException(
                status_code=404,
                detail="Sport is not part of the specified tour.",
            )

        R = aliased(Result)
        stmt = (
            select(
                Person.id.label("person_id"),
                Person.name.label("person_name"),
                R.id.label("result_id"),
                R.score.label("score"),
                literal(tour_id).label("tour_id"),
                Sport.id.label("sport_id"),
                Sport.name.label("sport_name"),
                Sport.metric.label("metric"),
            )
            .select_from(Person)
            .outerjoin(
                R,
                and_(
                    R.person_id == Person.id,
                    R.tour_id == tour_id,
                    R.sport_id == sport_id,
                ),
            )
            .join(Sport, Sport.id == sport_id)
            .where(Person.crew_id == crew_id)
            .order_by(Person.name)
        )

        rows = (await db.execute(stmt)).mappings().all()
        return {"list": [dict(r) for r in rows], "count": len(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @api_router.post("/{crew_id}/upload-photo")
# async def upload_file(tour_id: int, crewId: int, file: UploadFile = File(...)):
#     try:
#         # Process the uploaded image
#         image = await encode_image(file)

#         # Call OpenAI API
#         client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": "Read data in this image, there will be names on the left side and scores on right and on top there will be sport i need you to return it to me in JSON format {label:,list:[{name:,score:}],count: list.length} sport as label, results as list please just return JSON format no extra text, if the image doesnt look like i described return to me string 'false'",
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {"url": f"data:image/jpeg;base64,{image}"},
#                         },
#                     ],
#                 },
#             ],
#         )
#         res = completion.choices[0].message.content

#         if res == "false":
#             return {"message": "Invalid image format."}
#         # Fetch persons from the database
#         async with async_session_maker() as db:
#             result = await db.execute(text("SELECT * FROM persons"))
#             rows = result.fetchall()
#             persons = {"list": [dict(row._mapping) for row in rows], "count": len(rows)}

#         return format_openai_resp(res, persons)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
