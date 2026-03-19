import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import uvicorn
import logging

from script.chronopost.chr import run_chronopost, get_relay_detail
from script.chronopost.price_calc import get_chronopost_price
from script.chronopost.relay_search import search_relays_chronopost
from script.colissimo.colissimo import run_colissimo, search_relays_colissimo
from script.colissimo.price_calc_colissimo import get_colissimo_price

# ==============================================================================
# CONFIGURATION ET INITIALISATION
# ==============================================================================
app = FastAPI()

COLISSIMO_CONFIG = {
    "id": "825834",
    "key": "94ED799A18A2C685733CADF74DDDBA7B"
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# SECTION CHRONOPOST
# ==============================================================================

class ChronopostRequest(BaseModel):
    data: dict

class ChronopostSimulateRequest(BaseModel):
    sender_iso: str = "FR"
    sender_zip: str
    sender_city: str
    recipient_iso: str = "FR"
    recipient_zip: str
    recipient_city: str
    weight: float
    length: float = 0
    width: float = 0
    height: float = 0

@app.post("/generate/chronopost")
def generate_chronopost_endpoint(req: ChronopostRequest):
    try:
        result = run_chronopost(req.data)
        return result
    except Exception as e:
        logger.error(f"Erreur Chronopost: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

@app.post("/api/chronopost/simulate")
def simulate_chronopost_endpoint(req: ChronopostSimulateRequest):
    try:
        return get_chronopost_price(req.dict())
    except Exception as e:
        logger.error(f"Erreur Simulation Chronopost: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

class RelayRequest(BaseModel):
    pickup_id: str
    country: str = None

@app.post("/relay/info")
def get_relay_info_endpoint(req: RelayRequest):
    try:
        result = get_relay_detail(req.pickup_id, req.country)
        return result
    except Exception as e:
        logger.error(f"Erreur Relay: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

# ==============================================================================
# SECTION COLISSIMO
# ==============================================================================

class ColissimoSimulateRequest(BaseModel):
    weight: float
    sender_iso: str = "FR"
    recipient_iso: str = "FR"
    product_code: str = "DOM"
    shipping_date: str = None
    shipping_mode: str = "L_BAL"
    package_format: str = "F_STD"

@app.post("/api/colissimo/simulate")
def simulate_colissimo_endpoint(req: ColissimoSimulateRequest):
    try:
        return get_colissimo_price(req.dict(), COLISSIMO_CONFIG)
    except Exception as e:
        logger.error(f"Erreur Simulation Colissimo: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

class ColissimoRequest(BaseModel):
    data: dict

@app.post("/generate/colissimo")
def generate_colissimo_endpoint(req: ColissimoRequest):
    try:
        result = run_colissimo(req.data, COLISSIMO_CONFIG)
        return result
    except Exception as e:
        logger.error(f"Erreur Colissimo: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

# ==============================================================================
# RECHERCHE DE POINTS RELAIS
# ==============================================================================

@app.get("/relay/search")
def search_relays_endpoint(
    zip: str, 
    type: str = "colissimo", 
    lat: float = None, 
    lon: float = None, 
    country: str = "FR"
):
    try:
        if type == "colissimo":
            result = search_relays_colissimo(zip, COLISSIMO_CONFIG)
            return result
        elif type == "chronopost":
            result = search_relays_chronopost(lat, lon, zip, country)
            return result
        else:
            return {"status": "error", "message": "Type inconnu"}
    except Exception as e:
        logger.error(f"Erreur recherche relais: {str(e)}")
        raise HTTPException(status_code=500, detail="error")
# ==============================================================================
# LANCEMENT DE L'APPLICATION
# ==============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
