# ========================= payloads.py =========================
from datetime import datetime
from urllib.parse import quote_plus

BASE_PAYLOAD = (
    # === META / CONFIG ===
    "downloadTokenValue=1768849101561"
    "&typeImpression=PDF"
    "&mediaCommunication=APPLET"
    "&iv4Context=d8731416d5d60aac657dd0120cc49f59"
    "&codeLang=fr_FR"
    "&printDuplicata=false"
    "&printCustomerCab="
    "&printLandScape=false"
    "&europeReturnRelay=false"
    "&authorizedContractCost=false"
    "&hiddenAccountOption=false"
    "&account=47107_15972103"


    # === EXPÉDITEUR (SENDER) ===
    "&senderSearch="
    "&hiddenSenderType="
    "&senderType="
    "&senderCompanyName="
    "&senderLastname="
    "&senderFirstname="
    "&senderHandphone="
    "&senderEmail="
    "&senderCountry=FR"
    "&senderCP="
    "&senderCity="
    "&senderCityText="
    "&senderAddress="
    "&senderAddress2="
    "&senderRef="
    "&hiddenSenderCity="
    "&hiddenSenderCountry=FR"
    "&saveSenderForNextShipment=off"

    # === DESTINATAIRE (RECEIVER) ===
    "&receiverSearch="
    "&hiddenReceiverType="
    "&receiverType="
    "&receiverCompanyName="
    "&receiverLastname="
    "&receiverFirstname="
    "&receiverHandphone="
    "&receiverEmail="
    "&relaisReceiverLastname="
    "&relaisReceiverFirstname="
    "&relaisReceiverHandphone="
    "&relaisReceiverEmail="
    "&receiverCountry=FR"
    "&receiverCP="
    "&receiverCity="
    "&receiverCityText="
    "&receiverAddress="
    "&receiverAddress2="
    "&receiverAddress3="
    "&receiverRef="
    "&relaisReceiverCP="
    "&relaisReceiverCityList="
    "&relaisReceiverCityText="
    "&relaisReceiverAddress="
    "&codeRelais="
    "&hiddenReceiverCity="
    "&hiddenReceiverCountry=FR"

    # === COLIS / EXPÉDITION ===
    "&NbOfPackages=1"
    "&typeColis=2"
    "&packageWeight="
    "&packageLength="
    "&packageWidth="
    "&packageHeight="
    "&packageValue=1"
    "&packageDescriptionText="
    "&shippingRef="
    "&shippingDate="
    "&dlcshippingDate="
    "&shippingRep="
    "&shippingType=M"
    "&shippingToEurope=true"

    # === CONTENU / RÉGLEMENTATION ===
    "&shippingContent="
    "&shippingContentEn="
    "&shippingContentRestricted="
    "&shippingContentAutoCompleted=false"
    "&shippingContentOK=true"
    "&shippingContentRequired=true"
    "&insurancePrice="

    # === NOTIFICATION / SUIVI ===
    "&shipmentTracking="
    "&shipmentTrackingBy=EMAIL"
    "&notifyTheReceiver="
    "&notifyTheReceiverBy=EMAIL"

    # === NOTIFICATION / TIERS ===
    "&sendToThirdPerson=on"
    "&sendToThirdPersonInfo="
    "&ltAutoEnable=TRUE"
    "&textInformThird=Envoyer+automatiquement+par+e-mail+la+lettre+de+transport"
    "&textInformThirdLtAuto=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette+de+transport+%3A"
    "&textInformThirdHelp=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette+de+transport+%3A"
    "&textInformThirdHelpLtAuto=Emballages+disponibles+%C3%A0+la+vente+au+prix+de+2%2C00%E2%82%AC+TTC+en+bureau+de+poste.+Demandez-les+aupr%C3%A8s+du+conseiller+client%C3%A8le."
    "&textSendToThirdPersonInfo=Coordonn%C3%A9es+pour+recevoir+la+lettre+de+transport+par+e-mail+%3A"
    "&textSendToThirdPersonInfoLtAuto=Coordonn%C3%A9es+pour+recevoir+le+num%C3%A9ro+de+r%C3%A9servation+(e-mail+ou+SMS)+%3A"
    "&postOfficeOrPickupPoint=2"

    # === RETOUR ===
    "&returnProduct=1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false"
    "&returnTotalWeight="
    "&returnShippingRef="
    "&returnShippingDate="
)

