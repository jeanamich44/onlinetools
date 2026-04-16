from curl_cffi import requests
import json
import re
import time

# ==============================================================================

HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "fr-FR,fr;q=0.9",
    "priority": "u=1, i",
    "referer": "https://www.chronopost.fr/fr",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

HIT_KEYS = {
    "Colis en cours de préparation chez l&#x27;expéditeur": "Prêt",
    "Pris en charge par Chronopost": "Pris en charge",
    "En cours d&#x27;acheminement": "Acheminement",
    "Envoi en cours de livraison": "Livraison",
    "Livré": "Livré"
}

FAIL_KEYS = [
    "Merci de vérifier cette référence sur votre étiquette de transport",
    "Nous n'avons pas d'information à propos de ce numéro de suivi"
]

# ==============================================================================

def dissect_tracking(tracking_number):
    pattern = r'^([A-Z]{2})(\d+)([A-Z]{2})$'
    num_clean = str(tracking_number).upper().replace(" ", "")
    match = re.match(pattern, num_clean)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

def generate_sequence(prefix, digits, suffix, start_from, amount):
    digits_len = len(digits)
    try:
        start_val = int(start_from)
    except ValueError:
        return []
    
    results = []
    for i in range(amount):
        current_val = start_val + i
        formatted_digits = str(current_val).zfill(digits_len)
        results.append(f"{prefix}{formatted_digits}{suffix}")
    return results

# ==============================================================================

def extract_details(html):
    details = {"status_text": "Inconnu", "date": "N/C", "location": "N/C"}
    
    try:
        clean_html = re.sub(r'\s+', ' ', html)
        
        for key, labels in HIT_KEYS.items():
            if key in html:
                details["status_text"] = labels
                break
        
        status_match = re.search(r'<div class="step-label">([^<]+)</div>', html)
        if status_match:
            details["status_text"] = status_match.group(1).strip()
            
        date_match = re.search(r'<div class="step-date">([^<]+)</div>', html)
        if date_match:
            details["date"] = date_match.group(1).strip()
            
        loc_match = re.search(r'<div class="step-location">([^<]+)</div>', html)
        if loc_match:
            details["location"] = loc_match.group(1).strip()
            
    except:
        pass
        
    return details

# ==============================================================================

def check_chronopost_stream(targets, mode="check", keyword=None):
    total = len(targets)
    stats = {"HIT": 0, "FAILED": 0, "UNKNOWN": 0, "ERROR": 0}
    
    yield json.dumps({
        "status": "info", 
        "message": f"Analyse : {total} numéros"
    }) + "\n"
    
    for i, num in enumerate(targets, 1):
        try:
            r = requests.get(
                "https://www.chronopost.fr/tracking-no-cms/suivi-colis",
                params={"listeNumerosLT": num, "langue": "fr", "_": str(int(time.time()*1000))},
                headers=HEADERS,
                impersonate="chrome120",
                timeout=20,
                verify=False
            )
            html = r.text
            
            result_data = {"number": num, "status": "FAILED", "details": None}
            
            if mode == "search" and keyword:
                if keyword.lower() in html.lower():
                    result_data["status"] = "HIT"
            else:
                if any(key in html for key in HIT_KEYS):
                    result_data["status"] = "HIT"
                    result_data["details"] = extract_details(html)
                elif any(key in html for key in FAIL_KEYS):
                    result_data["status"] = "FAILED"
            
            stats[result_data["status"]] += 1
            
            yield json.dumps({
                "status": "result",
                "index": i,
                "total": total,
                "number": num,
                "result_status": result_data["status"],
                "details": result_data["details"],
                "stats": stats
            }) + "\n"
            
            if i % 10 == 0:
                time.sleep(1)
                
        except Exception as e:
            stats["ERROR"] += 1
            yield json.dumps({
                "status": "error",
                "index": i,
                "total": total,
                "number": num,
                "message": str(e),
                "stats": stats
            }) + "\n"

    yield json.dumps({
        "status": "completed", 
        "message": "Terminé",
        "stats": stats
    }) + "\n"

