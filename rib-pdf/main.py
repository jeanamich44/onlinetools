from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from script.lbp import generate_lbp_pdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PDFRequest(BaseModel):
    type_pdf: str

    sexe: Optional[str] = "m"
    banque: Optional[str] = None
    guichet: Optional[str] = None
    compte: Optional[str] = None
    cle: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    nom_prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp_ville: Optional[str] = None
    domiciliation: Optional[str] = None

@app.post("/generate-pdf")
def generate_pdf(payload: PDFRequest):
    data = payload.dict()

    if payload.type_pdf == "lbp":
        try:
            pdf_path = generate_lbp_pdf(data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Type de PDF non supporté")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="document.pdf",
    )
