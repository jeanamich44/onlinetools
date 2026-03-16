import fitz
import os

# =========================
# GESTION DES CHEMINS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Paths:
    BASE = BASE_DIR
    FONTS = os.path.join(BASE_DIR, "font")
    TEMPLATES = os.path.join(BASE_DIR, "base")
    
    @classmethod
    def font(cls, name):
        return os.path.join(cls.FONTS, name)
    
    @classmethod
    def template(cls, name):
        return os.path.join(cls.TEMPLATES, name)


FONT_ARIAL = Paths.font("arial.ttf")
FONT_ARIAL_BOLD = Paths.font("arialbd.ttf")

RIB_BASE = {
    "nom_prenom": "JEAN MICHEL BERNARD",
    "adresse": "8 PLACE DE LA CONCORDE",
    "cp_ville": "75006 PARIS",
    "cp": "75006",
    "ville": "PARIS",
    "telephone": "0635251420",
    "sexe": "m",
}

RIB_BANKS = {
    "CA": {
        "iban": "FR7613106005003002159831007",
        "banque": "13106",
        "guichet": "00500",
        "compte": "30021598310",
        "cle": "07",
        "agence": "TOULOUSE 31",
    },
    "REVOLUT": {
        "iban": "FR7630004008001234567890152",
        "bic": "REVOFR22",
        "depart": "Paris",
        "banque": "30004",
        "guichet": "00800",
        "compte": "12345678901",
        "cle": "52",
    },
    "CM": {
        "banque": "10278",
        "guichet": "02100",
        "compte": "00012345678",
        "cle": "45",
        "iban": "FR761027802100001234567845",
        "agence1": "AGENCE CRÉDIT MUTUEL",
        "agence2": "AGENCE CRÉDIT MUTUEL",
        "agenceadresse": "14 RUE DES LILAS",
        "agencecpville": "31000 TOULOUSE",
    },
    "BFB": {
        "banque": "30004",
        "guichet": "00800",
        "compte": "12345678901",
        "cle": "52",
        "iban": "FR7630004008001234567890152",
    },
    "CIC": {
        "banque": "30066",
        "guichet": "10278",
        "compte": "00012345678",
        "cle": "45",
        "iban": "FR7630066102780001234567845",
        "agence1": "AGENCE TOULOUSE CENTRE",
        "agence2": "CIC",
        "agenceadresse": "14 RUE ALSACE LORRAINE",
        "agencecpville": "31000 TOULOUSE",
        "agence": "AGENCE TOULOUSE CENTRE",
        "agence_adresse": "14 RUE ALSACE LORRAINE",
        "agence_cp_ville": "31000 TOULOUSE",
    },
    "SG": {
        "agence": "AULNAY SOUS BOIS CENTRE",
        "agence_adresse": "29 BOULEVARD HAUSSMANN",
        "agence_cp_ville": "75009 PARIS",
        "banque": "30003",
        "guichet": "01894",
        "compte": "12345678901",
        "cle": "52",
        "iban": "FR7630003018941234567890152",
        "bic": "SOGEFRPP",
    },
    "LBP": {
        "banque": "20041",
        "guichet": "01007",
        "compte": "1852185T038",
        "cle": "52",
        "iban": "FR6720041010071852185T03852",
        "bic": "PSSTFRPPLYO",
        "domiciliation": "LA BANQUE POSTALE LYON CENTRE FINANCIER",
    },
    "QONTO": {
        "iban": "FR7630004008001234567890152",
        "banque": "30004",
        "guichet": "00800",
        "compte": "12345678901",
        "cle": "52",
    }
}

def get_rib_defaults(bank_name):
    defaults = RIB_BASE.copy()
    defaults.update(RIB_BANKS.get(bank_name, {}))
    return defaults

def safe_get(data, key, defaults=None, default_val=""):
    val = getattr(data, key, None)
    if val is None or str(val).strip() == "":
        if defaults and key in defaults:
            val = defaults[key]
        else:
            val = default_val
    return str(val).strip()

DEPARTEMENTS = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube",
    "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal",
    "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard",
    "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine",
    "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura", "40": "Landes",
    "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret",
    "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche",
    "51": "Marne", "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme",
    "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne",
    "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "976": "Mayotte"
}

def get_departement_name(data, defaults=None):
    if defaults is None:
        defaults = {}
    cp = safe_get(data, "depart", None)
    if not cp:
        cp = safe_get(data, "cp", defaults)
    if not cp: return ""
    
    cp_str = str(cp).strip().upper()
    if cp_str in ["2A", "2B"]:
        code = cp_str
    elif cp_str.startswith("97"):
        code = cp_str[:3]
    else:
        code = cp_str[:2]
        if code == "20":
            try:
                if int(cp_str) < 20200: code = "2A"
                else: code = "2B"
            except:
                pass
                
    return DEPARTEMENTS.get(code, cp_str)

# =========================
# UTILITAIRES PDF
# =========================

def save_pdf_as_jpg(doc, output_path, zoom=1.8, quality=75):
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(output_path, jpg_quality=quality)
    doc.close()

def flatten_pdf(file_path):
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

def mask_chronopost_account(doc, account_id="15972103"):
    if not account_id:
        return

    account_id_str = str(account_id)
    
    texts_to_hide = [
        f"Account : {account_id_str}",
        f"Account :{account_id_str}",
        f"Account: {account_id_str}",
        f"Account:{account_id_str}",
        "Account :",
        "Account:",
        "Account",
        account_id_str
    ]
    
    for page in doc:
        for text in texts_to_hide:
            rects = page.search_for(text)
            for rect in rects:
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

