from curl_cffi import requests
import json
import re
import time

# ==============================================================================
# Chronopost Checker Service
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

HIT_KEYS = [
    "Colis en cours de préparation chez l&#x27;expéditeur",
    "Pris en charge par Chronopost",
    "En cours d&#x27;acheminement",
    "Envoi en cours de livraison",
    "Livré"
]

FAIL_KEYS = [
    "Merci de vérifier cette référence sur votre étiquette de transport",
    "Nous n'avons pas d'information à propos de ce numéro de suivi"
]

# ==============================================================================
# HELPERS
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
# CORE SERVICE
# ==============================================================================

def check_chronopost_stream(targets, mode="check", keyword=None):
    total = len(targets)
    stats = {"HIT": 0, "FAILED": 0, "UNKNOWN": 0, "ERROR": 0}
    
    yield json.dumps({
        "status": "info", 
        "message": f"Démarrage de l'analyse : {total} numéros (Mode: {mode})"
    }) + "\n"
    
    for i, num in enumerate(targets, 1):
        try:
            # On utilise curl_cffi avec impersonate chrome120 comme demandé
            r = requests.get(
                "https://www.chronopost.fr/tracking-no-cms/suivi-colis",
                params={"listeNumerosLT": num, "langue": "fr", "_": str(int(time.time()*1000))},
                headers=HEADERS,
                impersonate="chrome120",
                timeout=15,
                verify=False # Évite les erreurs SSL sur certains environnements
            )
            html = r.text
            
            status = "UNKNOWN"
            if mode == "search" and keyword:
                status = "HIT" if keyword.lower() in html.lower() else "FAILED"
            else:
                if any(key in html for key in HIT_KEYS):
                    status = "HIT"
                elif any(key in html for key in FAIL_KEYS):
                    status = "FAILED"
            
            if status in stats:
                stats[status] += 1
            else:
                stats["UNKNOWN"] += 1
            
            yield json.dumps({
                "status": "result",
                "index": i,
                "total": total,
                "number": num,
                "result_status": status,
                "stats": stats
            }) + "\n"
            
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
        "message": "Analyse terminée.",
        "stats": stats
    }) + "\n"
