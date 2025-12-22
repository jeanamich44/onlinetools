import random
from datetime import datetime, timedelta

# =========================
# ICAO UTILS
# =========================

def char_value_icao(char: str) -> int:
    if char.isdigit():
        return int(char)
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    if char == "<":
        return 0
    raise ValueError(f"Invalid ICAO char: {char}")

def icao_check_digit(data: str) -> str:
    weights = [7, 3, 1]
    return str(
        sum(char_value_icao(c) * weights[i % 3] for i, c in enumerate(data)) % 10
    )

def normalize_name(name: str) -> str:
    return name.upper().replace(" ", "<")

# =========================
# RANDOM DATA
# =========================

PRENOMS_M = [
        "GABRIEL", "RAPHAEL", "LEO", "LOUIS", "MAEL", "NOAH", "JULES", "ADAM", "ARTHUR", "ISAAC",
        "LIAM", "SACHA", "EDEN", "LUCAS", "GABIN", "LEON", "MOHAMED", "HUGO", "NAEL", "NOE",
        "MARCEAU", "AARON", "PAUL", "ETHAN", "AYDEN", "NATHAN", "MARIUS", "THEO", "IBRAHIM", "MALO",
        "ELIO", "TOM", "NINO", "VICTOR", "MARTIN", "ELIOTT", "MATHIS", "LYAM", "GASPARD", "IMRAN",
        "MILO", "AUGUSTIN", "ROBIN", "VALENTIN", "TIMEO", "AXEL", "LEANDRE", "ANTOINE", "NOLAN", "TIAGO",
        "SOHAN", "COME", "KAIS", "RAYAN", "AMIR", "ENZO", "ISMAEL", "YANIS", "SOAN", "CAMILLE",
        "SAMUEL", "OWEN", "ANDREA", "SIMON", "ALESSIO", "MAHE", "PABLO", "MATHEO", "OSCAR", "EVAN",
        "NAIM", "MAE", "CHARLY", "NOA", "CHARLIE", "ZAYN", "BASILE", "LIVIO", "MAXENCE", "KAYDEN",
        "ISSA", "ALI", "AYLAN", "CHARLES", "ALEXANDRE", "JOSEPH", "AUGUSTE", "MARIN", "ANAS", "CLEMENT",
        "ACHILLE", "ROMEO", "EZIO", "TIMOTHEE", "BAPTISTE", "LUCIEN", "ABEL", "LOAN", "LENNY"
]

PRENOMS_F = [
        "LOUISE", "AMBRE", "ALBA", "JADE", "EMMA", "ROSE", "ALMA", "ALICE", "ROMY", "ANNA",
        "EVA", "LINA", "MIA", "INAYA", "AGATHE", "LOU", "JULIA", "IRIS", "LENA", "GIULIA",
        "CHARLIE", "ADELE", "VICTOIRE", "OLIVIA", "CHLOE", "LEA", "JULIETTE", "JEANNE", "LUNA", "NINA",
        "NOUR", "LEONIE", "ZOE", "SOFIA", "VICTORIA", "ROMANE", "LOLA", "LYA", "AVA", "ALYA",
        "LUCIE", "ALIX", "CHARLOTTE", "LYANA", "ELENA", "INES", "MILA", "EMY", "MARGAUX", "ALBANE",
        "AYA", "MYA", "MARGOT", "LOUNA", "THEA", "GABRIELLE", "LYNA", "CAMILLE", "SARAH", "ASSIA",
        "CAPUCINE", "YASMINE", "MARIA", "APOLLINE", "ESMEE", "CELESTE", "LIVIA", "MAYA", "ELLA", "CLEMENCE",
        "MANON", "DIANE", "LANA", "ARYA", "LILA", "LILY", "AMELIA", "VALENTINA", "THAIS", "SUZANNE",
        "VALENTINE", "JOY", "CLARA", "ARIA", "MARYAM", "NORA", "MARIE", "CONSTANCE", "ROXANE", "LISE",
        "ALICIA", "ELLIE", "MATHILDE", "HELOISE", "ELYA", "ZELIE", "AICHA", "ALIYAH", "FATIMA", "JUDITH"
]