BASE_PAYLOAD_MONDE = (
    # === META / CONFIG ===
    "downloadTokenValue=1769273592939"
    "&typeImpression=PDF"
    "&mediaCommunication=APPLET"
    "&iv4Context=d8731416d5d60aac657dd0120cc49f59"
    "&codeLang=fr_FR"
    "&printDuplicata=false"
    "&printCustomerCab="
    "&printLandScape=false"
    "&europeReturnRelay=false"
    "&authorizedContractCost=false"
    "&hiddenAccountOption=false"
    "&account=47107_15972103"
    "&product=17_I_0_30_30_150_21_150_0.1_150_72.2_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"

    # === EXPÉDITEUR (SENDER) ===
    "&senderSearch="
    "&hiddenSenderType="
    "&senderType="
    "&senderCompanyName="
    "&senderLastname="
    "&senderFirstname="
    "&senderHandphone="
    "&senderEmail="
    "&senderCountry=FR"
    "&senderCP="
    "&senderCity="
    "&senderCityText="
    "&senderAddress="
    "&senderAddress2="
    "&senderRef="
    "&hiddenSenderCity="
    "&hiddenSenderCountry=FR"

    # === DESTINATAIRE (RECEIVER) ===
    "&receiverSearch="
    "&hiddenReceiverType="
    "&receiverType="
    "&receiverCompanyName="
    "&receiverLastname="
    "&receiverFirstname="
    "&receiverHandphone="
    "&receiverEmail="
    "&relaisReceiverLastname="
    "&relaisReceiverFirstname="
    "&relaisReceiverHandphone="
    "&relaisReceiverEmail="
    "&receiverCountry=FR"
    "&receiverCP="
    "&receiverCity="
    "&receiverCityText="
    "&receiverAddress="
    "&receiverAddress2="
    "&receiverAddress3="
    "&receiverRef="
    "&relaisReceiverCP="
    "&relaisReceiverCityList="
    "&relaisReceiverCityText="
    "&relaisReceiverAddress="
    "&codeRelais="
    "&hiddenReceiverCity="
    "&hiddenReceiverCountry=FR"

    # === COLIS / EXPÉDITION ===
    "&NbOfPackages=1"
    "&typeColis=2"
    "&packageWeight="
    "&packageLength="
    "&packageWidth="
    "&packageHeight="
    "&codePackaging=2"
    "&shippingRef="
    "&shippingDate="
    "&dlcshippingDate="
    "&shippingRep="
    "&shippingType=M"
    "&shippingToEurope=false"

    # === CONTENU / DOUANE ===
    "&shippingContent="
    "&shippingContentEn="
    "&shippingContentRestricted="
    "&shippingContentAutoCompleted=false"
    "&shippingContentOK=true"
    "&shippingContentRequired=true"
    "&packageDescription=M_01"
    "&packageDescriptionText="
    "&packageValue="
    "&packageIncoterm=DAP"
    "&generateProForma=on"
    "&insurancePrice="

    # === NOTIFICATION / LT AUTO ===
    "&sendToThirdPerson=on"
    "&ltAutoEnable=TRUE"
    "&sendToThirdPersonInfo="
    "&textInformThird=Envoyer+automatiquement+par+e-mail+la+lettre+de+transport"
    "&textInformThirdLtAuto=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette"
    "&textInformThirdHelp=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette"
    "&textInformThirdHelpLtAuto=Emballages+disponibles+%C3%A0+la+vente+au+prix+de+2%2C00%E2%82%AC+TTC+en+bureau+de+poste.+Demandez-les+aupr%C3%A8s+du+conseiller+client%C3%A8le."
    "&textSendToThirdPersonInfo=Coordonn%C3%A9es+pour+recevoir+la+lettre+de+transport+par+e-mail"
    "&textSendToThirdPersonInfoLtAuto=Coordonn%C3%A9es+pour+recevoir+le+num%C3%A9ro+de+r%C3%A9servation+(e-mail+ou+SMS)"
    "&postOfficeOrPickupPoint=2"

    # === RETOUR ===
    "&returnProduct=1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false"
    "&returnTotalWeight="
    "&returnShippingRef="
    "&returnShippingDate="
)


