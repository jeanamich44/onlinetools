import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths, FONT_ARIAL_BOLD, safe_get

PDF_TEMPLATE = Paths.template("LBP.pdf")
FONT_FILE = Paths.font("arialbd.ttf")

FONT_NAME = "ArialBold"
FONT_SIZE = 9
COLOR = (0, 0, 0)

DEFAULTS = {
    "banque": "20041",
    "guichet": "01007",
    "compte": "1852185T038",
    "cle": "52",
    "iban": "FR6720041010071852185T03852",
    "bic": "PSSTFRPPLYO",
    "nom_prenom": "GOULIET ANTOINE",
    "adresse": "14 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "domiciliation": "LA BANQUE POSTALE LYON CENTRE FINANCIER",
    "sexe": "m",
}


def generate_lbp(data, output_path, is_preview=False):
    sexe = safe_get(data, "sexe", DEFAULTS).lower()
    titre = "MR" if sexe == "m" else "MME"
    
    iban_raw = safe_get(data, "iban", DEFAULTS).replace(" ", "").upper()
    bic_raw = safe_get(data, "bic", DEFAULTS).replace(" ", "").upper()

    values = {
        "banque": safe_get(data, "banque", DEFAULTS).upper(),
        "guichet": safe_get(data, "guichet", DEFAULTS).upper(),
        "compte": safe_get(data, "compte", DEFAULTS).upper(),
        "cle": safe_get(data, "cle", DEFAULTS).upper(),
        "iban": " ".join(iban_raw[i:i+4] for i in range(0, len(iban_raw), 4)),
        "bic": " ".join(bic_raw),
        "nom prenom": f"{titre} {safe_get(data, 'nom_prenom', DEFAULTS).upper()}",
        "adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "cp ville": safe_get(data, "cp_ville", DEFAULTS).upper(),
        "domiciliation": safe_get(data, "domiciliation", DEFAULTS).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(fontname=FONT_NAME, fontfile=FONT_FILE)

        for key, text in values.items():
            for rect in page.search_for(f"*{key}"):
                page.draw_rect(rect, fill=(1, 1, 1), width=0)
                page.insert_text(
                    (rect.x0, rect.y1 - 2),
                    text,
                    fontsize=FONT_SIZE,
                    fontname=FONT_NAME,
                    color=COLOR,
                )
        
        if is_preview:
            add_watermark(page, FONT_FILE)

    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path)
        doc.close()
        flatten_pdf(output_path)

# Wrappers pour compatibilité main.py
def generate_lbp_pdf(data, output_path):
    return generate_lbp(data, output_path, is_preview=False)

def generate_lbp_preview(data, output_path):
    return generate_lbp(data, output_path, is_preview=True)
