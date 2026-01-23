from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os



from script.chr import run_chronopost

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
