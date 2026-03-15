import requests
import json
import logging
from .p_utils import USER_AGENT

logger = logging.getLogger(__name__)

URL = "https://www.laposte.fr/colis/occ/ecommerce/occ/v2/lpelPart/e-service/colis/price"
DOM = ["GP", "MQ", "RE", "GF", "YT", "PM", "WF", "TF", "NC", "PF", "BL", "MF"]
FR = ["FR", "MC", "AD"]

def get_zone(iso):
    if iso in FR: return "FRANCE"
    if iso in DOM: return "DOM"
    try:
        r = requests.get(f"https://restcountries.com/v3.1/alpha/{iso}?fields=region", timeout=5)
        if r.status_code == 200:
            if r.json().get("region") == "Europe": return "EUROPE"
    except:
        pass
    return "INTERNATIONAL"

def get_colissimo_price(data, config=None):
    try:
        sender = data.get("sender_iso", "FR").upper()
        dest = data.get("recipient_iso", "FR").upper()
        weight = int(float(data.get("weight", 0.5)) * 1000)
        
        zone_dest = get_zone(dest)
        
        # Choix utilisateur pour la France, sinon null (automatique avec signature international)
        user_mode = data.get("shipping_mode", "BAL")
        if zone_dest == "FRANCE":
            delivery_mode = "L_BAL" if user_mode == "BAL" else "L_DOM"
        else:
            delivery_mode = None

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.laposte.fr",
            "priority": "u=1, i",
            "referer": "https://www.laposte.fr/colissimo-en-ligne",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        }

        package_format = data.get("package_format", "STND")
        fmt = "F_VOL" if package_format == "VOL" else "F_STD"

        # ORDRE EXACT DU PAYLOAD FONCTIONNEL
        payload = {
            "depositMode": "D_BP",
            "departureAddress": None,
            "pickingDate": None,
            "deliveryMode": delivery_mode,
            "insurance": None,
            "insuredValue": None,
            "insuredMaxValue": None,
            "pickUpReturnedPackage": None,
            "eco": None,
            "destinationAddress": None,
            "cn23": None,
            "departureCountry": sender,
            "arrivalCountry": dest,
            "weight": weight,
            "format": fmt,
            "arrivalAddress": None,
            "id": None,
            "bundleUniqueId": None
        }

        response = requests.post(URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            price_obj = result.get("totalPrice") or result.get("postagePrice")
            if price_obj:
                print(f"DEBUG: Prix trouvé pour {dest}: {price_obj.get('value')}")
                return {
                    "status": "success",
                    "price": float(price_obj.get("value", 0)),
                    "label": "Colissimo Standard",
                    "zone": zone_dest
                }
        
        logger.error(f"Erreur Tarification ({response.status_code}): {response.text}")
        return {"status": "error", "message": "Tarif non disponible"}
        
        return {"status": "error", "message": "Tarif non disponible"}

    except Exception as e:
        logger.error(f"Erreur Colissimo: {str(e)}")
        return {"status": "error", "message": str(e)}
