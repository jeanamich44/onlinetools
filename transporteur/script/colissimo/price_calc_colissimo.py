import requests
import logging
from .p_utils import USER_AGENT

# Configuration du logging
logger = logging.getLogger(__name__)

# URL de l'API de tarification Colissimo
TARIFS_URL = "https://ws.colissimo.fr/tarification-ws/rest/tarifs"

def get_colissimo_price(data, config):
    """
    Calcule le prix d'un envoi Colissimo via l'API de tarification.
    data contient: sender_zip, recipient_zip, recipient_iso, weight, etc.
    config contient: id, key
    """
    
    # Préparation du payload pour l'API Tarification
    payload = {
        "identifiants": {
            "contractNumber": config.get("id"),
            "password": config.get("key")
        },
        "envoi": {
            "poids": data.get("weight"),
            "dateEnvoi": data.get("shipping_date"),
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
        logger.info(f"Appel API Tarification Colissimo pour le contrat {config['id']}")
        response = requests.post(TARIFS_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            # Traitement de la réponse pour extraire le prix
            if result.get("tarif") is not None:
                official_price = float(result["tarif"]) / 100 # Le prix est souvent en centièmes
                return {
                    "status": "success",
                    "price": official_price,
                    "delivery_date": result.get("dateLivraison"),
                    "label": result.get("libelleProduit", "Colissimo")
                }
        
        logger.error(f"Erreur API Tarification Colissimo: {response.text}")
        return {"status": "error"}

    except Exception as e:
        logger.error(f"Erreur technique Tarification Colissimo: {str(e)}")
        return {"status": "error"}
