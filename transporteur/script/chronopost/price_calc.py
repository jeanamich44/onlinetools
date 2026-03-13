from curl_cffi import requests
import json

def get_chronopost_price(data):
    """
    Calcule le prix TTC d'un envoi Chronopost.
    Applique une réduction de 50% sur le tarif officiel.
    """
    url = "https://www.chronopost.fr/wsmchronoweb-rest/offre/list"
    
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
                "height": data.get("height"),
                "width": data.get("width"),
                "length": data.get("length"),
                "weight": data.get("weight"),
                "policyValue": 0,
                "productDescriptionCode": "",
                "productDescriptionLabel": "",
                "valueDeclared": 0
            }
        ]
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "fr-FR,fr;q=0.9",
        "content-type": "application/json",
        "cookie": "lang=fr_FR; JSESSIONID_WSREST=.tc-mchronoweb-NODE7; parcours=Particulier; parcoursId=2;",
        "origin": "https://www.chronopost.fr",
        "priority": "u=1, i",
        "referer": "https://www.chronopost.fr/small-webapp/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    try:
        r = requests.post(
            f"{url}?lang=fr_FR",
            data=json.dumps(payload),
            headers=headers,
            impersonate="chrome120",
            timeout=30
        )
        
        if r.status_code != 200:
            return {"status": "error", "message": f"Erreur API Chronopost: {r.status_code}"}
            
        choices = r.json()
        results = []
        
        for service in choices:
            # Prix officiel TTC
            official_price = float(service.get("unitPriceTTC", 0))
            # Notre prix à -50%
            our_price = round(official_price / 2, 2)
            
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

if __name__ == "__main__":
    # Test rapide si lancé en direct
    test_data = {
        "sender_zip": "75001",
        "sender_city": "PARIS",
        "recipient_zip": "31000",
        "recipient_city": "TOULOUSE",
        "weight": 2.0
    }
    print(json.dumps(get_chronopost_price(test_data), indent=2, ensure_ascii=False))
