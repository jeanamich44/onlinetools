import fitz
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "ASSURANCE.pdf")
FONT_REG_FILE = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_BOLD_FILE = os.path.join(BASE_DIR, "font", "arialbd.ttf")

FONT_REG = "ArialReg"
FONT_BOLD = "ArialBold"

COLOR_RED = (231 / 255, 52 / 255, 76 / 255)
COLOR_BLACK = (0, 0, 0)

DEFAULTS = {
    "nom_prenom": "ANTOINE LABRIT",
    "adresse": "12 RUE DE PROVENCE",
    "cp_ville": "75009 PARIS",
    "nclient": "TI0002722652",
    "ncontrat": "MOT001227011",
    "norias": "17005124",
    "plaque": "ZA-974-HJ",
    "typevehicule": "X-MAX X-MAX (Scooter 125 cc)",
}


def generate_assurance_pdf(data, output_path):
    date_val = datetime.date.today() - datetime.timedelta(days=1)

    values = {
        "nomprenom": (data.nom_prenom or DEFAULTS["nom_prenom"]).upper(),
        "adresse": (data.adresse or DEFAULTS["adresse"]).upper(),
        "cpville": (data.cp_ville or DEFAULTS["cp_ville"]).upper(),
        "nclient": (data.nclient or DEFAULTS["nclient"]).upper(),
        "ncontrat": (data.ncontrat or DEFAULTS["ncontrat"]).upper(),
        "norias": (data.norias or DEFAULTS["norias"]).upper(),
        "date": date_val.strftime("%d/%m/%Y"),
        "jj": date_val.strftime("%d"),
        "m": date_val.strftime("%m"),
        "aaaa": date_val.strftime("%Y"),
        "plaque": (data.plaque or DEFAULTS["plaque"]).upper(),
        "typevehicule": (data.typevehicule or DEFAULTS["typevehicule"]).upper(),
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(fontname=FONT_REG, fontfile=FONT_REG_FILE)
        page.insert_font(fontname=FONT_BOLD, fontfile=FONT_BOLD_FILE)

        for key, text in values.items():
            for rect in page.search_for(f"*{key}"):
                page.draw_rect(rect, fill=(1, 1, 1), width=0)
                page.insert_text(
                    (rect.x0, rect.y1 - 2),
                    text,
                    fontsize=9 if key in ("jj", "m", "aaaa") else 10,
                    fontname=FONT_BOLD if key in ("jj", "m", "aaaa") else FONT_REG,
                    color=COLOR_RED if key == "nomprenom" else COLOR_BLACK,
                )

    doc.save(output_path)
    doc.close()
