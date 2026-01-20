import requests, time, os, json, base64
from .headers import HEADERS_1, HEADERS_2, HEADERS_4
from .payloads import build_payload

# ===================== PAYLOAD BUILD =====================
# Removed global PAYLOAD_TMP to avoid immediate execution

API_KEY = "a5fce98010bb9761a1d1a21af271d994"
SCRAPER_URL = "https://api.scraperapi.com/"
TIMEOUT = 60

# We need to maintain the session/token logic if it's dynamic, 
# but for now we follow the existing script structure where it seemed hardcoded or reused.
# The user said "payload de base qui change jamais".

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

def log(line):
    print(f"[LOG] {line}")

REQ_ID = 0

def retry_get(url, headers, stop_on_fail=False):
    global REQ_ID
    for attempt in range(2):
        REQ_ID += 1
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
        dt = time.time() - t0
        print(f"REQ {REQ_ID} -> {r.status_code} | {dt:.2f}s")
        log(f"REQ {REQ_ID}")
        log(f"STATUS : {r.status_code}")
        log(f"TIME   : {dt:.2f}s")
        log("-" * 80)
        if r.status_code == 200:
            return r
    if stop_on_fail:
        raise Exception("STOP: response != 200")
    return r

def retry_post(url, headers, data, stop_on_fail=False, check_false=False):
    global REQ_ID
    for attempt in range(2):
        REQ_ID += 1
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
        dt = time.time() - t0
        print(f"REQ {REQ_ID} -> {r.status_code} | {dt:.2f}s")
        log(f"REQ {REQ_ID}")
        log(f"STATUS : {r.status_code}")
        log(f"TIME   : {dt:.2f}s")
        # log(f"RESPONSE : {r.text}") # Too verbose?
        log("-" * 80)
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
    global REQ_ID
    REQ_ID = 0 # Reset for new run
    
    start_time = time.time()
    
    log("=" * 80)
    log(f"START | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 80)

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
        log(f"END | duration={duration:.2f}s")
        log("=" * 80)
        
        if final_response and final_response.status_code == 200:

             return {
                 "status": "success", 
                 "duration": duration, 
                 "content": None,
                 "headers": dict(final_response.headers)
             }
        else:
            return {"status": "error", "message": "Final request failed"}

    except Exception as e:
        log(f"ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Interactive mode (original behavior)
    run_chronopost(None)


