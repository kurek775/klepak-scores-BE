from fastapi import APIRouter, HTTPException, UploadFile, File
from utils.openai import encode_image, format_openai_resp
from db import async_session_maker
import os
import openai

api_router = APIRouter()

@api_router.post("/{crewId}/upload-photo")
async def upload_file(crewId: int, file: UploadFile = File(...)):
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
                    "content": "Read data in this image, ... JSON format only",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                },
            ],
        )
        res = completion.choices[0].message.content

        if res == 'false':
            return {"message": 'Invalid image format.'}

        # Fetch persons from the database
        async with async_session_maker() as db:
            result = await db.execute("SELECT * FROM persons")
            rows = result.fetchall()
            persons = {"list": [dict(row._mapping) for row in rows], "count": len(rows)}

        return format_openai_resp(res, persons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
