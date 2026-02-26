import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, FONT_ARIAL_BOLD, safe_get
import re

PDF_TEMPLATE = Paths.template("REVOLUT.pdf")
FONT_FILE = Paths.font("roboto-regular.ttf")

FONT_SIZE = 8.25
COLOR = (25/255, 28/255, 31/255)

DEFAULTS = {
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "iban": "FR7630004008001234567890152",
    "bic": "REVOFR22",
}

def format_iban(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return " ".join(v[i:i+4] for i in range(0, len(v), 4))

def format_bic(v: str):
    v = re.sub(r"\s+", "", v).upper()
    return " ".join(v)

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


def generate_revolut(data, output_path, is_preview=False):
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
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_revolut_pdf(data, output_path):
    return generate_revolut(data, output_path, is_preview=False)

def generate_revolut_preview(data, output_path):
    return generate_revolut(data, output_path, is_preview=True)
