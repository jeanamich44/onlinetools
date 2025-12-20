import fitz
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# =========================
# INIT API
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# CONSTANTES
# =========================

PDF_TEMPLATE = ".BASE.pdf"
FONT_FILE = "arialbd.ttf"
FONT_NAME = "ArialBold"
FONT_SIZE = 9
COLOR = (0, 0, 0)

# =========================
# DEFAULTS
# =========================

DEFAULTS = {
    "banque": "20041",
    "guichet": "01007",
    "compte": "1852185T038",
    "cle": "52",
    "iban": "FR6720041010071852185T03852",
    "bic": "PSSTFRPPLYO",
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "domiciliation": "LA BANQUE POSTALE LYON CENTRE FINANCIER",
}

# =========================
# SCHEMA API
# =========================

class PDFRequest(BaseModel):
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


# =========================
# API
# =========================

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):

    titre = "MR" if data.sexe.lower() == "m" else "MME"

    values = {
        "banque": (data.banque or DEFAULTS["banque"]).upper(),
        "guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "compte": (data.compte or DEFAULTS["compte"]).upper(),
        "cle": (data.cle or DEFAULTS["cle"]).upper(),
        "iban": " ".join(
            (data.iban or DEFAULTS["iban"]).replace(" ", "").upper()[i:i+4]
            for i in range(0, len((data.iban or DEFAULTS["iban"]).replace(" ", "")), 4)
        ),
        "bic": " ".join((data.bic or DEFAULTS["bic"]).replace(" ", "").upper()),
        "nom prenom": f"{titre} {(data.nom_prenom or DEFAULTS['nom_prenom']).upper()}",
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "domiciliation": (data.domiciliation or DEFAULTS["domiciliation"]).upper(),
    }

    output_path = f"/tmp/{uuid.uuid4()}.pdf"

    try:
        doc = fitz.open(PDF_TEMPLATE)

        for page in doc:
            page.insert_font(fontname=FONT_NAME, fontfile=FONT_FILE)

            for key, text in values.items():
                for rect in page.search_for(f"*{key}"):
                    page.draw_rect(rect, fill=(1, 1, 1), width=0)
                    page.insert_text(
                        (rect.x0, rect.y1 - 2),
                        text,
                        fontsize=FONT_SIZE,
                        fontname=FONT_NAME,
                        color=COLOR,
                    )

        doc.save(output_path)
        doc.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="rib_lbp.pdf",
    )
