import requests
import logging

from datetime import datetime

# =========================
# CONFIGURATION
# =========================

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def geocode_zip(zip_code):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "postalcode": zip_code,
        "country": "France",
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get("lat"), data[0].get("lon")
    except Exception as e:
        logger.error(f"Erreur géocodage Colissimo ({zip_code}): {str(e)}")
    return None, None
