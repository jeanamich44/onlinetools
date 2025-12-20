import fitz
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
# POLICE
# =========================

FONT_PATH = "arialbd.ttf"
if not os.path.exists(FONT_PATH):
    raise RuntimeError("Police manquante")

# =========================
# PDF ORIGINAL (BASE)
# =========================

PDF_TEMPLATE = ".BASE.pdf"
if not os.path.exists(PDF_TEMPLATE):
    raise RuntimeError("PDF template manquant")

# =========================
# VALEURS PAR DÉFAUT (INCHANGÉES)
# =========================

DEFAULTS = {
    "banque": "20041",
    "guichet": "01007",
    "compte": "1852185T038",
    "cle": "52",
    "iban": "FR67 2004 1010 0718 5218 5T03 852",
    "bic": "P S S T F R P P L Y O",
    "nom prenom": "GOULIET ANTOINE",
    "adresse": "14 rue de provence",
    "cp ville": "75009 PARIS",
    "domiciliation": "LA BANQUE POSTALE LYON CENTRE FINANCIER",
}

FONT_SIZE = 9
COLOR = (0, 0, 0)

# =========================
# SCHEMA API
# =========================

class PDFRequest(BaseModel):
    sexe: str | None = "m"
    banque: str | None = None
    guichet: str | None = None
    compte: str | None = None
    cle: str | None = None
    iban: str | None = None
    bic: str | None = None
    nom_prenom: str | None = None
    adresse: str | None = None
    cp_ville: str | None = None
    domiciliation: str | None = None

# =========================
# API
# =========================

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):

    titre = "MR" if data.sexe.lower() == "m" else "MME"

    # === LOGIQUE IDENTIQUE : valeur reçue OU défaut ===
    values = {
        "banque": (data.banque or DEFAULTS["banque"]).upper(),
        "guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "compte": (data.compte or DEFAULTS["compte"]).upper(),
        "cle": (data.cle or DEFAULTS["cle"]).upper(),
        "iban": " ".join(
            (data.iban or DEFAULTS["iban"]).replace(" ", "").upper()[i:i+4]
            for i in range(0, len((data.iban or DEFAULTS["iban"]).replace(" ", "")), 4)
        ),
        "bic": " ".join(list((data.bic or DEFAULTS["bic"]).replace(" ", "").upper())),
        "nom prenom": f"{titre} {(data.nom_prenom or DEFAULTS['nom prenom']).upper()}",
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cp ville": (data.cp_ville or DEFAULTS["cp ville"]).upper(),
        "domiciliation": (data.domiciliation or DEFAULTS["domiciliation"]).upper(),
    }

    # === NOUVEAU PDF UNIQUE ===
    uid = str(uuid.uuid4())
    output_path = f"/tmp/{uid}.pdf"

    # === OUVERTURE DU PDF ORIGINAL (JAMAIS MODIFIÉ) ===
    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        fontname = "ArialBold"
        page.insert_font(fontname=fontname, fontfile=FONT_PATH)

        for key, new_text in values.items():
            results = page.search_for(f"*{key}")
            if not results:
                continue

            for rect in results:
                page.draw_rect(rect, fill=(1, 1, 1), width=0)
                page.insert_text(
                    (rect.x0, rect.y1 - 2),
                    new_text,
                    fontsize=FONT_SIZE,
                    fontname=fontname,
                    color=COLOR,
                )

    doc.save(output_path)
    doc.close()

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="pdf_modifie.pdf"
    )
