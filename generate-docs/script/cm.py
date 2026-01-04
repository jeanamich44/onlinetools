import fitz
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "CM.pdf")
FONT_ARIAL_REG = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

COLOR_BLACK = (0, 0, 0)

FONT_SIZE = 8

DEFAULTS = {
    "banque": "10278",
    "guichet": "02100",
    "compte": "00012345678",
    "cle": "45",
    "iban": "FR761027802100001234567845",
    "agence1": "AGENCE TOULOUSE CENTRE",
    "agence2": "CREDIT MUTUEL",
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

def format_iban(iban: str):
    iban = re.sub(r"\s+", "", iban).upper()
    return "       ".join(iban[i:i+4] for i in range(0, len(iban), 4))

def insert_text(page, key, text, font_path):
    for r in page.search_for(key):
        pad = 0.6
        red = fitz.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad)
        page.add_redact_annot(red, fill=(1, 1, 1))
        page.apply_redactions()

        write = fitz.Rect(
            r.x0,
            r.y0 - 0.25 * r.height,
            page.rect.x1 - 36,
            r.y1 + 0.25 * r.height,
        )

        page.insert_textbox(
            write,
            text,
            fontsize=FONT_SIZE,
            fontfile=font_path,
            color=COLOR_BLACK,
            align=0,
        )

def generate_cm_pdf(data, output_path):
    values = {
        "*banque": data.banque or DEFAULTS["banque"],
        "*guichet": data.guichet or DEFAULTS["guichet"],
        "*compte": data.compte or DEFAULTS["compte"],
        "*cle": data.cle or DEFAULTS["cle"],
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
        "*agence1": (data.agence or DEFAULTS["agence1"]).upper(),
        "*agence2": (data.agence or DEFAULTS["agence2"]).upper(),
        "*agenceadresse": (data.agence_adresse or DEFAULTS["agenceadresse"]).upper(),
        "*agencecpville": (data.agence_cp_ville or DEFAULTS["agencecpville"]).upper(),
        "*telephone": data.telephone or DEFAULTS["telephone"],
        "*nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font("ARIAL_REG", FONT_ARIAL_REG)
        page.insert_font("ARIAL_BOLD", FONT_ARIAL_BOLD)

        for key, val in values.items():
            font = FONT_ARIAL_BOLD if key in BOLD_KEYS else FONT_ARIAL_REG
            insert_text(page, key, val, font)

    doc.save(output_path)
    doc.close()
