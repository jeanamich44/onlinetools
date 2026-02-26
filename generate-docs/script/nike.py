import fitz
import os
from .p_utils import save_pdf_as_jpg, flatten_pdf, add_watermark
import random
import string
from datetime import datetime

# =========================
# DOSSIER BASE
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_TEMPLATE = os.path.join(BASE_DIR, "base", "NIKE.pdf")
FONT_ARIAL = os.path.join(BASE_DIR, "font", "arial.ttf")

# =========================
# UTILS
# =========================

def generer_num_aleatoire(longueur=8):
    return ''.join(random.choices(string.digits, k=longueur))

# =========================
# STYLES
# =========================

STYLE_DEFAUT = {"size": 8.0, "font": FONT_ARIAL, "color": (0, 0, 0)}

STYLES = {
    "*nfacture":      STYLE_DEFAUT,
    "*ncommande":     STYLE_DEFAUT,
    "*nomprenom":    STYLE_DEFAUT,
    "*adresse":      STYLE_DEFAUT,
    "*cpville":      STYLE_DEFAUT,
    "*date":         STYLE_DEFAUT,
    "*prixbb":       STYLE_DEFAUT,
    "*tva":          STYLE_DEFAUT,
    "*prixx":        STYLE_DEFAUT,
    "*moyenpaiement": STYLE_DEFAUT,
    "*idproduit1":   STYLE_DEFAUT,
    "*desc1":        STYLE_DEFAUT,
    "*desc1suite":   STYLE_DEFAUT,
    "*quan1":        STYLE_DEFAUT,
    "*prixbrut1":    STYLE_DEFAUT,
    "*prixnet1":     STYLE_DEFAUT,
    "*prixtotal1":   STYLE_DEFAUT,
    "*idproduit2":   STYLE_DEFAUT,
    "*desc2":        STYLE_DEFAUT,
    "*desc2suite":   STYLE_DEFAUT,
    "*quan2":        STYLE_DEFAUT,
    "*prixbrut2":    STYLE_DEFAUT,
    "*prixnet2":     STYLE_DEFAUT,
    "*prixtotal2":   STYLE_DEFAUT,
}

# =========================
# LOGIQUE
# =========================

def traiter_page(page, remplacements):
    """Effectue les remplacements sur une page."""
    actions = []
    
    for cle, val in remplacements.items():
        if not cle or not val: continue
        rects = page.search_for(cle)
        for r in rects:
            actions.append((r, cle, val))
            
    if not actions:
        return

    # 1. Masquage
    for r, cle, val in actions:
        page.add_redact_annot(r, fill=(1, 1, 1))
    page.apply_redactions()

    # 2. Écriture
    for r, cle, val in actions:
        style = STYLES.get(cle, STYLE_DEFAUT)
        taille = style.get("size", 8.0)
        police = style.get("font", FONT_ARIAL)
        couleur = style.get("color", (0, 0, 0))
        
        y = r.y1 - 1.5
        page.insert_text(
            (r.x0, y),
            str(val),
            fontsize=taille,
            fontfile=police,
            color=couleur,
        )

# =========================
# GÉNÉRATEURS
# =========================

def preparer_valeurs(data):
    """Prépare le dictionnaire de valeurs à partir de l'objet data."""
    maintenant = datetime.now()
    
    # Récupération des données ou valeurs par défaut
    total_str = str(getattr(data, "prixx", None) or "129.99").replace("€", "").replace(",", ".").strip()
    try:
        total_ttc = float(total_str)
    except:
        total_ttc = 129.99
        
    total_ht = total_ttc / 1.2
    tva = total_ttc - total_ht
    
    valeurs = {
        "*nfacture": str(getattr(data, "nfacture", None) or ("F" + generer_num_aleatoire(10))),
        "*ncommande": str(getattr(data, "ncommande", None) or ("C" + generer_num_aleatoire(10))),
        "*nomprenom": (str(getattr(data, "nom_prenom", None) or "JEAN DUPONT")).upper(),
        "*adresse": (str(getattr(data, "adresse", None) or "10 RUE DE LA PAIX")).upper(),
        "*cpville": (str(getattr(data, "cp_ville", None) or "75001 PARIS")).upper(),
        "*date": str(getattr(data, "date", None) or maintenant.strftime("%d/%m/%Y")),
        "*prixbb": f"{total_ht:.2f} €",
        "*tva": f"{tva:.2f} €",
        "*prixx": f"{total_ttc:.2f} €",
        "*moyenpaiement": (str(getattr(data, "moyenpaiement", None) or "CARTE DE CRÉDIT")).upper(),
        
        "*idproduit1": str(getattr(data, "idproduit1", None) or "DJ6188-002"),
        "*desc1": (str(getattr(data, "desc1", None) or "NIKE AIR FORCE 1 '07")).upper(),
        "*desc1suite": str(getattr(data, "desc1suite", None) or "BLACK/WHITE-BLACK"),
        "*quan1": str(getattr(data, "quan1", None) or "1"),
        "*prixbrut1": f"{total_ttc:.2f} €",
        "*prixnet1": f"{total_ttc:.2f} €",
        "*prixtotal1": f"{total_ttc:.2f} €",
        
        "*idproduit2": "",
        "*desc2": "",
        "*desc2suite": "",
        "*quan2": "",
        "*prixbrut2": "",
        "*prixnet2": "",
        "*prixtotal2": "",
    }
    return valeurs

def generate_nike(data, output_path, is_preview=False):
    valeurs = preparer_valeurs(data)
    doc = fitz.open(PDF_TEMPLATE)
    for page in doc:
        traiter_page(page, valeurs)
        if is_preview:
            add_watermark(page, FONT_ARIAL)
            
    if is_preview:
        save_pdf_as_jpg(doc, output_path)
    else:
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        flatten_pdf(output_path)

# Wrappers
def generate_nike_pdf(data, output_path):
    """Génère le PDF final pour Nike."""
    return generate_nike(data, output_path, is_preview=False)

def generate_nike_preview(data, output_path):
    """Génère la preview pour Nike."""
    return generate_nike(data, output_path, is_preview=True)
