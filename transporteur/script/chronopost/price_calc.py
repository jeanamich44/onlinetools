from curl_cffi import requests
import json

from script.chronopost.headers import SIMULATEUR_HEADERS

# Taux de réduction appliqué aux tarifs officiels (0.5 = -50%)
CHRONOPOST_DISCOUNT_RATE = 0.5

def get_chronopost_price(data):

    url = "https://www.chronopost.fr/wsmchronoweb-rest/offre/list"
    
    # Validation et préparation des dimensions (par défaut à 0)
    weight = float(data.get("weight", 0))
    length = float(data.get("length", 0)) if data.get("length") else 0
    width = float(data.get("width", 0)) if data.get("width") else 0
    height = float(data.get("height", 0)) if data.get("height") else 0

    # Préparation du payload pour l'API Chronopost
    payload = {
        "locale": "fr",
        "senderCountryCode": data.get("sender_iso", "FR"),
        "senderZipCode": data.get("sender_zip"),
        "senderCity": data.get("sender_city"),
        "recipientCountryCode": data.get("recipient_iso", "FR"),
        "recipientZipCode": data.get("recipient_zip"),
        "recipientCity": data.get("recipient_city"),
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

    headers = SIMULATEUR_HEADERS

    if weight < 0.5:
        return {"status": "error", "message": "Le poids minimum est de 0.5kg."}
    
    if weight > 30:
        return {"status": "error", "message": "Le poids maximum est de 30kg."}
    
    if length > 150 or width > 150 or height > 150:
        return {"status": "error", "message": "Dimensions trop grandes (max 150cm par côté)."}

    if (length + 2 * (width + height)) > 300:
        return {"status": "error", "message": "Le développé total (L + 2W + 2H) dépasse 300cm."}

    try:
        r = requests.post(
            f"{url}?lang=fr_FR",
            data=json.dumps(payload),
            headers=headers,
            impersonate="chrome120",
            timeout=30
        )
        
        if r.status_code != 200:
            return {"status": "error", "message": f"Erreur de l'API Chronopost (Code: {r.status_code})"}
            
        choices = r.json()
        results = []
        
        for service in choices:
            # Prix officiel TTC
            official_price = float(service.get("unitPriceTTC", 0))
            # Calcul du prix réduit
            our_price = round(official_price * CHRONOPOST_DISCOUNT_RATE, 2)
            
            results.append({
                "label": service.get("label"),
                "product_code": service.get("productCode"),
                "official_price": official_price,
                "our_price": our_price,
                "is_relay": service.get("relay", False),
                "delivery_date": service.get("dateDelivery")
            })
            
        return {"status": "success", "offers": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
