from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import os

from script.lbp import generate_lbp_pdf, generate_lbp_preview
from script.sg import generate_sg_pdf, generate_sg_preview
from script.bfb import generate_bfb_pdf, generate_bfb_preview
from script.revolut import generate_revolut_pdf, generate_revolut_preview
from script.ca import generate_ca_pdf, generate_ca_preview
from script.cm import generate_cm_pdf, generate_cm_preview
from script.cic import generate_cic_pdf, generate_cic_preview
from script.qonto import generate_qonto_pdf, generate_qonto_preview
from script.maxance import generate_maxance_pdf, generate_maxance_preview


# =========================
# INITIALISATION
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# =========================
# SCHEMA
# =========================

class PDFRequest(BaseModel):
    type_pdf: str  # "lbp" | "sg" | "bfb" | "revolut" | "credit_agricole"
    preview: Optional[bool] = False

    sexe: Optional[str] = "m"

    # Champs communs
    nom_prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp_ville: Optional[str] = None
    telephone: Optional[str] = None

    # Champs détaillés
    cp: Optional[str] = None
    ville: Optional[str] = None
    depart: Optional[str] = None

    banque: Optional[str] = None
    guichet: Optional[str] = None
    compte: Optional[str] = None
    cle: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None

    domiciliation: Optional[str] = None

    agence: Optional[str] = None
    agence_adresse: Optional[str] = None
    agence_cp_ville: Optional[str] = None
    bank: Optional[str] = None

    nclient: Optional[str] = None
    ncontrat: Optional[str] = None
    norias: Optional[str] = None
    plaque: Optional[str] = None
    typevehicule: Optional[str] = None

# =========================
# API
# =========================

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):
    output_path = f"/tmp/{uuid.uuid4()}.pdf"

    try:
        if data.type_pdf == "lbp":
            if data.preview:
                generate_lbp_preview(data, output_path)
            else:
                generate_lbp_pdf(data, output_path)

        elif data.type_pdf == "sg":
            if data.preview:
                generate_sg_preview(data, output_path)
            else:
                generate_sg_pdf(data, output_path)

        elif data.type_pdf == "bfb":
            if data.preview:
                generate_bfb_preview(data, output_path)
            else:
                generate_bfb_pdf(data, output_path)

        elif data.type_pdf == "revolut":
            if data.preview:
                generate_revolut_preview(data, output_path)
            else:
                generate_revolut_pdf(data, output_path)

        elif data.type_pdf == "ca":
            if data.preview:
                generate_ca_preview(data, output_path)
            else:
                generate_ca_pdf(data, output_path)

        elif data.type_pdf == "cm":
            if data.preview:
                generate_cm_preview(data, output_path)
            else:
                generate_cm_pdf(data, output_path)

        elif data.type_pdf == "cic":
            if data.preview:
                generate_cic_preview(data, output_path)
            else:
                generate_cic_pdf(data, output_path)

        elif data.type_pdf == "qonto":
            if data.preview:
                generate_qonto_preview(data, output_path)
            else:
                generate_qonto_pdf(data, output_path)

        elif data.type_pdf == "maxance":
            if data.preview:
                generate_maxance_preview(data, output_path)
            else:
                generate_maxance_pdf(data, output_path)

        else:
            raise HTTPException(status_code=400, detail="type_pdf invalide")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="PDF non généré")

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="rib.pdf",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
