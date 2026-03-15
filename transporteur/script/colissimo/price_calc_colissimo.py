import requests
import logging
from .p_utils import USER_AGENT

# Configuration du logging
logger = logging.getLogger(__name__)

# URL de l'API de tarification Colissimo (Endpoint identifié via le site web)
TARIFS_URL = "https://www.laposte.fr/colis/occ/ecommerce/occ/v2/lpelPart/e-service/colis/price"

def get_colissimo_price(data, config):
    """
    Calcule le prix d'un envoi Colissimo via l'API de tarification web.
    """
    
    # Mapping des modes de dépôt et formats pour l'API Web
    shipping_mode = data.get("shipping_mode", "BDP")
    deposit_mode = "D_BAL" if shipping_mode == "BAL" else "D_BP"
    
    package_format = data.get("package_format", "STND")
    fmt = "F_VOL" if package_format == "VOL" else "F_STD"

    # Préparation du payload pour l'API Tarification (nouveau format)
    payload = {
        "depositMode": deposit_mode,
        "departureAddress": None,
        "pickingDate": None,
        "deliveryMode": "L_BAL", 
        "insurance": None,
        "insuredValue": None,
        "insuredMaxValue": None,
        "pickUpReturnedPackage": None,
        "eco": False,
        "destinationAddress": None,
        "cn23": None,
        "departureCountry": data.get("sender_iso", "FR"),
        "arrivalCountry": data.get("recipient_iso", "FR"),
        "weight": int(float(data.get("weight", 0.1)) * 1000), # Poids en grammes
        "format": fmt,
        "arrivalAddress": None,
        "id": None,
        "bundleUniqueId": None
    }

    # Adaptation spécifique du deliveryMode selon le product_code
    pc = data.get("product_code", "DOM")
    if pc in ["COL", "CORI"]:
        payload["deliveryMode"] = "L_A2P"
    elif pc == "BPR":
        payload["deliveryMode"] = "L_BPR"
    else:
        payload["deliveryMode"] = "L_BAL"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }

    try:
        logger.info(f"Appel API Tarification Colissimo Web (OCC)")
        response = requests.post(TARIFS_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            # Recherche du prix dans le format OCC
            price_obj = result.get("totalPrice") or result.get("postagePrice")
            if price_obj:
                official_price = float(price_obj.get("value", 0))
                
                return {
                    "status": "success",
                    "price": official_price,
                    "delivery_date": None, # Non fourni directement par ce point de terminaison spécifique
                    "label": "Colissimo Standard"
                }
            else:
                logger.error(f"Réponse API OCC sans tarif: {result}")
        
        error_detail = response.text
        logger.error(f"Erreur API Tarification Colissimo Web ({response.status_code}): {error_detail}")
        return {"status": "error", "message": "Impossible de récupérer le tarif actuel auprès de La Poste."}

    except Exception as e:
        logger.error(f"Erreur technique Tarification Colissimo Web: {str(e)}")
        return {"status": "error", "message": "Erreur technique serveur"}
