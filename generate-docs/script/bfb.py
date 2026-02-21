from .preview_utils import save_pdf_as_jpg
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "BFB.pdf")
FONT_ARIAL_REG = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

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


def add_watermark(page):
    rect = page.rect
    text = "PREVIEW – NON PAYÉ"

    for y in range(80, int(rect.height), 160):
        page.insert_text(
            (40, y),
            text,
            fontsize=42,
            fontfile=FONT_ARIAL_BOLD,
            color=(0.55, 0.55, 0.55),
            fill_opacity=0.5,
        )


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

def generate_bfb_pdf(data, output_path):
    iban_raw = data.iban or DEFAULTS["iban"]
    iban_fmt = format_iban(iban_raw)

    auto = parse_french_iban(iban_raw)

    values = {
        "*nom prenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*nnom prenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "*iban": iban_fmt,
    }

    if auto:
        values["*banque"] = auto["banque"]
        values["*guichet"] = auto["guichet"]
        values["*compte"] = auto["compte"]
        values["*cle"] = auto["cle"]
    else:
        values["*banque"] = data.banque or DEFAULTS["banque"]
        values["*guichet"] = data.guichet or DEFAULTS["guichet"]
        values["*compte"] = data.compte or DEFAULTS["compte"]
        values["*cle"] = data.cle or DEFAULTS["cle"]

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

    doc.save(output_path)
    doc.close()


def generate_bfb_preview(data, output_path):
    iban_raw = data.iban or DEFAULTS["iban"]
    iban_fmt = format_iban(iban_raw)

    auto = parse_french_iban(iban_raw)

    values = {
        "*nom prenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*nnom prenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "*iban": iban_fmt,
    }

    if auto:
        values["*banque"] = auto["banque"]
        values["*guichet"] = auto["guichet"]
        values["*compte"] = auto["compte"]
        values["*cle"] = auto["cle"]
    else:
        values["*banque"] = data.banque or DEFAULTS["banque"]
        values["*guichet"] = data.guichet or DEFAULTS["guichet"]
        values["*compte"] = data.compte or DEFAULTS["compte"]
        values["*cle"] = data.cle or DEFAULTS["cle"]

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
        
        add_watermark(page)

    save_pdf_as_jpg(doc, output_path)
