from datetime import datetime
from urllib.parse import quote_plus

iv4 = "d8731416d5d60aac657dd0120cc49f59"

def get_current_cart_date():
    """Retourne la date actuelle au format DD/MM/YYYY/HH:MM"""
    now = datetime.now()
    return now.strftime("%d/%m/%Y/%H:%M")

# Mapping Pays Nom -> ISO
COUNTRY_MAP = {
    "AFGHANISTAN": "AF", "AFRIQUE DU SUD": "ZA", "ALBANIE": "AL", "ALGÉRIE": "DZ", "ALLEMAGNE": "DE",
    "ANDORRE": "AD", "ANGOLA": "AO", "ANGUILLA": "AI", "ANTARCTIQUE": "AQ", "ANTIGUA-ET-BARBUDA": "AG",
    "ARABIE SAOUDITE": "SA", "ARGENTINE": "AR", "ARMÉNIE": "AM", "ARUBA": "AW", "AUSTRALIE": "AU",
    "AUTRICHE": "AT", "AZERBAÏDJAN": "AZ", "BAHAMAS": "BS", "BAHREÏN": "BH", "BANGLADESH": "BD",
    "BARBADE": "BB", "BELGIQUE": "BE", "BELIZE": "BZ", "BÉNIN": "BJ", "BERMUDES": "BM", "BHOUTAN": "BT",
    "BIÉLORUSSIE": "BY", "BOLIVIE": "BO", "BOSNIE-HERZÉGOVINE": "BA", "BOTSWANA": "BW", "BRÉSIL": "BR",
    "BRUNÉI DARUSSALAM": "BN", "BULGARIE": "BG", "BURKINA FASO": "BF", "BURUNDI": "BI", "CAMBODGE": "KH",
    "CAMEROUN": "CM", "CANADA": "CA", "CAP-VERT": "CV", "CHILI": "CL", "CHINE": "CN", "CHYPRE": "CY",
    "COLOMBIE": "CO", "COMORES": "KM", "CONGO": "CG", "CONGO (RÉP. DÉM.)": "CD", "CORÉE DU SUD": "KR",
    "CORÉE DU NORD": "KP", "COSTA RICA": "CR", "CÔTE D'IVOIRE": "CI", "CROATIE": "HR", "CUBA": "CU",
    "DANEMARK": "DK", "DJIBOUTI": "DJ", "DOMINIQUE": "DM", "ÉGYPTE": "EG", "ÉMIRATS ARABES UNIS": "AE",
    "ÉQUATEUR": "EC", "ÉRYTHRÉE": "ER", "ESPAGNE": "ES", "ESTONIE": "EE", "ÉTATS-UNIS": "US",
    "ÉTHIOPIE": "ET", "FIDJI": "FJ", "FINLANDE": "FI", "FRANCE": "FR", "GABON": "GA", "GAMBIE": "GM",
    "GÉORGIE": "GE", "GHANA": "GH", "GIBRALTAR": "GI", "GRÈCE": "GR", "GRENADE": "GD", "GROENLAND": "GL",
    "GUADELOUPE": "GP", "GUAM": "GU", "GUATEMALA": "GT", "GUERNESEY": "GG", "GUINÉE": "GN",
    "GUINÉE-BISSAU": "GW", "GUINÉE ÉQUATORIALE": "GQ", "GUYANA": "GY", "GUYANE FRANÇAISE": "GF",
    "HAÏTI": "HT", "HONDURAS": "HN", "HONG KONG": "HK", "HONGRIE": "HU", "ÎLE DE MAN": "IM", "INDE": "IN",
    "INDONÉSIE": "ID", "IRAK": "IQ", "IRAN": "IR", "IRLANDE": "IE", "ISLANDE": "IS", "ISRAËL": "IL",
    "ITALIE": "IT", "JAMAIQUE": "JM", "JAPON": "JP", "JERSEY": "JE", "JORDANIE": "JO", "KAZAKHSTAN": "KZ",
    "KENYA": "KE", "KIRGHIZISTAN": "KG", "KIRIBATI": "KI", "KOWEÏT": "KW", "LAOS": "LA", "LESOTHO": "LS",
    "LETTONIE": "LV", "LIBAN": "LB", "LIBÉRIA": "LR", "LIBYE": "LY", "LIECHTENSTEIN": "LI", "LITUANIE": "LT",
    "LUXEMBOURG": "LU", "MACAO": "MO", "MACÉDOINE DU NORD": "MK", "MADAGASCAR": "MG", "MALAISIE": "MY",
    "MALAWI": "MW", "MALDIVES": "MV", "MALI": "ML", "MALTE": "MT", "MAROC": "MA", "MARTINIQUE": "MQ",
    "MAURICE": "MU", "MAURITANIE": "MR", "MAYOTTE": "YT", "MEXIQUE": "MX", "MICRONÉSIE": "FM",
    "MOLDAVIE": "MD", "MONACO": "MC", "MONGOLIE": "MN", "MONTÉNÉGRO": "ME", "MONTSERRAT": "MS",
    "MOZAMBIQUE": "MZ", "MYANMAR (BIRMANIE)": "MM", "NAMIBIE": "NA", "NAURU": "NR", "NÉPAL": "NP",
    "NICARAGUA": "NI", "NIGER": "NE", "NIGÉRIA": "NG", "NIUE": "NU", "NORVÈGE": "NO",
    "NOUVELLE-CALÉDONIE": "NC", "NOUVELLE-ZÉLANDE": "NZ", "OMAN": "OM", "OUGANDA": "UG",
    "OUZBÉKISTAN": "UZ", "PAKISTAN": "PK", "PALAOS": "PW", "PALESTINE": "PS", "PANAMA": "PA",
    "PAPOUASIE-NOUVELLE-GUINÉE": "PG", "PARAGUAY": "PY", "PAYS-BAS": "NL", "PÉROU": "PE",
    "PHILIPPINES": "PH", "POLOGNE": "PL", "POLYNÉSIE FRANÇAISE": "PF", "PORTO RICO": "PR",
    "PORTUGAL": "PT", "QATAR": "QA", "RÉUNION": "RE", "ROUMANIE": "RO", "ROYAUME-UNI": "GB",
    "RUSSIE": "RU", "RWANDA": "RW", "SAHARA OCCIDENTAL": "EH", "SAINT-BARTHÉLEMY": "BL",
    "SAINT-KITTS-ET-NEVIS": "KN", "SAINT-MARIN": "SM", "SAINT-MARTIN": "MF",
    "SAINT-PIERRE-ET-MIQUELON": "PM", "SAINT-VINCENT-ET-LES-GRENADINES": "VC", "SAINTE-LUCIE": "LC",
    "SALOMON": "SB", "SAMOA": "WS", "SAMOA AMÉRICAINES": "AS", "SAO TOMÉ-ET-PRINCIPE": "ST",
    "SÉNÉGAL": "SN", "SERBIE": "RS", "SEYCHELLES": "SC", "SIERRA LEONE": "SL", "SINGAPOUR": "SG",
    "SLOVAQUIE": "SK", "SLOVÉNIE": "SI", "SOMALIE": "SO", "SOUDAN": "SD", "SRI LANKA": "LK",
    "SUÈDE": "SE", "SUISSE": "CH", "SURINAME": "SR", "SYRIE": "SY", "TADJIKISTAN": "TJ", "TAÏWAN": "TW",
    "TANZANIE": "TZ", "TCHAD": "TD", "TCHÉQUIE": "CZ", "TERRES AUSTRALES FRANÇAISES": "TF",
    "THAÏLANDE": "TH", "TIMOR ORIENTAL": "TL", "TOGO": "TG", "TOKELAU": "TK", "TONGA": "TO",
    "TRINITÉ-ET-TOBAGO": "TT", "TUNISIE": "TN", "TURKMÉNISTAN": "TM", "TURQUIE": "TR", "TUVALU": "TV",
    "UKRAINE": "UA", "URUGUAY": "UY", "VANUATU": "VU", "VENEZUELA": "VE", "VIETNAM": "VN",
    "WALLIS-ET-FUTUNA": "WF", "YÉMEN": "YE", "ZAMBIE": "ZM", "ZIMBABWE": "ZW"
}

def normalize_city(v):
    if not v:
        return ""
    return v.strip().upper().replace(" ", "+")

def normalize_address(v):
    if not v:
        return ""
    return v.strip().replace(" ", "+")

def norm_country(val):
    if not val:
        return ""
    val = val.strip().upper()
    # Si déjà code ISO (<= 3 chars, ex: FR, USA)
    if len(val) <= 3:
        return val
    # Sinon lookup
    return COUNTRY_MAP.get(val, val)

def ask(label, default=None, required=False, validator=None, data=None, key=None):
    val = None
    if data is not None and key is not None:
        val = data.get(key)
    
    if not val:
        if default is not None:
            val = default
        elif required:
            # In API mode, missing required field is an error
            raise ValueError(f"Missing required field: {key} ({label})")
        else:
             val = "" # optional field empty
    
    # Validate if validator exists
    if validator and val: 
            if not validator(val):
                raise ValueError(f"Invalid value for {key}: {val}")
    
    return str(val) if val is not None else ""

def phone_validator(v):
    return len(v) >= 8
