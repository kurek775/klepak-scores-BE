from fastapi import UploadFile
import base64
import re
import json
from difflib import get_close_matches
async def encode_image(file: UploadFile):
    file_content = await file.read()  
    return base64.b64encode(file_content).decode("utf-8")

def format_openai_resp(data, persons):
    # Extract JSON content from OpenAI response
    match = re.search(r"```json\n(.*?)\n```", data, re.DOTALL)
    if not match:
        raise ValueError("No JSON block found in the message.")
    json_content = match.group(1)
    fData = json.loads(json_content)
    db_persons = persons['list']
    for item in fData['list']:
        name_from_paper = item['name']
        matches = get_close_matches(name_from_paper, [p['name'] for p in db_persons], n=1, cutoff=0.5)
        if matches:
            matched_name = matches[0]
            person_data = next(p for p in db_persons if p['name'] == matched_name)
            item['name'] = matched_name
            item['id'] = person_data['id']
        else:
            item['id'] = None

    return fData