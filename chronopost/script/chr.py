import requests, time, os, json, base64
from .headers import HEADERS_1, HEADERS_2, HEADERS_4
from .payloads import build_payload

# ===================== PAYLOAD BUILD =====================

API_KEY = "a5fce98010bb9761a1d1a21af271d994"
SCRAPER_URL = "https://api.scraperapi.com/"
TIMEOUT = 60

def retry_get(url, headers, stop_on_fail=False):
    for attempt in range(2):
        t0 = time.time()
        r = requests.get(
            SCRAPER_URL,
            params={
                "api_key": API_KEY,
                "url": url,
                "keep_headers": "true",
                "render": "true",
            },
            headers=headers,
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r
    if stop_on_fail:
        raise Exception("STOP: response != 200")
    return r

def retry_post(url, headers, data, stop_on_fail=False, check_false=False):
    for attempt in range(2):
        t0 = time.time()
        r = requests.post(
            SCRAPER_URL,
            params={
                "api_key": API_KEY,
                "url": url,
                "keep_headers": "true",
                "premium": "true"
            },
            headers=headers,
            data=data,
            timeout=TIMEOUT
        )
        if r.status_code == 200 and (not check_false or "false" not in r.text.lower()):
            return r
    if stop_on_fail:
        raise Exception("STOP: jsonGeoRouting failed or contained 'false'")
    return r

def run_chronopost(payload_data=None):
    """
    Main entry point for generating the label.
    payload_data: dict of values for the payload. If None, interactive mode is triggered within build_payload.
    """
    start_time = time.time()

    try:
        # Build the payload string
        payload_str = build_payload(data=payload_data)

        # ===================== REQ 1 =====================
        URL_1 = "https://www.chronopost.fr/moncompte/displayCustomerArea.do?iv4Context=cb9ad1180a51ecc2e7cbf3e83c343581&lang=fr_FR"
        retry_get(URL_1, HEADERS_1)

        # ===================== REQ 2 =====================
        URL_2 = "https://www.chronopost.fr/expedier/accueilShipping.do?reinit=true&lang=fr_FR"
        HEADERS_2["Referer"] = URL_1
        retry_get(URL_2, HEADERS_2)

        token = 1768746808705

        # ===================== REQ 3 =====================
        if token:
            URL_3 = f"https://www.chronopost.fr/expeditionAvanceeSec/accueilShipping.do?_={token}&lang=fr_FR"
            retry_get(URL_3, HEADERS_4)

        # ===================== REQ 4 (CRITICAL) =====================
        if token:
            URL_4 = "https://www.chronopost.fr/expeditionAvanceeSec/jsonGeoRouting"
            HEADERS_6 = HEADERS_4.copy()
            HEADERS_6["Content-Type"] = "application/x-www-form-urlencoded"
            retry_post(URL_4, HEADERS_6, payload_str, stop_on_fail=True, check_false=True)

        # ===================== REQ 5 =====================
        final_response = None
        if token:
            URL_5 = "https://www.chronopost.fr/expeditionAvanceeSec/shippingZPL"
            final_response = retry_post(URL_5, HEADERS_6, payload_str)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if final_response and final_response.status_code == 200:
             return {
                 "status": "success", 
                 "duration": duration, 
                 "content": None
             }
        else:
            return {"status": "error", "message": "Final request failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


