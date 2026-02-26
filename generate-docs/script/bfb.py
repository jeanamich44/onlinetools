import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get
import re

PDF_TEMPLATE = Paths.template("BFB.pdf")
FONT_ARIAL_REG = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

COLOR_MAIN = (29/255, 29/255, 27/255)
COLOR_SECOND = (99/255, 99/255, 96/255)

DEFAULTS = {
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "banque": "30004",
    "guichet": "00800",
    "compte": "12345678901",
    "cle": "52",
    "iban": "FR7630004008001234567890152",
}


def format_iban(iban: str):
    iban = re.sub(r"\s+", "", iban).upper()
    return " ".join(iban[i:i+4] for i in range(0, len(iban), 4))

def parse_french_iban(iban: str):
    iban = re.sub(r"\s+", "", iban).upper()
    if not iban.startswith("FR") or len(iban) < 27:
        return None
    return {
        "banque": iban[4:9],
        "guichet": iban[9:14],
        "compte": iban[14:25],
        "cle": iban[25:27],
    }

def insert_text(page, key, text, style):
    for r in page.search_for(key):
        pad = 0.6
        red = fitz.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad)
        page.add_redact_annot(red, fill=(1, 1, 1))
        page.apply_redactions()

        y_offset = style.get("offset_y", 0)
        write = fitz.Rect(
            r.x0,
            r.y0 - 0.25 * r.height + y_offset,
            page.rect.x1 - 36,
            r.y1 + 0.25 * r.height + y_offset,
        )

        page.insert_textbox(
            write,
            text,
            fontsize=style["size"],
            fontfile=style["font"],
            color=style["color"],
            align=0,
        )

def generate_bfb(data, output_path, is_preview=False):
    iban_raw = safe_get(data, "iban", DEFAULTS).upper()
    auto = parse_french_iban(iban_raw)

    values = {
        "*nom prenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*nnom prenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cp ville": safe_get(data, "cp_ville", DEFAULTS).upper(),
        "*iban": format_iban(iban_raw),
    }

    if auto:
        values["*banque"] = auto["banque"]
        values["*guichet"] = auto["guichet"]
        values["*compte"] = auto["compte"]
        values["*cle"] = auto["cle"]
    else:
        values["*banque"] = safe_get(data, "banque", DEFAULTS)
        values["*guichet"] = safe_get(data, "guichet", DEFAULTS)
        values["*compte"] = safe_get(data, "compte", DEFAULTS)
        values["*cle"] = safe_get(data, "cle", DEFAULTS)

    STYLES = {
        "*nom prenom": {"size": 9, "font": FONT_ARIAL_REG, "color": COLOR_MAIN},
        "*nnom prenom": {"size": 7.5, "font": FONT_ARIAL_BOLD, "color": COLOR_SECOND},
        "*adresse": {"size": 9, "font": FONT_ARIAL_REG, "color": COLOR_MAIN},
        "*cp ville": {"size": 9, "font": FONT_ARIAL_REG, "color": COLOR_MAIN},
        "*banque": {"size": 6, "font": FONT_ARIAL_REG, "color": COLOR_SECOND, "offset_y": 2.0},
        "*guichet": {"size": 6, "font": FONT_ARIAL_REG, "color": COLOR_SECOND, "offset_y": 2.0},
        "*compte": {"size": 6, "font": FONT_ARIAL_REG, "color": COLOR_SECOND, "offset_y": 2.0},
        "*cle": {"size": 6, "font": FONT_ARIAL_REG, "color": COLOR_SECOND, "offset_y": 2.0},
        "*iban": {"size": 10.5, "font": FONT_ARIAL_REG, "color": COLOR_MAIN},
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        for key, val in values.items():
            if key in STYLES:
                insert_text(page, key, val, STYLES[key])
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_bfb_pdf(data, output_path):
    return generate_bfb(data, output_path, is_preview=False)

def generate_bfb_preview(data, output_path):
    return generate_bfb(data, output_path, is_preview=True)
