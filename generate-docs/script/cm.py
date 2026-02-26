import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get
import re

# =========================
# CHEMINS (EN LIGNE)
# =========================

PDF_TEMPLATE = Paths.template("CM.pdf")
FONT_ARIAL_REG_PATH = Paths.font("arial.ttf")
FONT_ARIAL_BOLD_PATH = Paths.font("arialbd.ttf")

FONT_REG_NAME = "ARIAL_REG"
FONT_BOLD_NAME = "ARIAL_BOLD"

FONT_SIZE = 8.5
COLOR = (0, 0, 0)

# =========================
# VALEURS PAR DEFAUT
# =========================

DEFAULTS = {
    "banque": "30066",
    "guichet": "10278",
    "compte": "00012345678",
    "cle": "45",
    "iban": "FR7630066102780001234567845",
    "agence": "AGENCE CRÉDIT MUTUEL",
    "agence_adresse": "14 RUE DES LILAS",
    "agence_cp_ville": "31000 TOULOUSE",
    "telephone": "01 23 45 67 89",
    "nom_prenom": "JEAN DUPONT",
    "adresse": "10 RUE DE LA PAIX",
    "cp_ville": "75001 PARIS",
}


# =========================
# UTILITAIRES (IDENTIQUE LOCAL)
# =========================


def format_iban(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return "       ".join(v[i:i+4] for i in range(0, len(v), 4))

# =========================
# ECRITURE (IDENTIQUE LOCAL)
# =========================

def overwrite(page, key, text, is_bold=False):
    fontname = FONT_BOLD_NAME if is_bold else FONT_REG_NAME
    for r in page.search_for(key):
        page.draw_rect(r, fill=(1, 1, 1), width=0)
        page.insert_text(
            (r.x0, r.y1 - 1.4),
            text,
            fontsize=FONT_SIZE,
            fontname=fontname,
            color=COLOR,
        )

# =========================
# GENERATEUR PRINCIPAL (EN LIGNE)
# =========================

def generate_cm(data, output_path, is_preview=False):
    values = {
        "*banque": safe_get(data, "banque", DEFAULTS).upper(),
        "*guichet": safe_get(data, "guichet", DEFAULTS).upper(),
        "*compte": safe_get(data, "compte", DEFAULTS).upper(),
        "*cle": safe_get(data, "cle", DEFAULTS).upper(),
        "*iban": format_iban(safe_get(data, "iban", DEFAULTS)),
        "*agence": safe_get(data, "agence", DEFAULTS).upper(),
        "*agencead": safe_get(data, "agence_adresse", DEFAULTS).upper(),
        "*agencecpv": safe_get(data, "agence_cp_ville", DEFAULTS).upper(),
        "*telephone": safe_get(data, "telephone", DEFAULTS).upper(),
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG_NAME, FONT_ARIAL_REG_PATH)
        page.insert_font(FONT_BOLD_NAME, FONT_ARIAL_BOLD_PATH)

        for k, v in values.items():
            overwrite(page, k, v)
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD_PATH)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_cm_pdf(data, output_path):
    return generate_cm(data, output_path, is_preview=False)

def generate_cm_preview(data, output_path):
    return generate_cm(data, output_path, is_preview=True)
