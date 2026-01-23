from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os



from script.chr import run_chronopost, get_relay_detail

app = FastAPI()

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

@app.post("/generate-chronopost/get-relay-info")
def get_relay_info_endpoint(req: RelayRequest):
    try:
        result = get_relay_detail(req.pickup_id)
        if result["status"] == "error":
             # We return as 200 with error data or 400? User asked for simplicity.
             # Let's return the dict.
             pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
