# ========================= payloads.py =========================
from datetime import datetime
from urllib.parse import quote_plus

BASE_PAYLOAD = (
    # === META / CONFIG ===
    "downloadTokenValue=1768849101561"
    "&typeImpression=PDF"
    "&mediaCommunication=APPLET"
    "&iv4Context=47220cd6138831e87b89bc06aa246440"
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

def normalize_city(v):
    return v.strip().upper().replace(" ", "+")

def normalize_address(v):
    return v.strip().replace(" ", "+")

def ask(label, default=None, required=False, validator=None, data=None, key=None):
    # If data dictionary is provided and key exists, try to use it.
    # In web mode, we expect 'data' to be populated.
    val = None
    if data is not None and key is not None:
        val = data.get(key)
    
    # If value is missing or empty, handle default/required
    if not val:
        if default is not None:
            val = default
        elif required:
            # In API mode, missing required field is an error
            raise ValueError(f"Missing required field: {key} ({label})")
        else:
             val = "" # optional field empty
    
    # Validate if validator exists
    if validator and val: # only validate if we have a value
            if not validator(val):
                # For basic logging if needed, or just raise
                raise ValueError(f"Invalid value for {key}: {val}")
    
    # Return the value (or default/empty string)
    return str(val) if val is not None else ""

def phone_validator(v):
    return len(v) >= 8

CHRONO_13_PRODUCT = "1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"
CHRONO_10_PRODUCT = "2_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"

def build_payload(data=None):
    payload = dict(p.split("=", 1) for p in BASE_PAYLOAD.split("&"))

    # Determine product and valeurproduct
    # Default to 13 if not specified
    valeur_product = "13"
    if data and "valeurproduct" in data:
        valeur_product = str(data["valeurproduct"])
    
    # Select product string
    if valeur_product == "10":
        payload["product"] = CHRONO_10_PRODUCT
    else:
        # Default to 13
        payload["product"] = CHRONO_13_PRODUCT
        valeur_product = "13" # Enforce strict value if unknown was passed

    # Add parameters to payload
    payload["valeurproduct"] = valeur_product


    # Helper to clean up the ask calls
    def get_val(key, label, current_val=None, default=None, required=False, validator=None):
        effective_default = default if default is not None else current_val
        return ask(label, effective_default, required, validator, data=data, key=key)

    # ============================================================
    # === EXPÉDITEUR (SENDER) ===
    # ============================================================

    payload["senderType"] = get_val(
        "senderType", "type expediteur",
        payload.get("senderType"),
        required=True,
        validator=lambda v: v in ("0", "1")
    )

    payload["hiddenSenderType"] = payload["senderType"]

    payload["senderCompanyName"] = get_val(
        "senderCompanyName", "nom de societe expediteur",
        payload.get("senderCompanyName"),
        default="-"
    )

    payload["senderLastname"] = get_val("senderLastname", "nom expediteur", payload.get("senderLastname"), default="-")
    payload["senderFirstname"] = get_val("senderFirstname", "prenom expediteur", payload.get("senderFirstname"), default="-")
    payload["senderHandphone"] = get_val(
        "senderHandphone", "telephone expediteur",
        payload.get("senderHandphone"),
        default="0602843841",
        validator=phone_validator
    )
    payload["senderEmail"] = get_val(
        "senderEmail", "mail expediteur",
        payload.get("senderEmail"),
        default="grecoh@outlook.fr",
        validator=lambda v: "@" in v
    )
    payload["senderCP"] = get_val(
        "senderCP", "code postal expediteur",
        payload.get("senderCP"),
        default="75013",
        validator=lambda v: v.isdigit()
    )

    sender_city = normalize_city(get_val("senderCity", "ville expediteur", payload.get("senderCity"), default="PARIS"))
    payload["senderCity"] = sender_city
    payload["hiddenSenderCity"] = sender_city

    payload["senderAddress"] = normalize_address(
        get_val("senderAddress", "adresse expediteur", payload.get("senderAddress"), default="14 rue henri pape")
    )

    payload["senderAddress2"] = normalize_address(
        get_val(
            "senderAddress2", "suite adresse expediteur",
            payload.get("senderAddress2"),
            default="",
            validator=lambda v: len(v) <= 20
        )
    )

    payload["senderRef"] = get_val(
        "senderRef", "reference expediteur",
        payload.get("senderRef"),
        default="",
        validator=lambda v: len(v) <= 20
    )

    # ============================================================
    # === DESTINATAIRE (RECEIVER) ===
    # ============================================================

    payload["receiverType"] = get_val(
        "receiverType", "type destinataire",
        payload.get("receiverType"),
        required=True,
        validator=lambda v: v in ("0", "1")
    )

    payload["hiddenReceiverType"] = payload["receiverType"]

    payload["receiverCompanyName"] = get_val(
        "receiverCompanyName", "nom de societe destinataire",
        payload.get("receiverCompanyName")
    )

    payload["receiverLastname"] = get_val("receiverLastname", "nom destinataire", payload.get("receiverLastname"))
    payload["receiverFirstname"] = get_val("receiverFirstname", "prenom destinataire", payload.get("receiverFirstname"))
    payload["receiverHandphone"] = get_val(
        "receiverHandphone", "telephone destinataire",
        payload.get("receiverHandphone"),
        validator=phone_validator
    )
    payload["receiverEmail"] = get_val(
        "receiverEmail", "mail destinataire",
        payload.get("receiverEmail"),
        validator=lambda v: "@" in v
    )
    payload["receiverCP"] = get_val(
        "receiverCP", "code postal destinataire",
        payload.get("receiverCP"),
        validator=lambda v: v.isdigit()
    )

    receiver_city = normalize_city(get_val("receiverCity", "ville destinataire", payload.get("receiverCity")))
    payload["receiverCity"] = receiver_city
    payload["receiverCityText"] = receiver_city
    payload["hiddenReceiverCity"] = receiver_city

    payload["receiverAddress"] = normalize_address(
        get_val("receiverAddress", "adresse destinataire", payload.get("receiverAddress"))
    )

    payload["receiverAddress2"] = normalize_address(
        get_val(
            "receiverAddress2", "suite adresse destinataire",
            payload.get("receiverAddress2"),
            validator=lambda v: len(v) <= 20
        )
    )

    payload["receiverAddress3"] = get_val(
        "receiverAddress3", "code batiment",
        payload.get("receiverAddress3"),
        validator=lambda v: len(v) <= 8
    )

    payload["receiverRef"] = get_val(
        "receiverRef", "reference destinataire",
        payload.get("receiverRef"),
        validator=lambda v: len(v) <= 20
    )

    # ============================================================
    # === COLIS / EXPÉDITION ===
    # ============================================================

    payload["packageWeight"] = get_val(
        "packageWeight", "poid",
        payload.get("packageWeight"),
        validator=lambda v: v.isdigit()
    )

    payload["shippingRef"] = get_val(
        "shippingRef", "nom de envoie",
        payload.get("shippingRef"),
        validator=lambda v: len(v) <= 15
    )

    # Date logic: usage input or default to today
    # Date logic: usage input or default to today
    today = quote_plus(datetime.now().strftime("%d/%m/%Y"))
    user_date = get_val("shippingDate", "Date d'envoi", None)
    
    if user_date:
        payload["shippingDate"] = quote_plus(user_date)
        payload["dlcshippingDate"] = quote_plus(user_date)
    else:
        payload["shippingDate"] = today
        payload["dlcshippingDate"] = today

    # ============================================================
    # === NOTIFICATION / SUIVI ===
    # ============================================================

    payload["shipmentTracking"] = get_val(
        "shipmentTracking", "suivi mail expediteur",
        payload.get("shipmentTracking"),
        required=True,
        validator=lambda v: v in ("on", "off")
    )

    payload["notifyTheReceiver"] = get_val(
        "notifyTheReceiver", "suivi mail destinataire",
        payload.get("notifyTheReceiver"),
        required=True,
        validator=lambda v: v in ("on", "off")
    )

    # ============================================================
    # === NOTIFICATION / TIERS ===
    # ============================================================

    payload["sendToThirdPersonInfo"] = get_val(
        "sendToThirdPersonInfo", "mail de reception Bordereau / Label",
        payload.get("sendToThirdPersonInfo"),
        required=True,
        validator=lambda v: "@" in v
    )

    # ============================================================
    # === RETOUR ===
    # ============================================================

    payload["returnShippingDate"] = today

    return "&".join(f"{k}={payload[k]}" for k in payload)
