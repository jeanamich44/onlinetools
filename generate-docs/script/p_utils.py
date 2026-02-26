import fitz
import os

# =========================
# GESTION DES CHEMINS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Paths:
    """Centralise tous les chemins du projet."""
    BASE = BASE_DIR
    FONTS = os.path.join(BASE_DIR, "font")
    TEMPLATES = os.path.join(BASE_DIR, "base")
    
    @classmethod
    def font(cls, name):
        """Retourne le chemin complet d'une police."""
        return os.path.join(cls.FONTS, name)
    
    @classmethod
    def template(cls, name):
        """Retourne le chemin complet d'un modèle PDF."""
        return os.path.join(cls.TEMPLATES, name)

# Raccourcis pour les polices communes
FONT_ARIAL = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

def safe_get(data, key, defaults=None, default_val=""):
    """
    Récupère une valeur de manière sécurisée depuis un objet data.
    Si absente ou vide, cherche dans le dictionnaire defaults.
    """
    val = getattr(data, key, None)
    if val is None or str(val).strip() == "":
        if defaults and key in defaults:
            val = defaults[key]
        else:
            val = default_val
    return str(val).strip()

# =========================
# UTILITAIRES PDF
# =========================

def save_pdf_as_jpg(doc, output_path, zoom=1.8, quality=75):
    """
    Convertit la première page d'un document PDF en image JPG optimisée pour la preview.
    """
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(output_path, jpg_quality=quality)
    doc.close()

def flatten_pdf(file_path):
    """
    Rend le PDF non modifiable (aplatissement).
    """
    doc = fitz.open(file_path)
    new_doc = fitz.open()

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, pixmap=pix)

    doc.close()
    new_doc.save(file_path, garbage=4, deflate=True)
    new_doc.close()

def add_watermark(page, font_file=FONT_ARIAL_BOLD, text="PREVIEW – NON PAYÉ"):
    """
    Ajoute un filigrane de prévisualisation.
    """
    rect = page.rect
    for y in range(80, int(rect.height), 160):
        page.insert_text(
            (40, y),
            text,
            fontsize=42,
            fontfile=font_file,
            color=(0.55, 0.55, 0.55),
            fill_opacity=0.5,
        )
