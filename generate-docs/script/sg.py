import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths

PDF_TEMPLATE = Paths.template("SG.pdf")
FONT_FILE = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

FONT_NAME = "Arial"
COLOR = (0, 0, 0)

DEFAULTS = {
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "agence": "AULNAY SOUS BOIS CENTRE",
    "agence_adresse": "29 BOULEVARD HAUSSMANN",
    "agence_cp_ville": "75009 PARIS",
    "banque": "30003",
    "guichet": "01894",
    "compte": "12345678901",
    "cle": "52",
    "iban": "FR7630003018941234567890152",
    "bic": "SOGEFRPP",
}

FONT_SIZES = {
    "nom prenom": 10.5,
    "adresse": 10.5,
    "cp ville": 10.5,
    "agence": 10.5,
    "adagence": 10.5,
    "cpvagence": 10.5,
    "banque": 12,
    "guichet": 12,
    "compte": 12,
    "cle": 12,
    "iban": 12,
    "bic": 12,
}


def generate_sg(data, output_path, is_preview=False):
    titre = "M. " if (data.sexe or "m").lower() == "m" else "Mme. "

    values = {
        "nom prenom": titre + (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "agence": (data.agence or DEFAULTS["agence"]).upper(),
        "adagence": (data.agence_adresse or DEFAULTS["agence_adresse"]).upper(),
        "cpvagence": (data.agence_cp_ville or DEFAULTS["agence_cp_ville"]).upper(),
        "banque": (data.banque or DEFAULTS["banque"]).upper(),
        "guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "compte": (data.compte or DEFAULTS["compte"]).upper(),
        "cle": (data.cle or DEFAULTS["cle"]).upper(),
        "iban": " ".join((data.iban or DEFAULTS["iban"]).replace(" ", "")[i:i+4] for i in range(0, 34, 4)),
        "bic": (data.bic or DEFAULTS["bic"]).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(fontname=FONT_NAME, fontfile=FONT_FILE)

        align_ref = page.search_for("Agence de domiciliation")
        x_align = align_ref[0].x1 if align_ref else 515.0

        for key, text in values.items():
            for rect in page.search_for(f"*{key}"):
                page.draw_rect(rect, fill=(1, 1, 1), width=0)
                fontsize = FONT_SIZES.get(key, 9)

                x = rect.x0
                if key in ["agence", "adagence", "cpvagence"]:
                    w = fitz.get_text_length(text, "helv", fontsize)
                    x = x_align - w - 2

                page.insert_text(
                    (x, rect.y1 - 2),
                    text,
                    fontsize=fontsize,
                    fontname=FONT_NAME,
                    color=COLOR,
                )
        
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_sg_pdf(data, output_path):
    return generate_sg(data, output_path, is_preview=False)

def generate_sg_preview(data, output_path):
    return generate_sg(data, output_path, is_preview=True)
