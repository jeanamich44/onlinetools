import fitz
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "ASSURANCE.pdf")
FONT_ARIAL_REG = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

FONT_REG = "ARIAL_REG"
FONT_BOLD = "ARIAL_BOLD"

COLOR_RED = (231/255, 52/255, 76/255)
COLOR_BLACK = (0, 0, 0)


def format_nomprenom(v: str):
    parts = v.strip().split()
    if len(parts) == 1:
        return parts[0].capitalize()
    return f"{parts[0].capitalize()} {' '.join(parts[1:]).upper()}"


def wipe_and_write(page, rect, text, font, size, color, y_override=None):
    page.draw_rect(rect, fill=(1, 1, 1), width=0)
    y = y_override if y_override is not None else (rect.y1 - 1.5)
    page.insert_text(
        (rect.x0, y),
        text,
        fontsize=size,
        fontname=font,
        color=color,
    )


def generate_assurance_pdf(data, output_path):
    date_val = datetime.date.today() - datetime.timedelta(days=1)

    DATA = {
        "*nomprenom": format_nomprenom(data.nom_prenom or "Antoine LABRIT"),
        "*adresse": data.adresse or "12 RUE DE PROVENCE",
        "*cpville": data.cp_ville or "75009 PARIS",
        "*nclient": data.nclient or "TI0002722652",
        "*ncontrat": data.ncontrat or "MOT001227011",
        "*norias": data.norias or "17005124",
        "*date": date_val.strftime("%d/%m/%Y"),
        "*jj": date_val.strftime("%d"),
        "*m": date_val.strftime("%m"),
        "*aaaa": date_val.strftime("%Y"),
        "*plaque": data.plaque or "ZA-974-HJ",
        "*typevehicule": data.typevehicule or "X-MAX X-MAX (Scooter 125 cc)",
    }

    doc = fitz.open(PDF_TEMPLATE)

    for page in doc:
        page.insert_font(FONT_REG, FONT_ARIAL_REG)
        page.insert_font(FONT_BOLD, FONT_ARIAL_BOLD)

        jj = page.search_for("*jj")
        m = page.search_for("*m")
        aaaa = page.search_for("*aaaa")

        base_y = None
        for lst in (jj, m, aaaa):
            if lst:
                base_y = lst[0].y1 - 1.5
                break

        MAP = {
            "*nomprenom": (FONT_REG, 10, COLOR_RED),
            "*adresse": (FONT_REG, 10, COLOR_BLACK),
            "*cpville": (FONT_REG, 10, COLOR_BLACK),
            "*nclient": (FONT_REG, 8, COLOR_BLACK),
            "*ncontrat": (FONT_REG, 8, COLOR_BLACK),
            "*norias": (FONT_REG, 8, COLOR_BLACK),
            "*date": (FONT_REG, 8, COLOR_BLACK),
            "*plaque": (FONT_REG, 9, COLOR_BLACK),
            "*typevehicule": (FONT_REG, 9, COLOR_BLACK),
        }

        for key, (font, size, color) in MAP.items():
            for r in page.search_for(key):
                wipe_and_write(page, r, DATA[key], font, size, color)

        for key in ("*jj", "*m", "*aaaa"):
            for r in page.search_for(key):
                wipe_and_write(
                    page,
                    r,
                    DATA[key],
                    FONT_BOLD,
                    9,
                    COLOR_BLACK,
                    y_override=base_y,
                )

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
