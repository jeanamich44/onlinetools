# ========================= payloads.py =========================
from datetime import datetime
from urllib.parse import quote_plus
from colorama import Fore, Style, init

init(autoreset=True)

BASE_PAYLOAD = (
    "downloadTokenValue=1768677443294"
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
    "&product=1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false_true"
    "&senderSearch="
    "&hiddenSenderType=1"
    "&senderType=1"
    "&senderCompanyName="
    "&senderLastname=-"
    "&senderFirstname=-"
    "&senderHandphone=0602843841"
    "&senderEmail=grecoh@outlook.fr"
    "&senderCountry=FR"
    "&senderCP=75013"
    "&senderCity=PARIS"
    "&senderCityText="
    "&senderAddress=3+rue+Henri+Pape"
    "&senderAddress2="
    "&senderRef="
    "&hiddenSenderCity=PARIS"
    "&hiddenSenderCountry=FR"
    "&saveSenderForNextShipment=on"
    "&receiverSearch="
    "&hiddenReceiverType=1"
    "&receiverType=1"
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
    "&NbOfPackages=1"
    "&typeColis=2"
    "&packageWeight=3"
    "&shippingRef="
    "&shippingDate=17%2F01%2F2026"
    "&dlcshippingDate=17%2F01%2F2026"
    "&shippingRep="
    "&packageLength="
    "&packageWidth="
    "&packageHeight="
    "&shippingContentEn="
    "&shippingContentRestricted="
    "&shippingContentAutoCompleted=false"
    "&shippingContentOK=true"
    "&shippingContentRequired=true"
    "&shippingType=M"
    "&shippingToEurope="
    "&shippingContent="
    "&packageDescriptionText="
    "&packageValue=1"
    "&insurancePrice="
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
    "&returnProduct=1_N_0_30_26_150_16_150_0.1_150_58.1_300_true_true_false_false_false_false_false_false_false_false_false_false_false"
    "&returnTotalWeight="
    "&returnShippingRef="
    "&returnShippingDate=17%2F01%2F2026"
)

def normalize_city(v):
    return v.strip().upper().replace(" ", "+")

def normalize_address(v):
    return v.strip().replace(" ", "+")

def ask(label, default=None, required=False, validator=None):
    while True:
        prompt = f"{Fore.CYAN}{label}{Style.RESET_ALL}"
        if default:
            prompt += f" {Fore.YELLOW}[{default}]{Style.RESET_ALL}"
        prompt += " : "
        val = input(prompt).strip()
        if not val:
            if required and not default:
                print(Fore.RED + "Valeur obligatoire")
                continue
            val = default
        if validator and not validator(val):
            print(Fore.RED + "Valeur invalide")
            continue
        return val

def phone_validator(v):
    return len(v) >= 8

def build_payload():
    payload = dict(p.split("=", 1) for p in BASE_PAYLOAD.split("&"))

    payload["senderLastname"] = ask("senderLastname", "-")
    payload["senderFirstname"] = ask("senderFirstname", "-")
    payload["senderHandphone"] = ask("senderHandphone", "0602843841", validator=phone_validator)
    payload["senderEmail"] = ask("senderEmail", "grecoh@outlook.fr", validator=lambda v: "@" in v)
    payload["senderCP"] = ask("senderCP", "75013", validator=lambda v: v.isdigit())

    sender_city = normalize_city(ask("senderCity", "PARIS"))
    payload["senderCity"] = sender_city
    payload["hiddenSenderCity"] = sender_city
    payload["senderAddress"] = normalize_address(ask("senderAddress", "3 rue Henri Pape"))

    payload["receiverLastname"] = ask("receiverLastname", "jean", required=True)
    payload["receiverFirstname"] = ask("receiverFirstname", "jean", required=True)
    payload["receiverHandphone"] = ask("receiverHandphone", "0602843841", required=True, validator=phone_validator)
    payload["receiverEmail"] = ask("receiverEmail", "jean@gmail.com", required=True, validator=lambda v: "@" in v)
    payload["receiverCP"] = ask("receiverCP", "75009", required=True, validator=lambda v: v.isdigit())

    receiver_city = normalize_city(ask("receiverCity","PARIS", required=True))
    payload["receiverCity"] = receiver_city
    payload["receiverCityText"] = receiver_city
    payload["hiddenReceiverCity"] = receiver_city
    payload["receiverAddress"] = normalize_address(ask("receiverAddress", "14 rue de provence", required=True))

    payload["packageWeight"] = ask("packageWeight", "3", validator=lambda v: v.isdigit())

    today = quote_plus(datetime.now().strftime("%d/%m/%Y"))
    payload["shippingDate"] = today
    payload["dlcshippingDate"] = today
    payload["returnShippingDate"] = today

    payload["sendToThirdPersonInfo"] = ask("sendToThirdPersonInfo","amich5845@gmail.com", required=True, validator=lambda v: "@" in v)

    return "&".join(f"{k}={payload[k]}" for k in payload)