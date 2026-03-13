import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import logging

from script.chronopost.chr import run_chronopost, get_relay_detail
from script.chronopost.price_calc import get_chronopost_price
from script.colissimo.colissimo import run_colissimo, search_relays_colissimo

app = FastAPI()

# Configuration Colissimo
COLISSIMO_CONFIG = {
    "id": "825834",
    "key": "94ED799A18A2C685733CADF74DDDBA7B"
}

# Configuration du logging
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

# --- CHRONOPOST ---

class ChronopostRequest(BaseModel):
    data: dict

@app.post("/generate/chronopost")
def generate_chronopost_endpoint(req: ChronopostRequest):
    """Génération de l'étiquette Chronopost"""
    try:
        result = run_chronopost(req.data)
        return result
    except Exception as e:
        logger.error(f"Erreur Chronopost: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

@app.post("/api/chronopost/simulate")
def simulate_chronopost_endpoint(data: dict):
    """Simulation des tarifs Chronopost avec réduction"""
    try:
        return get_chronopost_price(data)
    except Exception as e:
        logger.error(f"Erreur Simulation Chronopost: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

class RelayRequest(BaseModel):
    pickup_id: str
    country: str = None

@app.post("/relay/info")
def get_relay_info_endpoint(req: RelayRequest):
    """Récupération des détails d'un point relais Chronopost"""
    try:
        result = get_relay_detail(req.pickup_id, req.country)
        return result
    except Exception as e:
        logger.error(f"Erreur Relay: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

# --- COLISSIMO ---

class ColissimoRequest(BaseModel):
    data: dict

@app.post("/generate/colissimo")
def generate_colissimo_endpoint(req: ColissimoRequest):
    """Génération de l'étiquette Colissimo"""
    try:
        result = run_colissimo(req.data, COLISSIMO_CONFIG)
        return result
    except Exception as e:
        logger.error(f"Erreur Colissimo: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

# --- RECHERCHE RELAIS ---

@app.get("/relay/search")
def search_relays_endpoint(zip: str, type: str = "colissimo"):
    """Recherche de points relais par code postal"""
    try:
        if type == "colissimo":
            result = search_relays_colissimo(zip, COLISSIMO_CONFIG)
            return result
        else:
            return {"status": "error", "message": f"Type de recherche non supporté: {type}"}
    except Exception as e:
        logger.error(f"Erreur recherche relais: {str(e)}")
        raise HTTPException(status_code=500, detail="error")
