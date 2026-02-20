import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import logging

from script.chr import run_chronopost, get_relay_detail

app = FastAPI()

# Configuration du logging
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChronopostRequest(BaseModel):
    data: dict

@app.post("/generate-chronopost/generate-chronopost")
def generate_chronopost_endpoint(req: ChronopostRequest):
    try:
        result = run_chronopost(req.data)
        # Nous retournons le résultat même en cas d'erreur pour le debug frontend
        return result
    except Exception as e:
        logger.error(f"Erreur endpoint Chronopost: {str(e)}")
        raise HTTPException(status_code=500, detail="error")

class RelayRequest(BaseModel):
    pickup_id: str
    country: str = None

@app.post("/generate-chronopost/get-relay-info")
def get_relay_info_endpoint(req: RelayRequest):
    try:
        result = get_relay_detail(req.pickup_id, req.country)
        return result
    except Exception as e:
        logger.error(f"Erreur endpoint Relay: {str(e)}")
        raise HTTPException(status_code=500, detail="error")
