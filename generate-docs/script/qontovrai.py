import fitz
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "QONTO.pdf")
FONT_ARIAL_REG_PATH = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD_PATH = os.path.join(BASE_DIR, "font", "arialbd.ttf")

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

def generate_qonto_pdf(data, output_path):
    values = {
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
        "*banque": data.banque or DEFAULTS["banque"],
        "*guichet": data.guichet or DEFAULTS["guichet"],
        "*compte": data.compte or DEFAULTS["compte"],
        "*cle": data.cle or DEFAULTS["cle"],
        "*nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG, FONT_ARIAL_REG_PATH)
        page.insert_font(FONT_BOLD, FONT_ARIAL_BOLD_PATH)

        name_rects = page.search_for("*nomprenom")

        if len(name_rects) >= 1:
            wipe_and_write(
                page,
                name_rects[0],
                values["*nomprenom"],
                FONT_BOLD,
                7.5,
                COLOR_SECOND,
            )

        if len(name_rects) >= 2:
            wipe_and_write(
                page,
                name_rects[1],
                values["*nomprenom"],
                FONT_REG,
                9,
                COLOR_MAIN,
            )

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
                wipe_and_write(
                    page,
                    r,
                    prefix + values[key],
                    font,
                    size,
                    color,
                )

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
