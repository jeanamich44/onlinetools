from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
import zipfile
import os
import uuid
import shutil
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_LINES = 4000
RATE_LIMIT = {}
MAX_REQUESTS = 5
WINDOW = 60  # seconds

class QRRequest(BaseModel):
    lines: list[str]

def index_to_code(i: int) -> str:
    a = (i // 676) % 26
    b = (i // 26) % 26
    c = i % 26
    return f"{chr(65+a)}{chr(65+b)}{chr(65+c)}"

@app.post("/generate-zip")
def generate_zip(data: QRRequest, request: Request):
    ip = request.client.host
    now = time.time()

    hits = RATE_LIMIT.get(ip, [])
    hits = [t for t in hits if now - t < WINDOW]

    if len(hits) >= MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Trop de requêtes (5/min max)")

    hits.append(now)
    RATE_LIMIT[ip] = hits

    if not data.lines:
        raise HTTPException(status_code=400, detail="Liste vide")

    if len(data.lines) > MAX_LINES:
        raise HTTPException(status_code=400, detail="Limite dépassée (4000 lignes max)")

    uid = str(uuid.uuid4())
    temp_dir = f"/tmp/{uid}"
    zip_path = f"/tmp/{uid}.zip"

    os.makedirs(temp_dir)

    for i, text in enumerate(data.lines):
        code = index_to_code(i)
        qr = qrcode.make(text)
        qr.save(f"{temp_dir}/{code}.png")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(os.path.join(temp_dir, file), arcname=file)

    shutil.rmtree(temp_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="qr_codes.zip"
    )
