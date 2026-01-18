import fitz
import os
import re

# =========================
# BASE DIR
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "CIC.pdf")
FONT_ARIAL_REG = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

FONT_REG_NAME = "ARIAL_REG"
FONT_BOLD_NAME = "ARIAL_BOLD"

FONT_SIZE = 8.5
COLOR = (0, 0, 0)

# =========================
# DEFAULT VALUES
# =========================

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
# UTILS
# =========================

def format_iban(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return "       ".join(v[i:i+4] for i in range(0, len(v), 4))

def fontname_for(key: str):
    return FONT_BOLD_NAME if key in BOLD_KEYS else FONT_REG_NAME

# =========================
# WRITE
# =========================

def overwrite(page, key, text):
    for r in page.search_for(key):
        page.draw_rect(r, fill=(1, 1, 1), width=0)
        page.insert_text(
            (r.x0, r.y1 - 1.4),
            text,
            fontsize=FONT_SIZE,
            fontname=fontname_for(key),
            color=COLOR,
        )

# =========================
# GENERATOR
# =========================


def add_watermark(page):
    rect = page.rect
    text = "PREVIEW – NON PAYÉ"

    for y in range(80, int(rect.height), 160):
        page.insert_text(
            (40, y),
            text,
            fontsize=42,
            fontname=FONT_BOLD_NAME,
            color=(0.55, 0.55, 0.55),
            fill_opacity=5.22,
        )


def generate_cic_pdf(data, output_path):
    values = {
        "*banque": (data.banque or DEFAULTS["banque"]).upper(),
        "*guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "*compte": (data.compte or DEFAULTS["compte"]).upper(),
        "*cle": (data.cle or DEFAULTS["cle"]).upper(),
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
        "*agence1": (data.agence or DEFAULTS["agence1"]).upper(),
        "*agence2": (data.agence or DEFAULTS["agence2"]).upper(),
        "*agenceadresse": (data.agence_adresse or DEFAULTS["agenceadresse"]).upper(),
        "*agencecpville": (data.agence_cp_ville or DEFAULTS["agencecpville"]).upper(),
        "*telephone": (data.telephone or DEFAULTS["telephone"]).upper(),
        "*nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG_NAME, FONT_ARIAL_REG)
        page.insert_font(FONT_BOLD_NAME, FONT_ARIAL_BOLD)

        for k, v in values.items():
            overwrite(page, k, v)
        
        add_watermark(page)

    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True,
    )
    doc.close()
