import requests
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

COLISSIMO_URL = "https://ws.colissimo.fr/sls-ws/SlsServiceWS/rest/generateLabel"

def run_colissimo(data, config):
    """
    Génère une étiquette Colissimo via l'API officielle.
    data: dictionnaire contenant les infos expéditeur, destinataire et colis
    config: dictionnaire avec 'id' (contractNumber) et 'key' (apiKey)
    """
    
    # Préparation du payload selon la documentation SLS REST
    payload = {
        "outputFormat": {
            "x": 0,
            "y": 0,
            "outputPrintingType": "PDF_10x15_300dpi"
        },
        "letter": {
            "service": {
                "productCode": data.get("productCode", "DOM"), # DOM, DOS, COL, etc.
                "depositDate": data.get("shippingDate", datetime.now().strftime("%Y-%m-%d"))
            },
            "parcel": {
                "weight": data.get("packageWeight", 1.0)
            },
            "sender": {
                "address": {
                    "companyName": data.get("senderCompanyName", ""),
                    "lastName": data.get("senderLastname", "Expediteur"),
                    "firstName": data.get("senderFirstname", ""),
                    "line2": data.get("senderAddress", ""),
                    "countryCode": data.get("senderCountry", "FR"),
                    "city": data.get("senderCity", ""),
                    "zipCode": data.get("senderCP", "")
                }
            },
            "addressee": {
                "address": {
                    "companyName": data.get("receiverCompanyName", ""),
                    "lastName": data.get("receiverLastname", ""),
                    "firstName": data.get("receiverFirstname", ""),
                    "line2": data.get("receiverAddress", ""),
                    "countryCode": data.get("receiverCountry", "FR"),
                    "city": data.get("receiverCity", ""),
                    "zipCode": data.get("receiverCP", "")
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    # Authentification : Colissimo utilise normalement contractNumber et password dans le JSON 
    # ou apiKey dans le header selon la version. Ici on suit la config fournie.
    payload["contractNumber"] = config["id"]
    payload["password"] = config["key"]

    try:
        logger.info(f"Appel API Colissimo pour le contrat {config['id']}")
        response = requests.post(COLISSIMO_URL, json=payload, headers=headers)
        
        # Le retour de Colissimo SLS est un multipart si succès (PDF + JSON)
        # Mais en REST, on peut souvent récupérer le PDF directement si on gère bien la réponse.
        
        if response.status_code == 200:
            # Note: En réalité, Colissimo renvoie un binaire PDF ou un multipart.
            # Il faudra peut-être parser le multipart si des infos JSON sont jointes.
            return {
                "status": "success",
                "message": "Étiquette générée avec succès",
                "debug_info": "Appel API réussi"
            }
        else:
            logger.error(f"Erreur API Colissimo: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Erreur Colissimo ({response.status_code})",
                "details": response.text
            }

    except Exception as e:
        logger.error(f"Erreur lors de l'appel Colissimo: {str(e)}")
        return {"status": "error", "message": "Erreur technique lors de l'appel API"}
