from curl_cffi import requests
import json
import logging
import time

logger = logging.getLogger(__name__)

from script.chronopost.headers import SIMULATEUR_HEADERS

CHRONOPOST_DISCOUNT_RATE = 0.5

def get_chronopost_price(data):

    url = "https://www.chronopost.fr/wsmchronoweb-rest/offre/list"
    

    weight = float(data.get("weight", 0))
    length = float(data.get("length", 0)) if data.get("length") else 0
    width = float(data.get("width", 0)) if data.get("width") else 0
    height = float(data.get("height", 0)) if data.get("height") else 0

    headers = SIMULATEUR_HEADERS

    s_iso = data.get("sender_iso", "FR")
    r_iso = data.get("recipient_iso", "FR")
    s_zip = data.get("sender_zip")
    r_zip = data.get("recipient_zip")
    s_city = data.get("sender_city")
    r_city = data.get("recipient_city")

    if not all([s_zip, r_zip, s_city, r_city]):
        return {"status": "error"}
    
    if s_iso == "FR" and (not s_zip.isdigit() or len(s_zip) != 5):
        return {"status": "error"}
    if r_iso == "FR" and (not r_zip.isdigit() or len(r_zip) != 5):
        return {"status": "error"}
    
    if len(s_city) < 2 or len(r_city) < 2:
        return {"status": "error"}

    if weight < 0.5 or weight > 30:
        return {"status": "error"}
    
    if r_iso != "FR":
        if any(v > 150 for v in [length, width, height]):
            return {"status": "error"}
        if (length + 2 * (width + height)) > 300:
            return {"status": "error"}


    payload = {
        "locale": "fr",
        "senderCountryCode": s_iso,
        "senderZipCode": s_zip,
        "senderCity": s_city,
        "recipientCountryCode": r_iso,
        "recipientZipCode": r_zip,
        "recipientCity": r_city,
        "classification": "M",
        "recipientPart": True,
        "parcelList": [
            {
                "height": height,
                "width": width,
                "length": length,
                "weight": weight,
                "policyValue": 0,
                "productDescriptionCode": "",
                "productDescriptionLabel": "",
                "valueDeclared": 0
            }
        ]
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            r = requests.post(
                f"{url}?lang=fr_FR",
                data=json.dumps(payload),
                headers=headers,
                impersonate="chrome120",
                timeout=30
            )
            
            if r.status_code == 200:
                choices = r.json()
                results = []
                
                for service in choices:
                    official_price = float(service.get("unitPriceTTC", 0))
                    our_price = round(official_price * CHRONOPOST_DISCOUNT_RATE, 2)
                    
                    results.append({
                        "label": service.get("label"),
                        "product_code": service.get("productCode"),
                        "official_price": official_price,
                        "price": our_price,
                        "is_relay": service.get("relay", False),
                        "delivery_date": service.get("dateDelivery")
                    })
                    
                return {"status": "success", "offers": results}
            
            logger.warning(f"Chronopost Attempt {attempt + 1} failed (Code: {r.status_code})")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                logger.error(f"Chronopost API Final Error (Code: {r.status_code}): {r.text}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Chronopost Exception on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return {"status": "error"}
