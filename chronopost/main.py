from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Ensure script directory (for local imports within module) and parent (if needed) are in path
# Although if we run from chronopost/ directory, relative imports might work or need tweak 
# based on how it's launched. Assuming standard "uvicorn main:app" within chronopost file.
# The `script` folder is valid python package if it has __init__.py or just directory import.
# Using direct import since it's a sibling/child.

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

@app.post("/generate-chronopost")
def generate_chronopost_endpoint(req: ChronopostRequest):
    try:
        result = run_chronopost(req.data)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
