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
