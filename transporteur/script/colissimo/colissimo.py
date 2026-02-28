import requests
import logging
import json
import email
import base64
from email.policy import default
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)

# URLs de l'API Colissimo SLS REST v3.1
PATCH_BASE_URL = "https://ws.colissimo.fr/sls-ws/SlsServiceWSRest/3.1"
GENERATE_LABEL_URL = f"{PATCH_BASE_URL}/generateLabel"
CHECK_LABEL_URL = f"{PATCH_BASE_URL}/checkGenerateLabel"
PLAN_PICKUP_URL = f"{PATCH_BASE_URL}/planPickup"

def parse_multipart_response(response):
    """
    Parse une réponse multipart/related de Colissimo pour extraire le JSON et les fichiers (PDF/CN23).
    """
    content_type = response.headers.get("Content-Type", "")
    
    if "multipart" not in content_type:
        try:
            return response.json(), {}
        except:
            return {"error": "Réponse non JSON et non Multipart"}, {}

    # L'email.message_from_bytes a besoin du header Content-Type pour savoir comment parser
    msg_data = b"Content-Type: " + content_type.encode("utf-8") + b"\r\n\r\n" + response.content
    msg = email.message_from_bytes(msg_data, policy=default)
    
    json_infos = {}
    payloads = {}
    
    for part in msg.iter_parts():
        ctype = part.get_content_type()
        
        if ctype == "application/json":
            json_infos = json.loads(part.get_payload(decode=True))
        else:
            # On stocke les fichiers binaires (étiquettes, douanes, etc.)
            part_name = part.get_param("name", header="Content-Disposition") or part.get_filename() or "label"
            payloads[part_name] = part.get_payload(decode=True)
            
    return json_infos, payloads

def run_colissimo(data, config, method="generateLabel"):
    """
    Exécute une méthode de l'API SLS REST v3.1.
    method: 'generateLabel', 'checkGenerateLabel' ou 'planPickup'
    """
    
    if method == "generateLabel":
        url = GENERATE_LABEL_URL
    elif method == "checkGenerateLabel":
        url = CHECK_LABEL_URL
    elif method == "planPickup":
        url = PLAN_PICKUP_URL
    else:
        return {"status": "error", "message": f"Méthode non supportée: {method}"}
    
    # Payload de base
    payload = {
        "contractNumber": config.get("id"),
        "password": config.get("key")
    }

    # Configuration spécifique selon la méthode
    if method in ["generateLabel", "checkGenerateLabel"]:
        payload.update({
            "outputFormat": {
                "x": 0, "y": 0,
                "outputPrintingType": data.get("outputType", "PDF_10x15_300dpi")
            },
            "letter": {
                "service": {
                    "productCode": data.get("productCode", "DOM"),
                    "depositDate": data.get("shippingDate", datetime.now().strftime("%Y-%m-%d")),
                    "totalAmount": data.get("totalAmount", 0),
                    "orderNumber": data.get("orderNumber", ""),
                    "ftd": True  # Franc de Taxes et Droits : l'expéditeur paie les taxes (DDP)
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
                        "line3": data.get("senderAddress2", ""),
                        "countryCode": data.get("senderCountry", "FR"),
                        "city": data.get("senderCity", ""),
                        "zipCode": data.get("senderCP", ""),
                        "phoneNumber": data.get("senderPhone", ""),
                        "mobileNumber": data.get("senderMobile", ""),
                        "email": data.get("senderEmail", "")
                    }
                },
                "addressee": {
                    "address": {
                        "companyName": data.get("receiverCompanyName", ""),
                        "lastName": data.get("receiverLastname", ""),
                        "firstName": data.get("receiverFirstname", ""),
                        "line2": data.get("receiverAddress", ""),
                        "line3": data.get("receiverAddress2", ""),
                        "countryCode": data.get("receiverCountry", "FR"),
                        "city": data.get("receiverCity", ""),
                        "zipCode": data.get("receiverCP", ""),
                        "phoneNumber": data.get("receiverPhone", ""),
                        "mobileNumber": data.get("receiverMobile", ""),
                        "email": data.get("receiverEmail", "")
                    }
                }
            }
        })

        # Gestion spécifique du Point Relais (Product Code COL)
        if data.get("productCode") == "COL" and data.get("pickupLocationId"):
            payload["letter"]["addressee"]["pickupLocationId"] = data["pickupLocationId"]
            # Par défaut pour Relais Pickup si non précisé
            payload["letter"]["addressee"]["pickupLocationType"] = data.get("pickupLocationType", "A2P")
        if data.get("customs"):
            payload["letter"]["customsDeclarations"] = data["customs"]
            
    elif method == "planPickup":
        # Spécifique au retrait en boîte aux lettres (Retour par exemple)
        payload.update({
            "parcelNumber": data.get("parcelNumber"),
            "mailBoxPickingDate": data.get("pickupDate"),
            "sender": {
                "address": {
                    "lastName": data.get("senderLastname"),
                    "firstName": data.get("senderFirstname"),
                    "line2": data.get("senderAddress"),
                    "zipCode": data.get("senderCP"),
                    "city": data.get("senderCity"),
                    "countryCode": "FR"
                }
            }
        })

    headers = {
        "Content-Type": "application/json",
        "apikey": config.get("apikey") or config.get("key")
    }
    
    try:
        logger.info(f"Appel API Colissimo ({method}) pour le contrat {config['id']}")
        response = requests.post(url, json=payload, headers=headers)
        
        json_infos, files = parse_multipart_response(response)
        messages = json_infos.get("messages", [])
        errors = [m for m in messages if m.get("type") == "ERROR"]
        
        if response.status_code == 200 and not errors:
            result = {
                "status": "success",
                "message": "Opération réussie",
                "json": json_infos
            }
            if method in ["generateLabel", "checkGenerateLabel"]:
                result["parcelNumber"] = json_infos.get("labelV2Response", {}).get("parcelNumber")
                
                # Conversion des binaires en Base64 pour le client
                if "label" in files:
                    result["label"] = base64.b64encode(files["label"]).decode('utf-8')
                if "cn23" in files:
                    result["cn23"] = base64.b64encode(files["cn23"]).decode('utf-8')
                    
            return result
        else:
            error_msg = errors[0].get("messageContent") if errors else f"Erreur {response.status_code}"
            return {"status": "error", "message": error_msg, "details": json_infos}

    except Exception as e:
        logger.error(f"Erreur technique Colissimo: {str(e)}")
        return {"status": "error", "message": str(e)}

