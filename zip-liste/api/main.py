from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
import zipfile
import os
import uuid
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_LINES = 4000

class QRRequest(BaseModel):
    lines: list[str]

@app.post("/generate-zip")
def generate_zip(data: QRRequest):
    if not data.lines:
        raise HTTPException(status_code=400, detail="Liste vide")

    if len(data.lines) > MAX_LINES:
        raise HTTPException(status_code=400, detail="Maximum 4000 lignes")

    uid = str(uuid.uuid4())
    temp_dir = f"/tmp/{uid}"
    zip_path = f"/tmp/{uid}.zip"

    os.makedirs(temp_dir)

    for i, text in enumerate(data.lines, start=1):
        qr = qrcode.make(text)
        qr.save(f"{temp_dir}/qr_{i}.png")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(os.path.join(temp_dir, file), arcname=file)

    shutil.rmtree(temp_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="qr_codes.zip"
    )
