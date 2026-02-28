import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get
import re

PDF_TEMPLATE = Paths.template("CIC.pdf")
FONT_ARIAL_REG = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

FONT_REG_NAME = "ARIAL_REG"
FONT_BOLD_NAME = "ARIAL_BOLD"

FONT_SIZE = 8.5
COLOR = (0, 0, 0)

DEFAULTS = {
    "banque": "30066",
    "guichet": "10278",
    "compte": "00012345678",
    "cle": "45",
    "iban": "FR7630066102780001234567845",
    "agence1": "AGENCE TOULOUSE CENTRE",
    "agence2": "CIC",
    "agenceadresse": "14 RUE ALSACE LORRAINE",
    "agencecpville": "31000 TOULOUSE",
    "telephone": "01 49 08 51 33",
    "nom_prenom": "JEAN MICHEL BERNARD",
    "adresse": "8 PLACE DE LA CONCORDE",
    "cp_ville": "75006 PARIS",
    "agence": "AGENCE TOULOUSE CENTRE",
    "agence_adresse": "14 RUE ALSACE LORRAINE",
    "agence_cp_ville": "31000 TOULOUSE",
}

BOLD_KEYS = {"*banque", "*guichet", "*compte", "*cle", "*iban", "*agence1"}

def format_iban(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return "       ".join(v[i:i+4] for i in range(0, len(v), 4))

def fontname_for(key: str):
    return FONT_BOLD_NAME if key in BOLD_KEYS else FONT_REG_NAME

def overwrite(page, key, text):
    rects = page.search_for(key)
    if not rects:
        return

    for r in rects:
        page.add_redact_annot(r, fill=(1, 1, 1))
    
    page.apply_redactions()

    for r in rects:
        page.insert_text(
            (r.x0, r.y1 - 1.4),
            text,
            fontsize=FONT_SIZE,
            fontname=fontname_for(key),
            color=COLOR,
        )

def generate_cic(data, output_path, is_preview=False):
    values = {
        "*banque": safe_get(data, "banque", DEFAULTS).upper(),
        "*guichet": safe_get(data, "guichet", DEFAULTS).upper(),
        "*compte": safe_get(data, "compte", DEFAULTS).upper(),
        "*cle": safe_get(data, "cle", DEFAULTS).upper(),
        "*iban": format_iban(safe_get(data, "iban", DEFAULTS)),
        "*agence1": safe_get(data, "agence", DEFAULTS).upper(),
        "*agence2": safe_get(data, "agence", DEFAULTS).upper(),
        "*agenceadresse": safe_get(data, "agence_adresse", DEFAULTS).upper(),
        "*agencecpville": safe_get(data, "agence_cp_ville", DEFAULTS).upper(),
        "*telephone": safe_get(data, "telephone", DEFAULTS).upper(),
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG_NAME, FONT_ARIAL_REG)
        page.insert_font(FONT_BOLD_NAME, FONT_ARIAL_BOLD)

        # Tri par longueur décroissante pour éviter les conflits de sous-chaînes
        for k in sorted(values.keys(), key=len, reverse=True):
            overwrite(page, k, values[k])
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_cic_pdf(data, output_path):
    return generate_cic(data, output_path, is_preview=False)

def generate_cic_preview(data, output_path):
    return generate_cic(data, output_path, is_preview=True)