def search_relays_colissimo(zip_code, config):
    """
    Recherche les points de retrait Colissimo par code postal.
    """
    logger.info(f"Recherche de points de retrait Colissimo pour le CP: {zip_code}")
    url = "https://ws.colissimo.fr/pointretrait-ws-cxf/PointRetraitServiceRest/2.0/recherchePointRetraitParCP"
    params = {
        "accountNumber": config.get("id"),
        "password": config.get("key"),
        "zipCode": zip_code,
        "countryCode": "FR",
        "weight": "1"
    }
    
    try:
        # On force l'acceptation du JSON
        headers = {"Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            relays = data.get("listePointRetrait", [])
            
            formatted_relays = []
            for r in relays:
                formatted_relays.append({
                    "id": r.get("identifiant"),
                    "name": r.get("nom"),
                    "address": r.get("adresse1"),
                    "zip": r.get("codePostal"),
                    "city": r.get("localite"),
                    "type": r.get("typeDePoint"), # A2P, BPR, etc.
                    "lat": float(r.get("coordGeographiqueLatitude", 0)),
                    "lng": float(r.get("coordGeographiqueLongitude", 0))
                })
            
            return {"status": "success", "relays": formatted_relays}
        else:
            logger.error(f"Erreur API Colissimo PointRetrait: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"Erreur API Colissimo ({response.status_code})"}
            
    except Exception as e:
        logger.error(f"Erreur technique lors de la recherche Colissimo: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Exemple de test (remplacer par des vraies clés)
    test_config = {"id": "123456", "key": "API_KEY_HERE"}
    test_data = {
        "senderLastname": "Dupont",
        "senderAddress": "10 rue de la Paix",
        "senderCP": "75001",
        "senderCity": "Paris",
        "receiverLastname": "Martin",
        "receiverAddress": "5 avenue des Champs",
        "receiverCP": "75008",
        "receiverCity": "Paris",
        "packageWeight": 0.5
    }
    # print(run_colissimo(test_data, test_config, method="checkGenerateLabel"))
