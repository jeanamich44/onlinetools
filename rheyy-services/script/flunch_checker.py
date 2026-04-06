import requests
import json
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLUNCH_DIR = os.path.join(BASE_DIR, "script", "flunch")
TOKEN_FILE = os.path.join(FLUNCH_DIR, "output", "bearer_token.txt")
ORCHESTRATOR = os.path.join(FLUNCH_DIR, "main.js")

def get_cached_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()
    except:
        pass
    return None

def parse_profile_data(data):
    if not data or "id" not in data:
        return data
    
    parsed = {}
    
    # ROOT LEVEL
    if "id" in data: parsed["ID"] = str(data["id"])
    if "mainIdentifier" in data: parsed["CARTE"] = data["mainIdentifier"]
    if "mainPointsBalance" in data: parsed["SOLDE"] = str(data["mainPointsBalance"])
    if "enrolmentDate" in data: parsed["START"] = data["enrolmentDate"]
    if "lastName" in data: parsed["NOM"] = data["lastName"]
    if "firstName" in data: parsed["PRENOM"] = data["firstName"]
    if "birthDate" in data: parsed["DDN"] = data["birthDate"]
    
    # ADDRESS LEVEL
    addr = data.get("address", {})
    if addr.get("email"): parsed["MAIL"] = addr["email"]
    if addr.get("phone"): parsed["TEL"] = addr["phone"]
    if addr.get("mobile"): parsed["TEL2"] = addr["mobile"]
    if addr.get("postalCode"): parsed["CP"] = addr["postalCode"]
    if addr.get("city"): parsed["VILLE"] = addr["city"]
    if addr.get("street"): parsed["ADRESSE"] = addr["street"]
    
    # ATTRIBUTES LEVEL
    attrs = data.get("attributes", [])
    for attr in attrs:
        code = attr.get("code")
        val = attr.get("value")
        if not val or val == "": continue
        
        if code == "LAST_TRN_NOM_RESTO" or code == "NOM_RESTO":
            parsed["LIEU"] = val
        if code == "ACCOUNT_TYPE":
            parsed["TYPE"] = val
            
    return parsed

def fetch_flunch_data(client_id):
    token = get_cached_token()
    
    if not token:
        subprocess.run(["node", "main.js", str(client_id)], cwd=FLUNCH_DIR, check=True)
        token = get_cached_token()
    
    if not token:
        return {"id": client_id, "status": "error", "message": "Impossible de récupérer le token"}
        
    raw_data, status = call_api(client_id, token)
    
    if status == 200 and isinstance(raw_data, dict) and "id" in raw_data:
        return parse_profile_data(raw_data)
        
    return raw_data

def call_api(client_id, token):
    url = f"https://www.flunch.fr/fidelite/api/v3/fid/{client_id}/me"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://www.flunch.fr",
        "priority": "u=1, i",
        "referer": "https://www.flunch.fr/fidelite/mon-profil",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json(), 200
        return {"status": "error", "message": f"Erreur API: {resp.status_code}"}, resp.status_code
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(fetch_flunch_data(sys.argv[1]), ensure_ascii=False))