NOMS = [
    "MARTIN", "BERNARD", "THOMAS", "PETIT", "ROBERT", "RICHARD", "DURAND", "DUBOIS", "MOREAU", "LAURENT",
    "SIMON", "MICHEL", "LEFEBVRE", "LEROY", "ROUX", "DAVID", "BERTRAND", "MOREL", "FOURNIER", "GIRARD",
    "BONNET", "DUPONT", "LAMBERT", "FONTAINE", "ROUSSEAU", "VINCENT", "MULLER", "LEFEVRE", "FAURE", "ANDRE",
    "MERCIER", "BLANC", "GUERIN", "BOYER", "GARNIER", "CHEVALIER", "FRANCOIS", "LEGRAND", "GAUTHIER", "GARCIA",
    "PERRIN", "ROBIN", "CLEMENT", "MORIN", "NICOLAS", "HENRY", "ROUSSEL", "MATHIEU", "GAUTIER", "MASSON",
    "MARCHAND", "DUVAL", "DENIS", "DUMONT", "MARIE", "LEMAIRE", "NOEL", "MEYER", "DUFOUR", "MEUNIER",
    "BRUN", "BLANCHARD", "GIRAUD", "JOLY", "RIVIERE", "LUCAS", "BRUNET", "GAILLARD", "BARBIER", "ARNAUD",
    "MARTINEZ", "GERARD", "ROCHE", "RENARD", "SCHMITT", "ROY", "LEROUX", "COLIN", "VIDAL", "CARON",
    "PICARD", "ROGER", "FABRE", "AUBERT", "LEMOINE", "RENAUD", "DUMAS", "LACROIX", "OLIVIER", "PHILIPPE",
    "BOURGEOIS", "PIERRE", "BENOIT", "REY", "LECLERC", "PAYET", "ROLLAND", "LECLERCQ", "GUILLAUME", "LECOMTE",
    "LOPEZ", "JEAN", "DUPUY", "GUILLOT", "HUBERT", "BERGER", "CARPENTIER", "SANCHEZ", "DUPUIS", "MOULIN",
    "LOUIS", "DESCHAMPS", "HUET", "VASSEUR", "PEREZ", "BOUCHER", "FLEURY", "ROYER", "KLEIN", "JACQUET",
    "ADAM", "PARIS", "POIRIER", "MARTY", "AUBRY", "GUYOT", "CARRE", "CHARLES", "RENAULT", "CHARPENTIER",
    "MENARD", "MAILLARD", "BARON", "BERTIN", "BAILLY", "HERVE", "SCHNEIDER", "FERNANDEZ", "LE GALL", "COLLET",
    "LEGER", "BOUVIER", "JULIEN", "PREVOST", "MILLET", "PERROT", "DANIEL", "LE ROUX", "COUSIN", "GERMAIN",
    "BRETON", "BESSON", "LANGLOIS", "REMY", "LE GOFF", "PELLETIER", "LEVEQUE", "PERRIER", "LEBLANC", "BARRE",
    "LEBRUN", "MARCHAL", "WEBER", "MALLET", "HAMON", "BOULANGER", "JACOB", "MONNIER", "MICHAUD", "RODRIGUEZ",
    "GUICHARD", "GILLET", "ETIENNE", "GRONDIN", "POULAIN", "TESSIER", "CHEVALLIER", "COLLIN", "CHAUVIN", "DA SILVA",
    "BOUCHET", "GAY", "LEMAITRE", "BENARD", "MARECHAL", "HUMBERT", "REYNAUD", "ANTOINE", "HOARAU", "PERRET",
    "BARTHELEMY", "CORDIER", "PICHON", "LEJEUNE", "GILBERT", "LAMY", "DELAUNAY", "PASQUIER", "CARLIER", "LAPORTE",
    "HAMEL", "BERTHIER", "LETELLIER", "PREVOT", "GRAND", "GRANDJEAN", "BENOIST", "LEBLOND", "GOSSELIN", "LELEU",
    "COMTE", "FAVIER", "BELLANGER", "MARTINET", "BILLARD", "RAULT", "GEOFFROY", "FORESTIER", "BLONDEAU", "ROQUES",
    "RICARD", "POMMIER", "BOULET", "DROUET", "POISSON", "MAIRE", "MOUNIER", "GUEGUEN", "COMBES", "HUGUET",
    "MORAND", "LEONARD", "LEDOUX", "PRAT", "DUBREUIL", "FORTIN", "FERRE", "RIGAUD", "BROSSARD", "PICOT",
    "GRANGER", "MERLIN", "LAVAL", "CLAUDE", "MARQUET", "MOUTON", "BRAULT", "JEANNE", "MARC", "LEVASSEUR",
    "LE ROY", "GUILLEMIN", "BOCQUET", "CONSTANT", "PUJOL", "LAVIGNE", "BAUER", "HOFFMANN", "CHATELAIN", "LACOUR",
    "JUNG", "JAMET", "LALLEMAND", "WALTER", "BASSET", "PROVOST", "SALAUN", "TELLIER", "GIBERT", "MARTINS",
    "ROSE", "NAVARRO", "GRANGE", "LEPAGE", "BOUQUET", "KELLER", "TECHER", "JOLLY", "TOURNIER", "GUILLARD",
    "PAPIN", "BATAILLE", "LELONG", "CARTIER", "LEON", "CHAMPION", "DUJARDIN", "DUMOULIN", "LASSERRE", "FLAMENT",
    "HUSSON", "SCHMIDT", "LE BIHAN", "KIEFFER", "MILLOT", "LE GUEN", "FERRY", "BOURDIN", "MANGIN", "GICQUEL",
    "CADET", "SOULIER", "MIGNOT", "BARRET", "BUREAU", "LERAY", "FORT", "BARREAU", "MAS", "LAFONT",
    "BOUCHARD", "JOLIVET", "SAVARY", "FOULON", "GUILLEMOT", "COSTA", "ARMAND", "BLAISE", "BINET", "MONTAGNE",
    "JULLIEN", "BERARD", "VACHER", "SAUNIER", "DUPIN", "THIEBAUT", "SCHWARTZ", "FELIX", "SELLIER", "LAGRANGE",
    "LEFRANCOIS", "ANDRIEUX", "LALANNE", "BERTHET", "PAYEN", "LAVERGNE", "JOUAN", "CORNET", "COMBE", "LANG",
    "POULET", "GRANIER", "ZIMMERMANN", "LEBEAU", "BAYLE", "VIGNERON", "TERRIER", "BON", "LECOCQ", "ESNAULT",
    "BORDES", "SARRAZIN", "LE BORGNE", "JOUVE", "LAURET", "LE FLOCH", "GODEFROY", "PRIEUR", "LEMARCHAND", "VERNET",
    "VIVIER", "AUBIN", "FAUCHER", "DUCROCQ", "DORE", "LAMOTTE", "THIERY", "JACQUEMIN", "ARNOULD", "BASTIEN",
    "THERY", "COUDERC", "DUCHENE", "QUERE", "CHEVRIER", "COCHET", "VILLARD", "CORRE", "PROST", "BOIS",
    "MAGNIER", "MONIER", "GROSJEAN", "TARDY", "GIMENEZ", "CAILLAUD", "GUIGNARD", "LEFRANC", "BEAUMONT", "LE BERRE",
    "TISSIER", "ROUXEL", "BONNARD", "LE GAL", "CREPIN", "LESUEUR", "MARQUES", "ROTH", "WOLFF"
]

