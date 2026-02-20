import fitz
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "LBP.pdf")
FONT_FILE = os.path.join(BASE_DIR, "font", "arialbd.ttf")

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
}


def add_watermark(page):
    rect = page.rect
    text = "PREVIEW – NON PAYÉ"

    for y in range(80, int(rect.height), 160):
        page.insert_text(
            (40, y),
            text,
            fontsize=42,
            fontname=FONT_NAME,
            color=(0.55, 0.55, 0.55),
            fill_opacity=0.5,
        )


def generate_lbp_pdf(data, output_path):
    titre = "MR" if (data.sexe or "m").lower() == "m" else "MME"
    

    values = {
        "banque": (data.banque or DEFAULTS["banque"]).upper(),
        "guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "compte": (data.compte or DEFAULTS["compte"]).upper(),
        "cle": (data.cle or DEFAULTS["cle"]).upper(),
        "iban": " ".join(
            (data.iban or DEFAULTS["iban"])
            .replace(" ", "")
            .upper()[i:i+4]
            for i in range(0, len((data.iban or DEFAULTS["iban"]).replace(" ", "")), 4)
        ),
        "bic": " ".join((data.bic or DEFAULTS["bic"]).replace(" ", "").upper()),
        "nom prenom": f"{titre} {(data.nom_prenom or DEFAULTS['nom_prenom']).upper()}",
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "domiciliation": (data.domiciliation or DEFAULTS["domiciliation"]).upper(),
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

    doc.save(output_path)
    doc.close()


def generate_lbp_preview(data, output_path):
    titre = "MR" if (data.sexe or "m").lower() == "m" else "MME"
    

    values = {
        "banque": (data.banque or DEFAULTS["banque"]).upper(),
        "guichet": (data.guichet or DEFAULTS["guichet"]).upper(),
        "compte": (data.compte or DEFAULTS["compte"]).upper(),
        "cle": (data.cle or DEFAULTS["cle"]).upper(),
        "iban": " ".join(
            (data.iban or DEFAULTS["iban"])
            .replace(" ", "")
            .upper()[i:i+4]
            for i in range(0, len((data.iban or DEFAULTS["iban"]).replace(" ", "")), 4)
        ),
        "bic": " ".join((data.bic or DEFAULTS["bic"]).replace(" ", "").upper()),
        "nom prenom": f"{titre} {(data.nom_prenom or DEFAULTS['nom_prenom']).upper()}",
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cp ville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "domiciliation": (data.domiciliation or DEFAULTS["domiciliation"]).upper(),
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
        
        add_watermark(page)

    # Conversion de la première page en image JPG (optimisée)
    page = doc[0]
    # Un zoom de 1.8x offre une excellente netteté sur mobile et desktop
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
    
    # sauvegarde directe en JPG avec qualité contrôlée (natif PyMuPDF)
    pix.save(output_path, jpg_quality=75)
    
    doc.close()
