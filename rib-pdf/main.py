from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid

from script.sg import generate_sg_pdf
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

    agence: Optional[str] = None
    agence_adresse: Optional[str] = None
    agence_cp_ville: Optional[str] = None

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):
    output = f"/tmp/{uuid.uuid4()}.pdf"

    if data.type_pdf == "lbp":
        generate_lbp_pdf(data, output)
    elif data.type_pdf == "sg":
        generate_sg_pdf(data, output)
    else:
        raise HTTPException(400, "type_pdf inconnu")

    return FileResponse(output, media_type="application/pdf", filename="rib.pdf")