def _rand_date(start_year: int, end_year: int) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_random_data():
    is_male = random.choice([True, False])

    return {
        "nom": random.choice(NOMS),
        "prenom": random.choice(PRENOMS_M if is_male else PRENOMS_F),
        "sexe": "M" if is_male else "F",
        "dep": f"{random.randint(1, 95):02d}",
        "canton": random.choice("123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "bureau": f"{random.randint(0, 999):03d}",
        "naissance": _rand_date(1955, 2005).strftime("%y%m%d"),
        "date_delivrance": _rand_date(2017, 2019).strftime("%y%m"),
        "random_code": f"{random.randint(0, 9999):04d}",
    }

# =========================
# MRZ CORE
# =========================

def generate_mrz(data: dict) -> dict:
    prefix = "IDFRA"

    nom = normalize_name(data["nom"])
    prenom = normalize_name(data["prenom"])

    suffix = data["dep"] + data["canton"] + data["bureau"]
    max_nom_len = 36 - len(prefix) - len(suffix)
    nom_cut = nom[:max_nom_len]

    fill1 = "<" * (36 - len(prefix + nom_cut + suffix))
    line1 = f"{prefix}{nom_cut}{fill1}{suffix}"

    bloc7 = data["dep"] + data["canton"] + data["bureau"][0]
    cle1 = icao_check_digit(data["date_delivrance"] + bloc7 + data["random_code"])
    cle2 = icao_check_digit(data["naissance"])

    prenom_padded = (prenom + "<" * 14)[:14]

    line2_partial = (
        data["date_delivrance"]
        + bloc7
        + data["random_code"]
        + cle1
        + prenom_padded
        + data["naissance"]
        + cle2
        + data["sexe"]
    )

    cle3 = icao_check_digit(line1 + line2_partial)
    line2 = line2_partial + cle3

    return {
        "line1": line1,
        "line2": line2,
    }