# Mapping Pays Nom -> ISO (Extrait de chrono-express.html)
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
    return v.strip().upper().replace(" ", "+")

def normalize_address(v):
    return v.strip().replace(" ", "+")

def norm_country(val):
    if not val:
        return ""
    val = val.strip().upper()
    # Si déjà code ISO (<= 3 chars, ex: FR, USA)
    if len(val) <= 3:
        return val
    # Sinon lookup
    return COUNTRY_MAP.get(val, val) # Retourne val si pas trouvé (fallback)

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

CHRONO_13_PRODUCT = "1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"
CHRONO_10_PRODUCT = "2_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"
CHRONO_RELAIS_PRODUCT = "86_N_0_20_22.9_100_16_100_0.1_100_58.1_250_true_false_false_false_false_false_true_false_false_false_false_false_false_true"
CHRONO_MONDE_PRODUCT = "17_I_0_30_30_150_21_150_0.1_150_72.2_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"

def build_payload(data=None):
    # === SELECTION PRODUIT ===
    valeur_product = "13"
    if data and "valeurproduct" in data:
        valeur_product = str(data["valeurproduct"])

    # Si Chrono Express / Monde -> Fonction dédiée
    if valeur_product == "monde":
        return build_payload_monde(data)

    # === LOGIQUE STANDARD (Chrono 13, 10, Relais) ===
    payload = dict(p.split("=", 1) for p in BASE_PAYLOAD.split("&"))
    
    if valeur_product == "10":
        payload["product"] = CHRONO_10_PRODUCT
    elif valeur_product == "relais":
        payload["product"] = CHRONO_RELAIS_PRODUCT
    else:
        payload["product"] = CHRONO_13_PRODUCT
        valeur_product = "13"

    payload["valeurproduct"] = valeur_product

    def get_val(key, label, current_val=None, default=None, required=False, validator=None):
        effective_default = default if default is not None else current_val
        return ask(label, effective_default, required, validator, data=data, key=key)

    # --- SENDER ---
    payload["senderType"] = get_val("senderType", "type expediteur", payload.get("senderType"), required=True, validator=lambda v: v in ("0", "1"))
    payload["hiddenSenderType"] = payload["senderType"]
    payload["senderCompanyName"] = get_val("senderCompanyName", "nom de societe expediteur", payload.get("senderCompanyName"), default="-")
    payload["senderLastname"] = get_val("senderLastname", "nom expediteur", payload.get("senderLastname"), default="-")
    payload["senderFirstname"] = get_val("senderFirstname", "prenom expediteur", payload.get("senderFirstname"), default="-")
    payload["senderHandphone"] = get_val("senderHandphone", "telephone expediteur", payload.get("senderHandphone"), default="0602843841", validator=phone_validator)
    payload["senderEmail"] = get_val("senderEmail", "mail expediteur", payload.get("senderEmail"), default="grecoh@outlook.fr", validator=lambda v: "@" in v)
    payload["senderCP"] = get_val("senderCP", "code postal expediteur", payload.get("senderCP"), default="75013", validator=lambda v: v.isdigit())
    
    sender_city = normalize_city(get_val("senderCity", "ville expediteur", payload.get("senderCity"), default="PARIS"))
    payload["senderCity"] = sender_city
    payload["hiddenSenderCity"] = sender_city
    
    payload["senderAddress"] = normalize_address(get_val("senderAddress", "adresse expediteur", payload.get("senderAddress"), default="14 rue henri pape"))
    payload["senderAddress2"] = normalize_address(get_val("senderAddress2", "suite adresse expediteur", payload.get("senderAddress2"), default="", validator=lambda v: len(v) <= 38))
    payload["senderRef"] = get_val("senderRef", "reference expediteur", payload.get("senderRef"), default="", validator=lambda v: len(v) <= 38)

    # --- RECEIVER ---
    payload["receiverType"] = get_val("receiverType", "type destinataire", payload.get("receiverType"), required=True, validator=lambda v: v in ("0", "1"))
    payload["hiddenReceiverType"] = payload["receiverType"]
    payload["receiverCompanyName"] = get_val("receiverCompanyName", "nom de societe destinataire", payload.get("receiverCompanyName"))
    payload["receiverLastname"] = get_val("receiverLastname", "nom destinataire", payload.get("receiverLastname"))
    payload["receiverFirstname"] = get_val("receiverFirstname", "prenom destinataire", payload.get("receiverFirstname"))
    payload["receiverHandphone"] = get_val("receiverHandphone", "telephone destinataire", payload.get("receiverHandphone"), validator=phone_validator)
    payload["receiverEmail"] = get_val("receiverEmail", "mail destinataire", payload.get("receiverEmail"), validator=lambda v: "@" in v)
    payload["receiverCP"] = get_val("receiverCP", "code postal destinataire", payload.get("receiverCP"), validator=lambda v: v.isdigit())
    
    receiver_city = normalize_city(get_val("receiverCity", "ville destinataire", payload.get("receiverCity")))
    payload["receiverCity"] = receiver_city
    payload["receiverCityText"] = receiver_city
    payload["hiddenReceiverCity"] = receiver_city
    
    payload["receiverAddress"] = normalize_address(get_val("receiverAddress", "adresse destinataire", payload.get("receiverAddress")))
    payload["receiverAddress2"] = normalize_address(get_val("receiverAddress2", "suite adresse destinataire", payload.get("receiverAddress2")))
    payload["receiverAddress3"] = get_val("receiverAddress3", "code batiment", payload.get("receiverAddress3"))
    payload["receiverRef"] = get_val("receiverRef", "reference destinataire", payload.get("receiverRef"))

    # --- RELAIS ---
    if valeur_product == "relais":
        payload["relaisReceiverLastname"] = payload["receiverLastname"]
        payload["relaisReceiverFirstname"] = payload["receiverFirstname"]
        payload["relaisReceiverHandphone"] = payload["receiverHandphone"]
        payload["relaisReceiverEmail"] = payload["receiverEmail"]
        payload["relaisReceiverCP"] = payload["receiverCP"]
        payload["relaisReceiverCityList"] = payload["receiverCity"]
        payload["relaisReceiverCityText"] = payload["receiverCity"]
        payload["relaisReceiverAddress"] = payload["receiverAddress"]
        code_relais = get_val("codeRelais", "Code Relais", payload.get("codeRelais"))
        payload["codeRelais"] = code_relais
        payload["idAltadis"] = code_relais

    # --- COLIS ---
    payload["packageWeight"] = get_val("packageWeight", "poid", payload.get("packageWeight"), validator=lambda v: v.replace('.','',1).isdigit())
    payload["shippingRef"] = get_val("shippingRef", "nom de envoie", payload.get("shippingRef"))

    today = quote_plus(datetime.now().strftime("%d/%m/%Y"))
    user_date = get_val("shippingDate", "Date d'envoi", None)
    if user_date:
        payload["shippingDate"] = quote_plus(user_date)
        payload["dlcshippingDate"] = quote_plus(user_date)
    else:
        payload["shippingDate"] = today
        payload["dlcshippingDate"] = today

    # --- NOTIF ---
    payload["shipmentTracking"] = get_val("shipmentTracking", "suivi mail expediteur", payload.get("shipmentTracking"), required=True, validator=lambda v: v in ("on", "off"))
    payload["notifyTheReceiver"] = get_val("notifyTheReceiver", "suivi mail destinataire", payload.get("notifyTheReceiver"), required=True, validator=lambda v: v in ("on", "off"))
    payload["sendToThirdPersonInfo"] = get_val("sendToThirdPersonInfo", "mail de reception Bordereau / Label", payload.get("sendToThirdPersonInfo"), required=True, validator=lambda v: "@" in v)

    return "&".join(f"{k}={payload[k]}" for k in payload)


