# =========================
# script/revolut.py
# =========================
import fitz
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "REVOLUT.pdf")
FONT_FILE = os.path.join(BASE_DIR, "font", "roboto-regular.ttf")

FONT_SIZE = 8.25
COLOR = (25/255, 28/255, 31/255)

DEFAULTS = {
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp": "75009",
    "ville": "PARIS",
    "depart": "PARIS",
    "banque": "12345",
    "guichet": "12345",
    "compte": "12345678901",
    "cle": "12",
    "iban": "FR7612345123451234567890112",
}

def format_iban(iban: str):
    iban = re.sub(r"\s+", "", iban).upper()
    return iban[:27]

def insert_text(page, key, text):
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
            fontfile=FONT_FILE,
            color=COLOR,
            align=0,
        )

def generate_revolut_pdf(data, output_path):
    values = {
        "*nom prenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cp": (data.cp or DEFAULTS["cp"]),
        "*ville": (data.ville or DEFAULTS["ville"]).upper(),
        "*depart": (data.depart or DEFAULTS["depart"]).upper(),
        "*banque": (data.banque or DEFAULTS["banque"]).upper(),
        "*guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "*compte": (data.compte or DEFAULTS["compte"]).upper(),
        "*cle": (data.cle or DEFAULTS["cle"]).upper(),
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        for key, val in values.items():
            insert_text(page, key, val)

    doc.save(output_path)
    doc.close()
