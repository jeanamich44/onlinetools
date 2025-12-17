from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import qrcode
import zipfile
import os
import uuid
import shutil

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QRRequest(BaseModel):
    lines: list[str]

@app.post("/generate-zip")
def generate_zip(data: QRRequest):
    if not data.lines:
        raise HTTPException(status_code=400, detail="Empty list")

    if len(data.lines) > 4000:
        raise HTTPException(status_code=400, detail="Too many lines")

    uid = str(uuid.uuid4())
    temp_dir = f"tmp_{uid}"
    zip_path = f"{uid}.zip"

    os.makedirs(temp_dir)

    for i, text in enumerate(data.lines, start=1):
        qr = qrcode.make(text)
        qr.save(f"{temp_dir}/qr_{i}.png")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(
                os.path.join(temp_dir, file),
                arcname=file
            )

    shutil.rmtree(temp_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="qr_codes.zip"
    )
