import fitz
import os
from .preview_utils import save_pdf_as_jpg, flatten_pdf
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "CA.pdf")
FONT_FILE = os.path.join(BASE_DIR, "font", "opensans-semibold.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

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

def generate_ca_pdf(data, output_path):
    agence_value = data.agence or data.bank or DEFAULTS["agence"]

    values = {
        "*nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "*banque": (data.banque or DEFAULTS["banque"]),
        "*guichet": (data.guichet or DEFAULTS["guichet"]),
        "*compte": (data.compte or DEFAULTS["compte"]),
        "*cle": (data.cle or DEFAULTS["cle"]),
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
        "*agence": agence_value.upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        anchor_end_x = None

        anchor_end_x = insert(page, "*nomprenom", values["*nomprenom"])
        insert(page, "*adresse", values["*adresse"], anchor_end_x)
        insert(page, "*cpville", values["*cpville"], anchor_end_x)

        for key in ["*banque", "*guichet", "*compte", "*cle", "*iban", "*agence"]:
            insert(page, key, values[key])

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    # Sécurisation finale par mise à plat
    flatten_pdf(output_path)


def generate_ca_preview(data, output_path):
    agence_value = data.agence or data.bank or DEFAULTS["agence"]

    values = {
        "*nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "*adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "*cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "*banque": (data.banque or DEFAULTS["banque"]),
        "*guichet": (data.guichet or DEFAULTS["guichet"]),
        "*compte": (data.compte or DEFAULTS["compte"]),
        "*cle": (data.cle or DEFAULTS["cle"]),
        "*iban": format_iban(data.iban or DEFAULTS["iban"]),
        "*agence": agence_value.upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        anchor_end_x = None

        anchor_end_x = insert(page, "*nomprenom", values["*nomprenom"])
        insert(page, "*adresse", values["*adresse"], anchor_end_x)
        insert(page, "*cpville", values["*cpville"], anchor_end_x)

        for key in ["*banque", "*guichet", "*compte", "*cle", "*iban", "*agence"]:
            insert(page, key, values[key])
        
        add_watermark(page)

    save_pdf_as_jpg(doc, output_path)