def build_payload_monde(data=None):
    """
    Fonction dédiée pour le payload Chrono Express (Monde).
    Utilise BASE_PAYLOAD_MONDE et applique les règles spécifiques.
    """
    payload = dict(p.split("=", 1) for p in BASE_PAYLOAD_MONDE.split("&"))
    
    def get_val(key, label, current_val=None, default=None, required=False, validator=None):
        effective_default = default if default is not None else current_val
        return ask(label, effective_default, required, validator, data=data, key=key)

    # === EXPÉDITEUR (SENDER) ===
    payload["senderType"] = get_val("senderType", "type expediteur", payload.get("senderType"), required=True, validator=lambda v: v in ("0", "1", "pro"))
    payload["hiddenSenderType"] = payload["senderType"]
    
    payload["senderCompanyName"] = get_val("senderCompanyName", "societe Expéditeur", payload.get("senderCompanyName"), default="-")
    payload["senderLastname"] = get_val("senderLastname", "nom Expéditeur", payload.get("senderLastname"), default="-")
    payload["senderFirstname"] = get_val("senderFirstname", "prenom Expéditeur", payload.get("senderFirstname"), default="-")
    payload["senderHandphone"] = get_val("senderHandphone", "telephone Expéditeur", payload.get("senderHandphone"), default="0602843841", validator=phone_validator)
    payload["senderEmail"] = get_val("senderEmail", "email Expéditeur", payload.get("senderEmail"), default="grecoh@outlook.fr", validator=lambda v: "@" in v)
    
    payload["senderCountry"] = "FR" # Force FR as per base payload
    payload["senderCP"] = get_val("senderCP", "code postal Expéditeur", payload.get("senderCP"), default="75013")
    
    sender_city = normalize_city(get_val("senderCity", "ville Expéditeur", payload.get("senderCity"), default="PARIS"))
    payload["senderCity"] = sender_city
    payload["hiddenSenderCity"] = sender_city
    payload["hiddenSenderCountry"] = "FR"

    payload["senderAddress"] = normalize_address(get_val("senderAddress", "adresse Expéditeur", payload.get("senderAddress"), default="14 rue henri pape"))
    payload["senderAddress2"] = normalize_address(get_val("senderAddress2", "Complément adresse Expéditeur", payload.get("senderAddress2"), default=""))
    payload["senderRef"] = get_val("senderRef", "Référence Expéditeur", payload.get("senderRef"), default="")

    # === DESTINATAIRE (RECEIVER) ===
    payload["receiverType"] = get_val("receiverType", "type destinataire", payload.get("receiverType"), required=True)
    payload["hiddenReceiverType"] = payload["receiverType"]
    
    payload["receiverCompanyName"] = get_val("receiverCompanyName", "societe destinataire", payload.get("receiverCompanyName"))
    payload["receiverLastname"] = get_val("receiverLastname", "nom destinataire", payload.get("receiverLastname"))
    payload["receiverFirstname"] = get_val("receiverFirstname", "prenom destinataire", payload.get("receiverFirstname"))
    payload["receiverHandphone"] = get_val("receiverHandphone", "telephone destinataire", payload.get("receiverHandphone"), validator=phone_validator)
    payload["receiverEmail"] = get_val("receiverEmail", "email destinataire", payload.get("receiverEmail"), validator=lambda v: "@" in v)
    
    payload["receiverCountry"] = norm_country(get_val("receiverCountry", "pays destinataire", payload.get("receiverCountry")))
    payload["hiddenReceiverCountry"] = payload["receiverCountry"]
    
    payload["receiverCP"] = get_val("receiverCP", "code postal destinataire", payload.get("receiverCP"))
    
    receiver_city = normalize_city(get_val("receiverCity", "ville destinataire", payload.get("receiverCity"))) # Using normalize for consistency
    payload["receiverCityText"] = receiver_city # Note: mapped to receiverCityText as requested for monde input logic? standard is receiverCity. Base says receiverCityText=. Let's populate both.
    payload["receiverCity"] = receiver_city 
    payload["hiddenReceiverCity"] = receiver_city 

    payload["receiverAddress"] = normalize_address(get_val("receiverAddress", "adresse destinataire", payload.get("receiverAddress")))
    payload["receiverAddress2"] = normalize_address(get_val("receiverAddress2", "Complément adresse Destinataire", payload.get("receiverAddress2")))
    payload["receiverAddress3"] = get_val("receiverAddress3", "Code Bâtiment Destinataire", payload.get("receiverAddress3"))
    payload["receiverRef"] = get_val("receiverRef", "Référence Destinataire", payload.get("receiverRef"))

    # === COLIS / EXPÉDITION ===
    payload["packageWeight"] = get_val("packageWeight", "poid", payload.get("packageWeight"))
    payload["packageLength"] = get_val("packageLength", "longueur", payload.get("packageLength"))
    payload["packageWidth"] = get_val("packageWidth", "largeur", payload.get("packageWidth"))
    payload["packageHeight"] = get_val("packageHeight", "hauteur", payload.get("packageHeight"))
    
    payload["shippingRef"] = get_val("shippingRef", "Nom envoi", payload.get("shippingRef"))
    
    today = quote_plus(datetime.now().strftime("%d/%m/%Y"))
    user_date = get_val("shippingDate", "date", None)
    if user_date:
        payload["shippingDate"] = quote_plus(user_date)
        payload["dlcshippingDate"] = quote_plus(user_date)
        payload["returnShippingDate"] = quote_plus(user_date)
    else:
        payload["shippingDate"] = today
        payload["dlcshippingDate"] = today
        payload["returnShippingDate"] = today

    # === CONTENU / DOUANE ===
    payload["shippingContent"] = get_val("shippingContent", "contenu envoie", payload.get("shippingContent"))
    payload["shippingContentEn"] = payload["shippingContent"]
    payload["packageValue"] = get_val("packageValue", "valeur contenu", payload.get("packageValue"), default="1")

    # === NOTIFICATION ===
    # Using defaults from Base Payload, but if user inputs expected allow overrides? 
    # Request didn't specify inputs for tracking, but usually we keep them enabled.
    # Base payload has them on? Not explicitly. Let's check base payload.
    # Base Payload Monde -> shipmentTracking= (empty). So we SHOULD populate them.
    payload["shipmentTracking"] = get_val("shipmentTracking", "suivi mail expediteur", payload.get("shipmentTracking"), default="on", validator=lambda v: v in ("on", "off"))
    payload["notifyTheReceiver"] = get_val("notifyTheReceiver", "suivi mail destinataire", payload.get("notifyTheReceiver"), default="on", validator=lambda v: v in ("on", "off"))
    
    payload["sendToThirdPersonInfo"] = get_val("sendToThirdPersonInfo", "email reception bordereau", payload.get("sendToThirdPersonInfo"), required=True, validator=lambda v: "@" in v)

    return "&".join(f"{k}={payload[k]}" for k in payload)
