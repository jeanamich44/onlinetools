
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from script.mrz import generate_mrz, generate_random_data
from script.qr_zip import generate_qr_zip

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT = {}
MAX_REQUESTS = 5
WINDOW = 60

class MRZRequest(BaseModel):
    mode: str = "random"
    nom: str | None = None
    prenom: str | None = None
    dep: str | None = None
    canton: str | None = None
    bureau: str | None = None
    date_delivrance: str | None = None
    random_code: str | None = None
    naissance: str | None = None
    sexe: str | None = None

class QRRequest(BaseModel):
    lines: list[str]

@app.post("/generate-mrz")
def generate_mrz_endpoint(req: MRZRequest):
    if req.mode.lower() == "aleatoire":
        data = generate_random_data()
        mrz = generate_mrz(data)
        return {"mrz": [f"{mrz['line1']}\n{mrz['line2']}"]}

    if req.mode.lower() == "manuel":
        data = {
            "nom": req.nom,
            "prenom": req.prenom,
            "dep": req.dep,
            "canton": req.canton,
            "bureau": req.bureau,
            "date_delivrance": req.date_delivrance,
            "random_code": req.random_code,
            "naissance": req.naissance,
            "sexe": req.sexe.upper(),
        }
        if data["sexe"] not in ("M", "F"):
            raise HTTPException(400, "Sexe invalide (M/F)")

        if None in data.values():
            raise HTTPException(status_code=400, detail="Missing fields")

        mrz = generate_mrz(data)
        return {"mrz": [f"{mrz['line1']}\n{mrz['line2']}"]}

    raise HTTPException(status_code=400, detail="Invalid mode")

@app.post("/generate-zip")
def generate_zip_endpoint(req: QRRequest, request: Request):
    ip = request.client.host
    now = time.time()

    hits = RATE_LIMIT.get(ip, [])
    hits = [t for t in hits if now - t < WINDOW]

    if len(hits) >= MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit")

    hits.append(now)
    RATE_LIMIT[ip] = hits

    try:
        zip_path = generate_qr_zip(req.lines)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="qr_codes.zip"
    )
