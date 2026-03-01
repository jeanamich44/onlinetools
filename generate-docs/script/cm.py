import fitz
import os
import re
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get

# =========================
# CHEMINS (EN LIGNE)
# =========================

PDF_TEMPLATE = Paths.template("CM.pdf")
FONT_ARIAL_REG_PATH = Paths.font("arial.ttf")
FONT_ARIAL_BOLD_PATH = Paths.font("arialbd.ttf")

FONT_REG_NAME = "ARIAL_REG"
FONT_BOLD_NAME = "ARIAL_BOLD"

FONT_SIZE = 8
COLOR = (0, 0, 0)

# =========================
# VALEURS PAR DEFAUT
# =========================

DEFAULTS = {
    "banque": "10278",
    "guichet": "02100",
    "compte": "00012345678",
    "cle": "45",
    "iban": "FR761027802100001234567845",
    "agence1": "AGENCE CRÉDIT MUTUEL",
    "agence2": "AGENCE CRÉDIT MUTUEL",
    "agenceadresse": "14 RUE DES LILAS",
    "agencecpville": "31000 TOULOUSE",
    "telephone": "01 23 45 67 89",
    "nom_prenom": "JEAN MICHEL BERNARD",
    "adresse": "8 PLACE DE LA CONCORDE",
    "cp_ville": "75006 PARIS",
}

BOLD_KEYS = {
    "*banque",
    "*guichet",
    "*compte",
    "*cle",
    "*iban",
    "*agence1",
}

# =========================
# UTILITAIRES
# =========================

def format_iban(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return "       ".join(v[i:i+4] for i in range(0, len(v), 4))

def fontname_for(key):
    return FONT_BOLD_NAME if key in BOLD_KEYS else FONT_REG_NAME

# =========================
# ECRITURE
# =========================

def overwrite(page, key, text):
    rects = page.search_for(key)
    if not rects:
        return

    # Rédaction réelle pour éviter les superpositions au moteur de recherche
    for r in rects:
        page.add_redact_annot(r, fill=(1, 1, 1))
    
    page.apply_redactions()

    # Insertion du nouveau texte
    for r in rects:
        page.insert_text(
            (r.x0, r.y1 - 1.4),
            text,
            fontsize=FONT_SIZE,
            fontname=fontname_for(key),
            color=COLOR,
        )

# =========================
# GENERATEUR PRINCIPAL
# =========================

def generate_cm(data, output_path, is_preview=False):
    # Mapping des valeurs avec fallback sur les nouveaux DEFAULTS
    values = {
        "*banque": safe_get(data, "banque", DEFAULTS),
        "*guichet": safe_get(data, "guichet", DEFAULTS),
        "*compte": safe_get(data, "compte", DEFAULTS),
        "*cle": safe_get(data, "cle", DEFAULTS),
        "*iban": format_iban(safe_get(data, "iban", DEFAULTS)),
        "*agence1": safe_get(data, "agence", DEFAULTS).upper() or DEFAULTS["agence1"],
        "*agence2": safe_get(data, "agence", DEFAULTS).upper() or DEFAULTS["agence2"],
        "*agenceadresse": safe_get(data, "agence_adresse", DEFAULTS).upper() or DEFAULTS["agenceadresse"],
        "*agencecpville": safe_get(data, "agence_cp_ville", DEFAULTS).upper() or DEFAULTS["agencecpville"],
        "*telephone": safe_get(data, "telephone", DEFAULTS),
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG_NAME, FONT_ARIAL_REG_PATH)
        page.insert_font(FONT_BOLD_NAME, FONT_ARIAL_BOLD_PATH)

        # Tri par longueur décroissante pour être sûr de ne pas écraser les sous-tags
        for k in sorted(values.keys(), key=len, reverse=True):
            overwrite(page, k, values[k])
        
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
