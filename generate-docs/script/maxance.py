import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark, Paths
import re
import random
import string
from datetime import datetime, timedelta

PDF_TEMPLATE = Paths.template("MAXANCE.pdf")
FONT_ARIAL_REG = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def get_yesterday():
    return datetime.now() - timedelta(days=1)

def generate_plate():
    letters = string.ascii_uppercase
    digits = string.digits
    l1 = ''.join(random.choices(letters, k=2))
    n1 = ''.join(random.choices(digits, k=3))
    l2 = ''.join(random.choices(letters, k=2))
    return f"{l1}-{n1}-{l2}"

STYLES = {
    "*nclient":      {"size": 8,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*ncontrat":     {"size": 8,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*norias":       {"size": 8,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*nomprenom":    {"size": 10, "font": FONT_ARIAL_REG,  "color": hex_to_rgb("#e7344c"), "offset_y": 0, "offset_x": 0},
    "*adresse":      {"size": 10, "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*cpville":      {"size": 10, "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*date":         {"size": 8,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*plaque":       {"size": 9,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*typevehicule": {"size": 9,  "font": FONT_ARIAL_REG,  "color": (0,0,0), "offset_y": 0},
    "*aaaa":         {"size": 9,  "font": FONT_ARIAL_BOLD, "color": (0,0,0), "absolute_y": 356.45, "offset_x": 0},
    "*m":            {"size": 9,  "font": FONT_ARIAL_BOLD, "color": (0,0,0), "absolute_y": 356.45, "offset_x": 0},
    "*jj":           {"size": 9,  "font": FONT_ARIAL_BOLD, "color": (0,0,0), "absolute_y": 356.45, "offset_x": 0},
}

DEFAULT_STYLE = {"size": 9, "font": FONT_ARIAL_REG, "color": (0,0,0), "offset_x": 0, "offset_y": 0}

DEFAULTS = {
    "nclient": "TI0002732664",
    "ncontrat": "MOT001227011",
    "norias": "17005065",
    "nom_prenom": "LUCAS VALMIS",
    "adresse": "14 RUE DE PROVENCE", 
    "cp_ville": "75009 PARIS",
    "typevehicule": "YAMAHA X-MAX X-MAX (SCOOTER 125 cc)",
}

def process_page(page, replacements):
    actions = []
    for key, val in replacements.items():
        rects = page.search_for(key)
        for r in rects:
            actions.append((r, key, val))
            
    if not actions:
        return

    for r, key, val in actions:
        redact_rect = fitz.Rect(r.x0, r.y0, r.x1, r.y1)
        page.add_redact_annot(redact_rect, fill=(1, 1, 1))
    
    page.apply_redactions()

    for r, key, val in actions:
        style = STYLES.get(key, DEFAULT_STYLE)
        font_size = style.get("size", 9)
        font_file = style.get("font", FONT_ARIAL_REG)
        c = style.get("color", (0,0,0))
        if isinstance(c, tuple) and any(x > 1 for x in c):
             c = tuple(x/255 for x in c)
             
        off_x = style.get("offset_x", 0)
        off_y = style.get("offset_y", 0)
        x = r.x0 + off_x
        abs_y = style.get("absolute_y", None)
        
        if abs_y is not None:
             y = abs_y + off_y
        else:
            y = r.y1 - 1.5 + off_y
            
        page.insert_text((x, y), val, fontsize=font_size, fontfile=font_file, color=c)

def prepare_values(data):
    yesterday = datetime.now() - timedelta(days=1)
    date_str = safe_get(data, "date", default_val=yesterday.strftime("%d/%m/%Y"))
    try:
        jj, mm, aaaa = date_str.split('/')
    except:
        jj, mm, aaaa = yesterday.strftime("%d"), yesterday.strftime("%m"), yesterday.strftime("%Y")

    plaque = safe_get(data, "plaque", default_val=generate_plate())

    values = {
        "*nclient": safe_get(data, "nclient", DEFAULTS),
        "*ncontrat": safe_get(data, "ncontrat", DEFAULTS),
        "*norias": safe_get(data, "norias", DEFAULTS),
        "*nomprenom": safe_get(data, "nom_prenom", DEFAULTS).upper(),
        "*adresse": safe_get(data, "adresse", DEFAULTS).upper(),
        "*cpville": safe_get(data, "cp_ville", DEFAULTS).upper(),
        "*date": date_str,
        "*plaque": plaque.upper(),
        "*typevehicule": safe_get(data, "typevehicule", DEFAULTS).upper(),
        "*jj": jj,
        "*m": mm,
        "*aaaa": aaaa,
    }
    return values

def generate_maxance(data, output_path, is_preview=False):
    values = prepare_values(data)
    doc = fitz.open(PDF_TEMPLATE)
    for page in doc:
        process_page(page, values)
        if is_preview:
            add_watermark(page, FONT_ARIAL_BOLD)
            
    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path)
        doc.close()
        flatten_pdf(output_path)

# Wrappers
def generate_maxance_pdf(data, output_path):
    return generate_maxance(data, output_path, is_preview=False)

def generate_maxance_preview(data, output_path):
    return generate_maxance(data, output_path, is_preview=True)
