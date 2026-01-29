import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

from script.chr import run_chronopost, get_relay_detail

app = FastAPI()

# Simple in-memory rate limiting dict: {ip: [timestamp1, timestamp2, ...]}
RELAY_LIMITS = {}

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
        raise HTTPException(status_code=500, detail=str(e))

class RelayRequest(BaseModel):
    pickup_id: str
    country: str = None

@app.post("/generate-chronopost/get-relay-info")
def get_relay_info_endpoint(req: RelayRequest, request: Request):
    try:
        # Rate Limiting Logic
        client_ip = request.client.host
        now = time.time()
        
        # Initialize if not exists
        if client_ip not in RELAY_LIMITS:
            RELAY_LIMITS[client_ip] = []
        
        # Filter timestamps older than 60 seconds
        RELAY_LIMITS[client_ip] = [t for t in RELAY_LIMITS[client_ip] if now - t < 60]
        
        # Check limit
        if len(RELAY_LIMITS[client_ip]) >= 5:
            # Return error status directly as frontend expects JSON with status
            return {"status": "error", "message": "Trop de requêtes. Veuillez patienter 1 minute."}
        
        # Add current request
        RELAY_LIMITS[client_ip].append(now)

        result = get_relay_detail(req.pickup_id, req.country)
        if result["status"] == "error":
             # We return as 200 with error data or 400? User asked for simplicity.
             # Let's return the dict.
             pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
