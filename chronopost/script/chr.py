import time
import json
import base64
from curl_cffi import requests as cffi_requests
from .headers import HEADERS_1, HEADERS_2, HEADERS_4
from .payload_fr import build_payload_fr
from .payload_express import build_payload_monde, build_payload_relais_europe
import logging

TIMEOUT = 60

def retry_get(url, headers):
    for attempt in range(2):
        r = cffi_requests.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r
    return r

def retry_post(url, headers, data):
    for attempt in range(2):
        r = cffi_requests.post(
            url,
            headers=headers,
            data=data,
            impersonate="chrome120",
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r
    return r

def run_chronopost(payload_data=None):
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    logger.info(f"--- NOUVEAU RUN CHRONOPOST ---")
    logger.info(f"Data reçue: {json.dumps(payload_data) if payload_data else 'None'}")

    try:
        valeur_product = payload_data.get("valeurproduct")
        destination_country = payload_data.get("destinationCountry")
        logger.info(f"Produit: {valeur_product}, Pays: {destination_country}")

        if valeur_product == "monde":
            payload_str = build_payload_monde(data=payload_data)
        elif valeur_product == "relais" and destination_country:
             # Chrono Relais Europe
             payload_str = build_payload_relais_europe(data=payload_data)
        else:
            # Chrono 10, 13, Relais (France standard)
            payload_str = build_payload_fr(data=payload_data)

        # Init debug vars
        r1 = r2 = r3 = req4_response = final_response = None

        # ===================== REQUETE 1 =====================
        URL_1 = (
            "https://www.chronopost.fr/moncompte/"
            "displayCustomerArea.do?iv4Context=d8731416d5d60aac657dd0120cc49f59&lang=fr_FR"
        )
        r1 = retry_get(URL_1, HEADERS_1)

        # ===================== REQUETE 2 =====================
        URL_2 = "https://www.chronopost.fr/expedier/accueilShipping.do?reinit=true&lang=fr_FR"
        HEADERS_2["Referer"] = URL_1
        r2 = retry_get(URL_2, HEADERS_2)

        token = 1768746808705

        # ===================== REQUETE 3 =====================
        if token:
            URL_3 = f"https://www.chronopost.fr/expeditionAvanceeSec/accueilShipping.do?_={token}&lang=fr_FR"
            r3 = retry_get(URL_3, HEADERS_4)

        # ===================== REQUETE 4 (CRITIQUE) =====================
        if token:
            URL_4 = "https://www.chronopost.fr/expeditionAvanceeSec/jsonGeoRouting"
            HEADERS_6 = HEADERS_4.copy()
            HEADERS_6["Content-Type"] = "application/x-www-form-urlencoded"
            req4_response = retry_post(
                URL_4,
                HEADERS_6,
                payload_str
            )

        # ===================== REQUETE 5 =====================
        if token:
            URL_5 = "https://www.chronopost.fr/expeditionAvanceeSec/shippingZPL"
            final_response = retry_post(URL_5, HEADERS_6, payload_str)

        duration = time.time() - start_time

        is_monde = payload_data and payload_data.get("valeurproduct") == "monde"
        check_routing = False
        if req4_response and "true" in req4_response.text.lower():
            check_routing = True



        if final_response and final_response.status_code == 200:
            content = final_response.text
            proforma_res = None
            
            # Logic "monde" -> parse jobName/idArticle -> get_proforma
            if is_monde:
                logger.info("Produit Monde détecté, tentative d'extraction LT et ID Article pour Proforma")
                try:
                    nlabel = None
                    id_article = None
                    if "jobName>" in content:
                        nlabel = content.split("jobName>")[1].split("<")[0]
                        logger.info(f"LT trouvé: {nlabel}")
                    else:
                        logger.warning("Tag <jobName> non trouvé dans la réponse Chronopost")
                        
                    if "idArticle>" in content:
                        id_article = content.split("idArticle>")[1].split("<")[0]
                        logger.info(f"ID Article trouvé: {id_article}")
                    else:
                        logger.warning("Tag <idArticle> non trouvé dans la réponse Chronopost")
                    
                    if nlabel and id_article:
                        proforma_res = get_proforma(nlabel, id_article, HEADERS_6)
                    else:
                        logger.error(f"Impossible de lancer get_proforma: LT={nlabel}, ID={id_article}")
                except Exception as parse_err:
                   logger.error(f"Erreur lors du parsing des tags Proforma: {str(parse_err)}")
                   logger.debug(f"Contenu brut pour investigation: {content[:1000]}")

            return {
                "status": "success",
                "duration": duration,
                "proforma": proforma_res
            }

        return {"status": "error", "message": "Final request failed"}

    except Exception as e:
        # Log détaillé côté serveur
        logging.getLogger(__name__).error(f"Erreur Chronopost: {str(e)}")
        return {"status": "error", "message": "error"}

def get_proforma(nlabel, id_article, headers):
    """
    Récupère la facture Proforma.
    """
    logger = logging.getLogger(__name__)
    url = "https://www.chronopost.fr/expeditionAvanceeSec/getProforma"
    data = f"proFormaLtNumber={nlabel}&proFormaIdArticle={id_article}"
    
    # Headers specific for this request based on user images
    req_headers = headers.copy()
    req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    req_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    
    logger.info(f"DEBUG PROFORMA: Tentative de récupération pour LT={nlabel}, ID={id_article}")
    
    try:
        r = cffi_requests.post(
            url,
            headers=req_headers,
            data=data,
            impersonate="chrome120",
            timeout=30
        )
        logger.info(f"DEBUG PROFORMA: Status Code = {r.status_code}")
        
        if r.status_code == 200:
            content_len = len(r.content)
            is_pdf = r.content.startswith(b"%PDF")
            logger.info(f"DEBUG PROFORMA: Taille reçue = {content_len} octets, Est un PDF = {is_pdf}")
            
            if is_pdf:
                # Return base64 encoded PDF
                return base64.b64encode(r.content).decode('utf-8')
            else:
                logger.warning(f"DEBUG PROFORMA: Le contenu reçu n'est pas un PDF (commence par: {r.content[:20]})")
        else:
            logger.error(f"DEBUG PROFORMA: Erreur lors de la requête (Body: {r.text[:500]})")
            
    except Exception as e:
        logger.error(f"DEBUG PROFORMA: Exception = {str(e)}")
    
    return None

def get_relay_detail(pickup_id, country=None):
    """
    Récupère les détails d'un point relais via son ID.
    Utilise curl_cffi pour simuler un navigateur (chrome120).
    Boucle de 10 tentatives en cas d'erreur ou 403.
    """
    url = f"https://www.chronopost.fr/expeditionAvanceeSec/jsonPointRelaisById.json?pickUpId={pickup_id}"
    if country:
        url += f"&country={country}"
    
    for attempt in range(10):
        try:
            r = cffi_requests.get(
                url,
                headers=HEADERS_4,
                impersonate="chrome120",
                timeout=60
            )
            
            if r.status_code == 200:
                data = json.loads(r.text)
                if data and isinstance(data, list) and len(data) > 0:
                    pr = data[0]
                    return {
                        "status": "success",
                        "nom": pr.get("nom"),
                        "adresse": pr.get("adresse1"),
                        "cp": pr.get("codePostal"),
                        "ville": pr.get("localite")
                    }
                # If 200 but empty data/wrong format, might be a soft error, but usually we can stop or retry? 
                # User said "tant que response code = 200 n'est pas atteint". 
                # If we get 200 but invalid data (empty list), it's technically a 200.
                # But let's assume 200 needs to give us data. 
                # For safety, if data is empty, maybe retry? 
                # Let's stick to status_code check as primary request.
                return {"status": "error", "message": "Aucune donnée trouvée"}
            
            # If not 200, loop continues
            time.sleep(0.5) # Small buffer
            
        except Exception as e:
            # On exception, loop continues
            time.sleep(0.5)
            
    return {"status": "error", "message": "Erreur: rechargé la page ou contactez le gerant"}
