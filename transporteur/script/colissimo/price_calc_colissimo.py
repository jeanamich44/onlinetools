import requests
import logging
from .p_utils import USER_AGENT

# Configuration du logging
logger = logging.getLogger(__name__)

# URL de l'API de tarification Colissimo (Endpoint Checkout plus robuste)
TARIFS_URL = "https://ws.colissimo.fr/tarification-ws/rest/tarifsCheckout"

def get_colissimo_price(data, config):
    """
    Calcule le prix d'un envoi Colissimo via l'API de tarification.
    """
    
    # Nettoyage de la date (format attendu: YYYY-MM-DD)
    shipping_date = data.get("shipping_date")
    if not shipping_date:
        from datetime import datetime
        shipping_date = datetime.now().strftime("%Y-%m-%d")

    # Préparation du payload pour l'API Tarification Checkout
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
        "User-Agent": USER_AGENT
    }

    try:
        logger.info(f"Appel API Tarification Checkout Colissimo pour le contrat {config['id']}")
        # Log du payload sans le mot de passe pour le debug
        debug_payload = payload.copy()
        debug_payload["identifiants"]["password"] = "****"
        logger.info(f"Payload simulation: {debug_payload}")

        response = requests.post(TARIFS_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            # Dans l'API Checkout, le prix est souvent dans "montant" ou "tarif"
            # On vérifie les deux cas
            price_raw = result.get("tarif") or result.get("montant")
            
            if price_raw is not None:
                official_price = float(price_raw) / 100
                
                if data.get("package_format") == "VOL":
                    official_price += 6.0
                    
                return {
                    "status": "success",
                    "price": official_price,
                    "delivery_date": result.get("dateLivraison"),
                    "label": result.get("libelleProduit", "Colissimo")
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

        logger.error(f"Erreur API Tarification Colissimo: {error_detail}")
        return {"status": "error", "message": error_detail}

    except Exception as e:
        logger.error(f"Erreur technique Tarification Colissimo: {str(e)}")
        return {"status": "error", "message": "Erreur technique serveur"}
