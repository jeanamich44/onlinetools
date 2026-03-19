from curl_cffi import requests
import json
import time
import logging

logger = logging.getLogger(__name__)

def search_relays_chronopost(lat, lon, zipcode, country="FR", radius="100"):
    """
    Recherche des points relais Chronopost via l'API stubpointsearch.json
    """
    url = "https://www.chronopost.fr/expeditionAvanceeSec/stubpointsearch.json"
    
    params = {
        "lat": str(lat) if lat else "0",
        "lon": str(lon) if lon else "0",
        "r": str(radius),
        "z": str(zipcode),
        "c": "",
        "a": "",
        "p": country,
        "lang": "fr_FR",
        "_": int(time.time() * 1000)
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.chronopost.fr/expeditionAvanceeSec/ounoustrouver.html"
    }

    try:
        r = requests.get(
            url,
            params=params,
            headers=headers,
            impersonate="chrome120",
            timeout=20
        )
        
        if r.status_code != 200:
            logger.error(f"Chronopost Relay API error: {r.status_code}")
            return {"status": "error", "message": f"API Error {r.status_code}"}
            
        data = r.json()
        points = data.get("olgiPointList", [])
        
        relays = []
        for p in points:
            # Extraction propre des données pour le frontend
            relays.append({
                "id": p.get("identifier"),
                "name": p.get("name"),
                "address": p.get("address"),
                "zip": p.get("zipcode"),
                "city": p.get("city"),
                "lat": float(p.get("latitude")) if p.get("latitude") else 0,
                "lng": float(p.get("longitude")) if p.get("longitude") else 0,
                "distance": p.get("distanceValue", 0) / 1000 if "distanceValue" in p else 0, # Distance en km ?
                "type": p.get("type")
            })
            
        return {
            "status": "success",
            "relays": relays
        }
        
    except Exception as e:
        logger.error(f"Error searching Chronopost relays: {str(e)}")
        return {"status": "error", "message": str(e)}
