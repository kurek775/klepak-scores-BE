from fastapi import UploadFile
import base64
import re
import json
async def encode_image(file: UploadFile):
    file_content = await file.read()  
    return base64.b64encode(file_content).decode("utf-8")

def format_openai_resp(data):

    match = re.search(r"```json\n(.*?)\n```", data, re.DOTALL)
    if not match:
            raise ValueError("No JSON block found in the message.")
    json_content = match.group(1)
    fData = json.loads(json_content)
    return fData