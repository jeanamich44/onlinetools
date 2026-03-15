import requests
import logging
from .p_utils import USER_AGENT

# Configuration du logging
logger = logging.getLogger(__name__)

# URL de l'API de tarification Colissimo (Endpoint standard)
TARIFS_URL = "https://ws.colissimo.fr/tarification-ws/rest/service/tarifs"

def get_colissimo_price(data, config):
    """
    Calcule le prix d'un envoi Colissimo via l'API de tarification.
    """
    
    # Nettoyage de la date (format attendu: YYYY-MM-DD)
    shipping_date = data.get("shipping_date")
    if not shipping_date:
        from datetime import datetime
        shipping_date = datetime.now().strftime("%Y-%m-%d")

    # Préparation du payload pour l'API Tarification
    payload = {
        "identifiants": {
            "contractNumber": config.get("id"),
            "password": config.get("key")
        },
        "envoi": {
            "poids": data.get("weight"),
            "dateEnvoi": shipping_date,
            "paysExpediteur": data.get("sender_iso", "FR"),
            "codePostalExpediteur": data.get("sender_zip"),
            "paysDestinataire": data.get("recipient_iso", "FR"),
            "codePostalDestinataire": data.get("recipient_zip"),
            "typeProduit": data.get("product_code", "DOM")
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }

    try:
        logger.info(f"Appel API Tarification Colissimo pour le contrat {config['id']}")
        # Log du payload sans le mot de passe pour le debug
        debug_payload = payload.copy()
        debug_payload["identifiants"]["password"] = "****"
        logger.info(f"Payload simulation: {debug_payload}")

        response = requests.post(TARIFS_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            # Gestion du cas où la réponse est une liste (rare sur cet endpoint mais possible)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            # Recherche du prix (montant en centimes généralement)
            price_raw = result.get("tarif") or result.get("montant")
            if not price_raw and "service" in result:
                price_raw = result["service"].get("prix") or result["service"].get("prixCalculé") or result["service"].get("montant")
            
            if price_raw is not None:
                # L'API renvoie souvent le prix en centimes (entier ou float)
                official_price = float(price_raw) / 100
                
                if data.get("package_format") == "VOL":
                    official_price += 6.0
                    
                delivery_date = result.get("dateLivraison")
                if not delivery_date and "service" in result:
                    delivery_date = result["service"].get("dateLivraison")
                
                label = result.get("libelleProduit")
                if not label and "service" in result:
                    label = result["service"].get("libelleProduit", "Colissimo")
                elif not label:
                    label = "Colissimo"

                return {
                    "status": "success",
                    "price": official_price,
                    "delivery_date": delivery_date,
                    "label": label
                }
            else:
                logger.error(f"Réponse API sans tarif: {result}")
        
        # En cas d'erreur, on capture le message si c'est du JSON
        error_detail = response.text
        try:
            err_json = response.json()
            if "messages" in err_json:
                error_detail = " | ".join([m.get("messageContent", "") for m in err_json["messages"]])
        except:
            pass

        logger.error(f"Erreur API Tarification Colissimo ({response.status_code}): {error_detail}")
        return {"status": "error", "message": error_detail}

    except Exception as e:
        logger.error(f"Erreur technique Tarification Colissimo: {str(e)}")
        return {"status": "error", "message": "Erreur technique serveur"}
