import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import logging

from script.chronopost.chr import run_chronopost, get_relay_detail
from script.colissimo.colissimo import run_colissimo

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
    try:
        result = run_chronopost(req.data)
        return result
    except Exception as e:
        logger.error(f"Erreur Chronopost: {str(e)}")
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

# --- COLISSIMO ---

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
