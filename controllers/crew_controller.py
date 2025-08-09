from fastapi import APIRouter, HTTPException, UploadFile, File
from utils.openai import encode_image, format_openai_resp
from sqlalchemy import text
from db import async_session_maker
import os
import openai

api_router = APIRouter()


from typing import List
from fastapi import Body, Path, HTTPException
from pydantic import BaseModel


class ResultFromFrontend(BaseModel):
    person_id: int
    score: float
    # other fields are ignored


@api_router.put(
    "/{crew_id}/sport/{sport_id}",
    summary="Save results from frontend payload (like GET response)",
)
async def save_results_from_frontend(
    crew_id: int = Path(...),
    sport_id: int = Path(...),
    results: List[ResultFromFrontend] = Body(...),
):
    async with async_session_maker() as db:
        try:
            for item in results:
                check = await db.execute(
                    text("SELECT 1 FROM persons WHERE id = :pid AND crew_id = :cid"),
                    {"pid": item.person_id, "cid": crew_id},
                )
                if check.first() is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Person {item.person_id} not in crew {crew_id}",
                    )

                # Check if result exists
                existing = await db.execute(
                    text(
                        "SELECT id FROM results WHERE person_id = :pid AND sport_id = :sid"
                    ),
                    {"pid": item.person_id, "sid": sport_id},
                )
                row = existing.first()

                if row:
                    await db.execute(
                        text("UPDATE results SET score = :score WHERE id = :rid"),
                        {"score": item.score, "rid": row.id},
                    )
                else:
                    await db.execute(
                        text(
                            "INSERT INTO results (person_id, sport_id, score) VALUES (:pid, :sid, :score)"
                        ),
                        {"pid": item.person_id, "sid": sport_id, "score": item.score},
                    )

            await db.commit()
            return {"status": "success", "updated": len(results)}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@api_router.get(
    "/{crew_id}/sport/{sport_id}",
    summary="Get persons with result for a given crew, sport and tour",
)
async def get_crew_results(crew_id: int, sport_id: int, tour_id: int):
    async with async_session_maker() as db:
        try:
            # 1) Ověř, že sport patří do tour (tour_sports)
            check = await db.scalar(
                text(
                    """
                    SELECT 1
                    FROM tour_sports
                    WHERE tour_id = :tour_id AND sport_id = :sport_id
                    LIMIT 1
                """
                ),
                {"tour_id": tour_id, "sport_id": sport_id},
            )
            if not check:
                raise HTTPException(
                    status_code=404, detail="Sport is not part of the specified tour."
                )

            # 2) Vrať všechny osoby z crew, s případným výsledkem pro daný sport v dané tour
            #    (LEFT JOIN zachová i osoby bez výsledku)
            query = text(
                """
                SELECT
                    p.id   AS person_id,
                    p.name AS person_name,
                    r.id   AS result_id,
                    r.score,
                    r.tour_id,
                    s.id   AS sport_id,
                    s.name AS sport_name,
                    s.metric
                FROM persons p
                LEFT JOIN results r
                  ON r.person_id = p.id
                 AND r.tour_id   = :tour_id
                 AND r.sport_id  = :sport_id
                -- sport info vrátíme i když výsledek neexistuje
                LEFT JOIN sports s
                  ON s.id = :sport_id
                WHERE p.crew_id = :crew_id
                ORDER BY p.name
            """
            )

            result = await db.execute(
                query,
                {"crew_id": crew_id, "tour_id": tour_id, "sport_id": sport_id},
            )
            rows = [dict(row._mapping) for row in result.fetchall()]
            return {"list": rows, "count": len(rows)}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{crew_id}/upload-photo")
async def upload_file(tour_id: int, crewId: int, file: UploadFile = File(...)):
    try:
        # Process the uploaded image
        image = await encode_image(file)

        # Call OpenAI API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Read data in this image, there will be names on the left side and scores on right and on top there will be sport i need you to return it to me in JSON format {label:,list:[{name:,score:}],count: list.length} sport as label, results as list please just return JSON format no extra text, if the image doesnt look like i described return to me string 'false'",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        },
                    ],
                },
            ],
        )
        res = completion.choices[0].message.content

        if res == "false":
            return {"message": "Invalid image format."}

        # Fetch persons from the database
        async with async_session_maker() as db:
            result = await db.execute(text("SELECT * FROM persons"))
            rows = result.fetchall()
            persons = {"list": [dict(row._mapping) for row in rows], "count": len(rows)}

        return format_openai_resp(res, persons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
