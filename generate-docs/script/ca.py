import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get
import re

PDF_TEMPLATE = Paths.template("CA.pdf")
FONT_FILE = Paths.font("opensans-semibold.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

FONT_SIZE = 9.6
COLOR = (0, 0, 0)
RIGHT_LIMIT_X = 538.87

DEFAULTS = {
    "nom_prenom": "JEAN MICHEL BERNARD",
    "adresse": "8 PLACE DE LA CONCORDE",
    "cp_ville": "75006 PARIS",
    "iban": "FR7613106005003002159831007",
    "banque": "13106",
    "guichet": "00500",
    "compte": "30021598310",
    "cle": "07",
    "agence": "TOULOUSE 31",
}


def format_iban(iban: str):
    iban = re.sub(r"\s+", "", iban).upper()
    return " ".join(iban[i:i+4] for i in range(0, len(iban), 4))

def text_width(text: str):
    return fitz.get_text_length(text, fontsize=FONT_SIZE)

def insert(page, key, text, anchor_end_x=None):
    rects = page.search_for(key)

    for r in rects:
        page.add_redact_annot(
            fitz.Rect(r.x0 - 0.5, r.y0 - 0.5, r.x1 + 0.5, r.y1 + 0.5),
            fill=(1, 1, 1),
        )

    if rects:
        page.apply_redactions()

    end_x = anchor_end_x

    for r in rects:
        w = text_width(text)

        if anchor_end_x:
            x = anchor_end_x - w
        else:
            x = min(r.x0, RIGHT_LIMIT_X - w)
            end_x = x + w

        page.insert_text(
            (x, r.y1 - 2),
            text,
            fontsize=FONT_SIZE,
            fontfile=FONT_FILE,
            color=COLOR,
        )

    return end_x

def generate_ca(data, output_path, is_preview=False):
    agence_val = safe_get(data, "agence", DEFAULTS)
    if not agence_val:
        agence_val = safe_get(data, "bank", DEFAULTS)

    values = {
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
        "*banque": safe_get(data, "banque", DEFAULTS),
        "*guichet": safe_get(data, "guichet", DEFAULTS),
        "*compte": safe_get(data, "compte", DEFAULTS),
        "*cle": safe_get(data, "cle", DEFAULTS),
        "*iban": format_iban(safe_get(data, "iban", DEFAULTS)),
        "*agence": agence_val.upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        anchor_end_x = None

        anchor_end_x = insert(page, "*nomprenom", values["*nomprenom"])
        insert(page, "*adresse", values["*adresse"], anchor_end_x)
        insert(page, "*cpville", values["*cpville"], anchor_end_x)

        for key in ["*banque", "*guichet", "*compte", "*cle", "*iban", "*agence"]:
            insert(page, key, values[key])
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_ca_pdf(data, output_path):
    return generate_ca(data, output_path, is_preview=False)

def generate_ca_preview(data, output_path):
    return generate_ca(data, output_path, is_preview=True)
