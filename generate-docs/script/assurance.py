# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import fitz
import datetime
import os
import uuid

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "ASSURANCE.pdf")
FONT_ARIAL_REG = os.path.join(BASE_DIR, "font", "arial.ttf")
FONT_ARIAL_BOLD = os.path.join(BASE_DIR, "font", "arialbd.ttf")

FONT_REG = "ARIAL_REG"
FONT_BOLD = "ARIAL_BOLD"

COLOR_RED = (231/255, 52/255, 76/255)
COLOR_BLACK = (0, 0, 0)


class PDFRequest(BaseModel):
    nomprenom: str | None = None
    adresse: str | None = None
    cpville: str | None = None
    nclient: str | None = None
    ncontrat: str | None = None
    norias: str | None = None
    plaque: str | None = None
    typevehicule: str | None = None
    export: str | None = "png"  # pdf | png


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


@app.post("/generate")
def generate(data: PDFRequest):
    out_id = uuid.uuid4().hex
    out_pdf = f"/tmp/{out_id}.pdf"
    out_png = f"/tmp/{out_id}.png"

    date_val = datetime.date.today() - datetime.timedelta(days=1)

    DATA = {
        "*nomprenom": format_nomprenom(data.nomprenom or "Antoine LABRIT"),
        "*adresse": data.adresse or "12 RUE DE PROVENCE",
        "*cpville": data.cpville or "75009 PARIS",
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

    if data.export == "pdf":
        doc.save(out_pdf, garbage=4, deflate=True, clean=True)
        doc.close()
        return FileResponse(out_pdf, media_type="application/pdf", filename="document.pdf")

    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)
    pix.save(out_png)
    doc.close()

    return FileResponse(out_png, media_type="image/png", filename="document.png")
