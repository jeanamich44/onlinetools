import requests, time, os
from headers import HEADERS_1, HEADERS_2, HEADERS_4
from payloads import build_payload

# ===================== PAYLOAD BUILD =====================
PAYLOAD_TMP = build_payload()

start_time = time.time()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

def log(line):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

API_KEY = "a5fce98010bb9761a1d1a21af271d994"
SCRAPER_URL = "https://api.scraperapi.com/"
TIMEOUT = 60

token = None
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
        raise SystemExit("STOP: response != 200")
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
        log(f"RESPONSE : {r.text}")
        log("-" * 80)
        if r.status_code == 200 and (not check_false or "false" not in r.text.lower()):
            return r
    if stop_on_fail:
        raise SystemExit("STOP: jsonGeoRouting failed")
    return r

log("=" * 80)
log(f"START | {time.strftime('%Y-%m-%d %H:%M:%S')}")
log("=" * 80)

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
    retry_post(URL_4, HEADERS_6, PAYLOAD_TMP, stop_on_fail=True, check_false=True)

# ===================== REQ 5 =====================
if token:
    URL_5 = "https://www.chronopost.fr/expeditionAvanceeSec/shippingZPL"
    retry_post(URL_5, HEADERS_6, PAYLOAD_TMP)

end_time = time.time()
duration = end_time - start_time

log(f"END | duration={duration:.2f}s")
log("=" * 80)
print(f"Temps total : {duration:.2f}s")
