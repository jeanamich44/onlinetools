import time
import json
import base64
from curl_cffi import requests as cffi_requests
from .headers import HEADERS_1, HEADERS_2, HEADERS_4
from .payload_fr import build_payload_fr
from .payload_express import build_payload_monde, build_payload_relais_europe
import logging

TIMEOUT = 60

def retry_get(url, headers, session=None):
    client = session if session else cffi_requests
    for attempt in range(2):
        r = client.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r
    return r

def retry_post(url, headers, data, session=None):
    client = session if session else cffi_requests
    for attempt in range(2):
        r = client.post(
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
    session = cffi_requests.Session(impersonate="chrome120")
    
    logger.info("--- NOUVEAU RUN CHRONOPOST ---")

    try:
        valeur_product = payload_data.get("valeurproduct")
        destination_country = payload_data.get("destinationCountry")
        
        if valeur_product == "monde":
            payload_str = build_payload_monde(data=payload_data)
        elif valeur_product == "relais" and destination_country:
             payload_str = build_payload_relais_europe(data=payload_data)
        else:
            payload_str = build_payload_fr(data=payload_data)

        r1 = r2 = r3 = req4_response = final_response = None

        # ===================== REQUETE 1 =====================
        URL_1 = (
            "https://www.chronopost.fr/moncompte/"
            "displayCustomerArea.do?iv4Context=d8731416d5d60aac657dd0120cc49f59&lang=fr_FR"
        )
        r1 = retry_get(URL_1, HEADERS_1, session=session)

        URL_2 = "https://www.chronopost.fr/expedier/accueilShipping.do?reinit=true&lang=fr_FR"
        HEADERS_2["Referer"] = URL_1
        r2 = retry_get(URL_2, HEADERS_2, session=session)

        token = 1768746808705

        if token:
            URL_3 = f"https://www.chronopost.fr/expeditionAvanceeSec/accueilShipping.do?_={token}&lang=fr_FR"
            r3 = retry_get(URL_3, HEADERS_4, session=session)

        if token:
            URL_4 = "https://www.chronopost.fr/expeditionAvanceeSec/jsonGeoRouting"
            HEADERS_6 = HEADERS_4.copy()
            HEADERS_6["Content-Type"] = "application/x-www-form-urlencoded"
            req4_response = retry_post(
                URL_4,
                HEADERS_6,
                payload_str,
                session=session
            )

        if token:
            URL_5 = "https://www.chronopost.fr/expeditionAvanceeSec/shippingZPL"
            final_response = retry_post(URL_5, HEADERS_6, payload_str, session=session)

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
                    if "idArticle>" in content:
                        id_article = content.split("idArticle>")[1].split("<")[0]

                    if nlabel and id_article:
                        proforma_res = get_proforma(nlabel, id_article, HEADERS_6, session=session)
                    else:
                        logger.error(f"Echec extraction Proforma: LT={nlabel}, ID={id_article}.")
                except Exception as parse_err:
                   logger.error(f"Exception parsing Proforma: {str(parse_err)}")

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

def get_proforma(nlabel, id_article, headers, session=None):
    """
    Récupère la facture Proforma via la session active.
    """
    logger = logging.getLogger(__name__)
    url = "https://www.chronopost.fr/expeditionAvanceeSec/getProforma"
    data = f"proFormaLtNumber={nlabel}&proFormaIdArticle={id_article}"
    
    req_headers = headers.copy()
    req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    req_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    
    logger.info(f"DEBUG PROFORMA: Tentative avec LT={nlabel}")
    
    try:
        client = session if session else cffi_requests
        r = client.post(
            url,
            headers=req_headers,
            data=data,
            impersonate="chrome120",
            timeout=30
        )
        logger.info(f"DEBUG PROFORMA: Status Code = {r.status_code}")
        
        if r.status_code == 200:
            if r.content.startswith(b"%PDF"):
                return base64.b64encode(r.content).decode('utf-8')
            else:
                logger.warning(f"Contenu non-PDF reçu: {r.content[:50]}")
        else:
            logger.error(f"Echec Proforma (Code {r.status_code})")
            
    except Exception as e:
        logger.error(f"Exception Proforma: {str(e)}")
    
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
