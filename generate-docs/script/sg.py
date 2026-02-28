import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, safe_get

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
    "sexe": "m",
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
    sexe = safe_get(data, "sexe", DEFAULTS).lower()
    titre = "M. " if sexe == "m" else "Mme. "

    values = {
        "nom prenom": titre + safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "cp ville": safe_get(data, "cp_ville", DEFAULTS).upper(),
        "agence": safe_get(data, "agence", DEFAULTS).upper(),
        "adagence": safe_get(data, "agence_adresse", DEFAULTS).upper(),
        "cpvagence": safe_get(data, "agence_cp_ville", DEFAULTS).upper(),
        "banque": safe_get(data, "banque", DEFAULTS).upper(),
        "guichet": safe_get(data, "guichet", DEFAULTS).upper(),
        "compte": safe_get(data, "compte", DEFAULTS).upper(),
        "cle": safe_get(data, "cle", DEFAULTS).upper(),
        "iban": " ".join(safe_get(data, "iban", DEFAULTS).replace(" ", "")[i:i+4] for i in range(0, 34, 4)),
        "bic": safe_get(data, "bic", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(fontname=FONT_NAME, fontfile=FONT_FILE)

        align_ref = page.search_for("Agence de domiciliation")
        x_align = align_ref[0].x1 if align_ref else 515.0

        # Tri par longueur décroissante pour éviter les conflits de sous-chaînes
        for key in sorted(values.keys(), key=len, reverse=True):
            text = values[key]
            rects = page.search_for(f"*{key}")
            if not rects:
                continue

            for r in rects:
                page.add_redact_annot(r, fill=(1, 1, 1))
            
            page.apply_redactions()

            for rect in rects:
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
