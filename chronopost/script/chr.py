import time
import json
import base64
from curl_cffi import requests as cffi_requests
from .headers import HEADERS_1, HEADERS_2, HEADERS_4
from .payload_fr import build_payload_fr
from .payload_express import build_payload_monde, build_payload_relais_europe

TIMEOUT = 60

def retry_get(url, headers, stop_on_fail=False):
    for attempt in range(2):
        r = cffi_requests.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r
    if stop_on_fail:
        raise Exception("STOP: response != 200")
    return r

def retry_post(url, headers, data, stop_on_fail=False, check_false=False):
    for attempt in range(2):
        r = cffi_requests.post(
            url,
            headers=headers,
            data=data,
            impersonate="chrome120",
            timeout=TIMEOUT
        )
        if r.status_code == 200 and (not check_false or "false" not in r.text.lower()):
            return r
    if stop_on_fail:
        raise Exception("STOP: jsonGeoRouting failed or contained 'false'")
    return r

def run_chronopost(payload_data=None):
    start_time = time.time()

    try:
        valeur_product = payload_data.get("valeurproduct")
        destination_country = payload_data.get("destinationCountry")

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
                payload_str,
                stop_on_fail=True,
                check_false=True
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
                try:
                    nlabel = None
                    id_article = None
                    if "jobName>" in content:
                        nlabel = content.split("jobName>")[1].split("<")[0]
                    if "idArticle>" in content:
                        id_article = content.split("idArticle>")[1].split("<")[0]
                    
                    if nlabel and id_article:
                        proforma_res = get_proforma(nlabel, id_article, HEADERS_6)
                except Exception:
                   pass

            return {
                "status": "success",
                "duration": duration,
                "routing": check_routing,
                "content": None,
                "proforma": proforma_res
            }

        return {"status": "error", "message": "Final request failed", "routing": check_routing}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_proforma(nlabel, id_article, headers):
    """
    Récupère la facture Proforma.
    """
    url = "https://www.chronopost.fr/expeditionAvanceeSec/getProforma"
    data = f"proFormaLtNumber={nlabel}&proFormaIdArticle={id_article}"
    
    # Headers specific for this request based on user images
    req_headers = headers.copy()
    req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    req_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    
    try:
        r = cffi_requests.post(
            url,
            headers=req_headers,
            data=data,
            impersonate="chrome120",
            timeout=30
        )
        if r.status_code == 200:
            # Return base64 encoded PDF
            return base64.b64encode(r.content).decode('utf-8')
    except Exception:
        pass
    return None

def get_relay_detail(pickup_id):
    """
    Récupère les détails d'un point relais via son ID.
    Utilise curl_cffi pour simuler un navigateur (chrome120).
    """
    url = f"https://www.chronopost.fr/expeditionAvanceeSec/jsonPointRelaisById.json?pickUpId={pickup_id}"
    
    try:
        r = cffi_requests.get(
            url,
            headers=HEADERS_4,
            impersonate="chrome120",
            timeout=60
        )
        
        if r.status_code != 200:
             return {"status": "error", "message": f"HTTP {r.status_code}"}
        
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
        return {"status": "error", "message": "Aucune donnée trouvée"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
