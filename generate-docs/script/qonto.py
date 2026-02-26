import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get
import re

PDF_TEMPLATE = Paths.template("QONTO.pdf")
FONT_ARIAL_REG_PATH = Paths.font("arial.ttf")
FONT_ARIAL_BOLD_PATH = Paths.font("arialbd.ttf")

FONT_REG = "ARIAL_REG"
FONT_BOLD = "ARIAL_BOLD"

COLOR_MAIN = (29/255, 29/255, 27/255)
COLOR_SECOND = (99/255, 99/255, 96/255)

DEFAULTS = {
    "iban": "FR7630004008001234567890152",
    "banque": "30004",
    "guichet": "00800",
    "compte": "12345678901",
    "cle": "52",
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
}

def format_iban(v):
    v = re.sub(r"\s+", "", v or "").upper()
    return " ".join(v[i:i+4] for i in range(0, len(v), 4))

def wipe_and_write(page, rect, text, font, size, color):
    page.draw_rect(rect, fill=(1, 1, 1), width=0)
    page.insert_text(
        (rect.x0, rect.y1 - 1.5),
        text,
        fontsize=size,
        fontname=font,
        color=color,
    )


def generate_qonto(data, output_path, is_preview=False):
    values = {
        "*iban": format_iban(safe_get(data, "iban", DEFAULTS)),
        "*banque": safe_get(data, "banque", DEFAULTS),
        "*guichet": safe_get(data, "guichet", DEFAULTS),
        "*compte": safe_get(data, "compte", DEFAULTS),
        "*cle": safe_get(data, "cle", DEFAULTS),
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG, FONT_ARIAL_REG_PATH)
        page.insert_font(FONT_BOLD, FONT_ARIAL_BOLD_PATH)

        name_rects = page.search_for("*nomprenom")

        if len(name_rects) >= 1:
            wipe_and_write(page, name_rects[0], values["*nomprenom"], FONT_BOLD, 7.5, COLOR_SECOND)

        if len(name_rects) >= 2:
            wipe_and_write(page, name_rects[1], values["*nomprenom"], FONT_REG, 9, COLOR_MAIN)

        MAP = {
            "*iban":   (FONT_REG, 10.5, COLOR_MAIN, ""),
            "*banque": (FONT_REG, 6, COLOR_SECOND, "Banque  "),
            "*guichet":(FONT_REG, 6, COLOR_SECOND, "Guichet  "),
            "*compte": (FONT_REG, 6, COLOR_SECOND, "Compte  "),
            "*cle":    (FONT_REG, 6, COLOR_SECOND, "Clé  "),
            "*adresse":(FONT_REG, 9, COLOR_MAIN, ""),
            "*cpville":(FONT_REG, 9, COLOR_MAIN, ""),
        }

        for key, (font, size, color, prefix) in MAP.items():
            for r in page.search_for(key):
                wipe_and_write(page, r, prefix + values[key], font, size, color)
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD_PATH)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_qonto_pdf(data, output_path):
    return generate_qonto(data, output_path, is_preview=False)

def generate_qonto_preview(data, output_path):
    return generate_qonto(data, output_path, is_preview=True)
