import os
import sys
import json
import requests
import subprocess
import time

# Chemins relatifs à rheyy-services
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
        return None
    return None

def refresh_token():
    print("[PY-FLUNCH] Lancement de la régénération du token (Playwright)...")
    try:
        # On lance node pour l'automate
        subprocess.run(["node", ORCHESTRATOR], check=True, cwd=FLUNCH_DIR)
        return get_cached_token()
    except Exception as e:
        print(f"[PY-FLUNCH] ERREUR AUTOMATE: {str(e)}")
        return None

def fetch_flunch_data(client_id):
    token = get_cached_token()
    
    # 1. On tente avec le token en cache
    if token:
        data, status = call_api(client_id, token)
        if status == 200:
            return data
        
        # 2. Si 401 ou erreur liée au token, on refresh
        if status == 401 or "UNAUTHORIZED" in str(data):
            token = refresh_token()
    else:
        token = refresh_token()

    # 3. Dernier essai avec le nouveau token (ou premier si pas de cache)
    if token:
        data, status = call_api(client_id, token)
        return data
    
    return {"status": "error", "message": "Impossible de récupérer un token valide"}

def call_api(client_id, token):
    url = f"https://www.flunch.fr/fidelite/api/v3/fid/{client_id}/me"
    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(fetch_flunch_data(sys.argv[1])))
