from datetime import datetime
from urllib.parse import quote_plus
from .p_utils import iv4, norm_country, normalize_city, normalize_address, ask, phone_validator, COUNTRY_MAP

# === CHRONO EXPRESS (MONDE) ===
BASE_PAYLOAD_MONDE = (
    # === META / CONFIG ===
    "downloadTokenValue=1769273592939"
    "&typeImpression=PDF"
    "&mediaCommunication=APPLET"
    f"&iv4Context={iv4}"
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

def build_payload_monde(data=None):
    """
    Fonction dédiée pour le payload Chrono Express (Monde).
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
    
    payload["senderCountry"] = "FR" 
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
    
    receiver_city = normalize_city(get_val("receiverCity", "ville destinataire", payload.get("receiverCity"))) 
    payload["receiverCityText"] = receiver_city
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
    payload["shipmentTracking"] = get_val("shipmentTracking", "suivi mail expediteur", payload.get("shipmentTracking"), default="on", validator=lambda v: v in ("on", "off"))
    payload["notifyTheReceiver"] = get_val("notifyTheReceiver", "suivi mail destinataire", payload.get("notifyTheReceiver"), default="on", validator=lambda v: v in ("on", "off"))
    
    payload["sendToThirdPersonInfo"] = get_val("sendToThirdPersonInfo", "email reception bordereau", payload.get("sendToThirdPersonInfo"), required=True, validator=lambda v: "@" in v)

    return "&".join(f"{k}={payload[k]}" for k in payload)

# === CHRONO RELAIS EUROPE ===
BASE_PAYLOAD_RELAIS_EUROPE = (
    # === META / CONFIG ===
    "downloadTokenValue=1769628759649"
    "&typeImpression=PDF"
    "&mediaCommunication=APPLET"
    f"&iv4Context={iv4}"
    "&codeLang=fr_FR"
    "&printDuplicata=false"
    "&printCustomerCab="
    "&printLandScape=false"
    "&europeReturnRelay=false"
    "&authorizedContractCost=false"
    "&hiddenAccountOption=false"
    "&account=47107_15972103"
    "&product=49_I_0_20_22.9_100_16_100_0.1_100_58.1_250_true_false_false_false_false_false_true_false_false_false_false_false_false_true"

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
    "&receiverCP="
    "&receiverCity="
    "&receiverCityText="
    "&receiverAddress="
    "&receiverAddress2="
    "&receiverAddress3="
    "&receiverRef="
    "&hiddenReceiverCity="
    "&hiddenReceiverCountry="
    "&relaisReceiverLastname="
    "&relaisReceiverFirstname="
    "&relaisReceiverHandphone="
    "&relaisReceiverEmail="
    "&relaisReceiverCountry="
    "&relaisReceiverCP="
    "&relaisReceiverCityList="
    "&relaisReceiverCityText="
    "&relaisReceiverAddress="
    "&codeRelais="
    "&relais="
    "&idAltadis="

    # === COLIS / EXPÉDITION ===
    "&NbOfPackages=1"
    "&typeColis=2"
    "&packageWeight="
    "&shippingRef="
    "&shippingDate="
    "&dlcshippingDate="
    "&shippingRep="
    "&packageLength="
    "&packageWidth="
    "&packageHeight="
    "&codePackaging=2"

    # === CONTENU / OPTIONS ===
    "&shippingContentEn="
    "&shippingContentRestricted="
    "&shippingContentAutoCompleted=false"
    "&shippingContentOK=true"
    "&shippingContentRequired=true"
    "&shippingType=M"
    "&shippingToEurope=true"
    "&shippingContent="
    "&packageDescriptionText="
    "&packageValue=1"
    "&insurancePrice="

    # === ENVOI TIERS ===
    "&sendToThirdPerson=on"
    "&ltAutoEnable=TRUE"
    "&textInformThird=Envoyer+automatiquement+par+e-mail+la+lettre+de+transport"
    "&textInformThirdLtAuto=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette+de+transport+%3A"
    "&textInformThirdHelp=Recevoir+le+n%C2%B0+de+r%C3%A9servation+pour+d%C3%A9poser+mon+colis+sans+imprimer+d'%C3%A9tiquette+de+transport+%3A"
    "&textInformThirdHelpLtAuto=Emballages+disponibles+%C3%A0+la+vente+au+prix+de+2%2C00e+TTC+en+bureau+de+poste.+Demandez-les+aupr%C3%A8s+du+conseiller+client%C3%A8le."
    "&textSendToThirdPersonInfo=Coordonn%C3%A9es+pour+recevoir+la+lettre+de+transport+par+e-mail+%3A"
    "&textSendToThirdPersonInfoLtAuto=Coordonn%C3%A9es+pour+recevoir+le+num%C3%A9ro+de+r%C3%A9servation+(e-mail+ou+SMS)+%3A"
    "&postOfficeOrPickupPoint=2"
    "&sendToThirdPersonInfo="

    # === RETOUR ===
    "&returnProduct=1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false"
    "&returnTotalWeight="
    "&returnShippingRef="
    "&returnShippingDate="
)

def build_payload_relais_europe(data=None):
    """
    Fonction dédiée pour Chrono Relais Europe.
    """
    payload = dict(p.split("=", 1) for p in BASE_PAYLOAD_RELAIS_EUROPE.split("&"))
    
    def get_val(key, label, current_val=None, default=None, required=False, validator=None):
        effective_default = default if default is not None else current_val
        return ask(label, effective_default, required, validator, data=data, key=key)

    # --- SENDER ---
    payload["senderType"] = get_val("senderType", "type expediteur", payload.get("senderType"), required=True, validator=lambda v: v in ("0", "1", "pro"))
    payload["hiddenSenderType"] = payload["senderType"]
    payload["senderCompanyName"] = get_val("senderCompanyName", "nom de societe expediteur", payload.get("senderCompanyName"), default="-")
    payload["senderLastname"] = get_val("senderLastname", "nom expediteur", payload.get("senderLastname"), default="-")
    payload["senderFirstname"] = get_val("senderFirstname", "prenom expediteur", payload.get("senderFirstname"), default="-")
    payload["senderHandphone"] = get_val("senderHandphone", "telephone expediteur", payload.get("senderHandphone"), default="0602843841", validator=phone_validator)
    payload["senderEmail"] = get_val("senderEmail", "mail expediteur", payload.get("senderEmail"), default="grecoh@outlook.fr", validator=lambda v: "@" in v)
    payload["senderCP"] = get_val("senderCP", "code postal expediteur", payload.get("senderCP"), default="75013", validator=lambda v: v.isdigit())
    
    sender_city = normalize_city(get_val("senderCity", "ville expediteur", payload.get("senderCity"), default="PARIS"))
    payload["senderCity"] = sender_city
    payload["senderCityText"] = sender_city
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

    # --- COUNTRY OVERRIDE FOR EUROPE ---
    dest_country = norm_country(get_val("destinationCountry", "pays destinataire", None))
    # Fallback to FR if not provided (should be provided for this service)
    if not dest_country:
        dest_country = "FR"

    payload["hiddenReceiverCountry"] = dest_country
    payload["relaisReceiverCountry"] = dest_country
    # Note: receiverCountry might need to be set too if the user wants it, 
    # but the provided payload shows hiddenReceiverCountry and relaisReceiverCountry being key.
    # We should probably set receiverCountry too just in case, or leave it empty if the model implies it.
    # The model has "hiddenReceiverCountry =" and "relaisReceiverCountry =". 
    # Let's set both.
    
    # --- RELAIS ---
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
    payload["relais"] = code_relais # Also map to 'relais' as per provided payload key
    payload["idAltadis"] = code_relais

    # --- COLIS ---
    payload["packageWeight"] = get_val("packageWeight", "poid", payload.get("packageWeight"), validator=lambda v: v.replace('.','',1).isdigit())
    payload["packageLength"] = get_val("packageLength", "longueur", payload.get("packageLength"))
    payload["packageWidth"] = get_val("packageWidth", "largeur", payload.get("packageWidth"))
    payload["packageHeight"] = get_val("packageHeight", "hauteur", payload.get("packageHeight"))
    
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
    payload["sendToThirdPersonInfo"] = get_val("sendToThirdPersonInfo", "mail de reception Bordereau / Label", payload.get("sendToThirdPersonInfo"), required=True, validator=lambda v: "@" in v)

    return "&".join(f"{k}={payload[k]}" for k in payload)
