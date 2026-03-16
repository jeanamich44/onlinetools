import requests
import json
import logging
import email
import base64
from email.policy import default
from datetime import datetime
import fitz
from .p_utils import geocode_zip, USER_AGENT

# =========================
# CONFIGURATION
# =========================

logger = logging.getLogger(__name__)
PATCH_BASE_URL = "https://ws.colissimo.fr/sls-ws/SlsServiceWSRest/3.1"
GENERATE_LABEL_URL = f"{PATCH_BASE_URL}/generateLabel"
CHECK_LABEL_URL = f"{PATCH_BASE_URL}/checkGenerateLabel"
PLAN_PICKUP_URL = f"{PATCH_BASE_URL}/planPickup"

def parse_multipart_response(response):
    content_type = response.headers.get("Content-Type", "")
    
    if "multipart" not in content_type:
        try:
            return response.json(), {}
        except:
            return {"error": "Réponse non JSON et non Multipart"}, {}

    msg_data = b"Content-Type: " + content_type.encode("utf-8") + b"\r\n\r\n" + response.content
    msg = email.message_from_bytes(msg_data, policy=default)
    
    json_infos = {}
    payloads = {}
    
    for part in msg.iter_parts():
        ctype = part.get_content_type()
        
        if ctype == "application/json":
            json_infos = json.loads(part.get_payload(decode=True))
        else:
            payloads[part_name] = part.get_payload(decode=True)
            
    return json_infos, payloads

# =========================
# GENERATION ETIQUETTE
# =========================

def run_colissimo(data, config, method="generateLabel"):
    
    if method == "generateLabel":
        url = GENERATE_LABEL_URL
    elif method == "checkGenerateLabel":
        url = CHECK_LABEL_URL
    elif method == "planPickup":
        url = PLAN_PICKUP_URL
    else:
        return {"status": "error"}
    
    payload = {
        "contractNumber": config.get("id"),
        "password": config.get("key")
    }

    if method in ["generateLabel", "checkGenerateLabel"]:
        payload.update({
            "outputFormat": {
                "x": 0, "y": 0,
                "outputPrintingType": data.get("outputType", "PDF_A4_300dpi")
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

        if data.get("productCode") == "COL" and data.get("pickupLocationId"):
            pickup_type = data.get("pickupLocationType", "A2P")
            payload["letter"]["service"]["productCode"] = pickup_type
            payload["letter"]["addressee"]["pickupLocationId"] = data["pickupLocationId"]
            payload["letter"]["addressee"]["pickupLocationType"] = pickup_type
        if data.get("customs"):
            payload["letter"]["customsDeclarations"] = data["customs"]
            
    elif method == "planPickup":
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
            if method in ["generateLabel", "checkGenerateLabel"]:
                if "label" in files:
                    try:
                        pdf_doc = fitz.open(stream=files["label"], filetype="pdf")
                        page = pdf_doc[0]
                        contract_id = str(config.get("id"))
                        texts_to_hide = [f"Compte : {contract_id}", f"Compte :{contract_id}", "Compte :", contract_id]
                        
                        for text in texts_to_hide:
                            rects = page.search_for(text)
                            for rect in rects:
                                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                
                        files["label"] = pdf_doc.write()
                        pdf_doc.close()
                    except Exception as pdf_err:
                        logger.warning(f"Impossible de masquer le contrat sur le PDF: {str(pdf_err)}")
                        
                    return {
                        "status": "success",
                        "label": base64.b64encode(files["label"]).decode('utf-8')
                    }
            return {"status": "success"}
        else:
            return {"status": "failed"}

    except Exception as e:
        logger.error(f"Erreur technique Colissimo: {str(e)}")
        return {"status": "failed"}


# =========================
# RECHERCHE POINTS RELAIS
# =========================

def search_relays_colissimo(zip_code, config=None):
    logger.info(f"Recherche de points de retrait Colissimo pour le CP: {zip_code}")
    
    lat, lon = geocode_zip(zip_code)
    
    url = "https://localiser.laposte.fr/index.html"
    params = {
        "jesuis": "particulier",
        "contact": "depot",
        "r": "10",
        "per": "30",
        "l": "fr"
    }
    
    if lat and lon:
        params["q"] = f"{lat},{lon}"
        params["qp"] = f"{zip_code}, France"
        logger.info(f"Appel API La Poste avec coordonnées: {params['q']}")
    else:
        params["qp"] = zip_code
        params["q"] = zip_code
        logger.info(f"Appel API La Poste avec CP uniquement (Fallback): {zip_code}")

    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        logger.info(f"Réponse API La Poste: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            entities = data.get("response", {}).get("entities", [])
            
            formatted_relays = []
            for item in entities:
                try:
                    p = item.get("profile", {})
                    address_obj = p.get("address", {})
                    coords = p.get("yextDisplayCoordinate", {})
                    
                    relay_id = p.get("meta", {}).get("yextId") or p.get("meta", {}).get("uid")
                    
                    raw_type = p.get("c_typePointDeContact", "")
                    relay_type = "A2P"
                    if raw_type and "BUREAU" in str(raw_type).upper(): relay_type = "BPR"
                    if raw_type and "CONSIGNE" in str(raw_type).upper(): relay_type = "PCS"

                    distance_raw = item.get("distance", 0)
                    distance_km = 0
                    if isinstance(distance_raw, (int, float)):
                        distance_km = float(distance_raw) / 1000
                    elif isinstance(distance_raw, str) and distance_raw.replace('.','',1).isdigit():
                        distance_km = float(distance_raw) / 1000
                    elif isinstance(distance_raw, dict):
                        val = distance_raw.get("value", 0)
                        distance_km = float(val) / 1000 if isinstance(val, (int, float, str)) else 0

                    formatted_relays.append({
                        "id": relay_id,
                        "name": p.get("geomodifier") or p.get("c_intituléÉtablissement") or p.get("c_intituleEtablissement") or p.get("name") or "Point de retrait",
                        "address": address_obj.get("line1", ""),
                        "zip": address_obj.get("postalCode", ""),
                        "city": address_obj.get("city", ""),
                        "type": relay_type,
                        "lat": coords.get("lat"),
                        "lng": coords.get("long"),
                        "distance": distance_km
                    })
                except Exception as item_err:
                    logger.error(f"Erreur lors du traitement d'un point relais: {str(item_err)}")
                    continue
            
            return {"status": "success", "relays": formatted_relays}
        else:
            return {"status": "error"}
            
    except Exception as e:
        logger.error(f"Erreur technique recherche: {str(e)}")
        return {"status": "technical error"}

