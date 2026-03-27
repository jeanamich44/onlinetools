from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import logging
import json

from script.database import init_db, get_db, Payment, Admin
from script.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_admin,
    check_ip_whitelist
)

from script.mrz import generate_mrz, generate_random_data
from script.qr_zip import generate_qr_zip
from script.audio_analyse import perform_full_analysis, perform_full_analysis_stream, perform_retry_analysis_stream
import shutil
import os

# =========================
# SETUP
# =========================

app = FastAPI(title="Rheyy Services", version="2.0.0")
# Cache pour stocker les chemins temporaires
audio_files = {}

@app.post("/analyze-audio-stream")
async def analyze_audio_streaming_endpoint(request: Request, admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    file = form_data.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="Fichier manquant")
        
    file_id = str(int(time.time()))
    temp_path = f"temp_stream_{file_id}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    audio_files[file_id] = temp_path

    async def event_generator():
        # On lance le générateur d'analyse (Pass 1 & 2)
        for progress_json in perform_full_analysis_stream(temp_path):
            data = json.loads(progress_json)
            if data["status"] == "completed":
                data["file_id"] = file_id # On donne l'ID pour le retry/confirm
                yield json.dumps(data) + "\n"
            else:
                yield progress_json + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/analyze-audio-retry")
async def analyze_audio_retry_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    file_id = req.get("file_id")
    temp_path = audio_files.get(file_id)
    if not temp_path or not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé ou session expirée")

    async def event_generator():
        # On lance le générateur de retry (Pass 3 & 4)
        for progress_json in perform_retry_analysis_stream(temp_path):
            yield progress_json + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/analyze-audio-confirm")
async def analyze_audio_confirm_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    file_id = req.get("file_id")
    numbers = req.get("numbers", [])
    temp_path = audio_files.pop(file_id, None)
    
    if numbers:
        from script.audio_analyse import perform_ssh_transfer
        perform_ssh_transfer(numbers)
        
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
        
    return {"status": "success", "message": "Nombres envoyés au serveur distant via SSH."}


@app.post("/analyze-audio")
async def analyze_audio_endpoint(request: Request, admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    file = form_data.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="Fichier manquant")
        
    temp_path = f"temp_{int(time.time())}_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        results = perform_full_analysis(temp_path)
        return results
    except Exception as e:
        logger.error(f"Erreur d'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Base de données initialisée pour Rheyy Services.")

# =========================
# MODÈLES PYDANTIC
# =========================

class MRZRequest(BaseModel):
    mode: str = "random"
    nom: str | None = None
    prenom: str | None = None
    dep: str | None = None
    canton: str | None = None
    bureau: str | None = None
    date_delivrance: str | None = None
    random_code: str | None = None
    naissance: str | None = None
    sexe: str | None = None

class QRRequest(BaseModel):
    lines: list[str]

class LoginRequest(BaseModel):
    username: str
    password: str

# =========================
# ROUTES AUTHENTIFICATION
# =========================

@app.post("/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == req.username).first()
    if not admin or not verify_password(req.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    admin.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin/setup-first-admin")
async def setup_first_admin(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_ip_whitelist(request)
    
    try:
        existing = db.query(Admin).first()
        if existing:
            raise HTTPException(status_code=400, detail="Un administrateur existe déjà")
        
        hashed = get_password_hash(req.password)
        new_admin = Admin(
            username=req.username,
            hashed_password=hashed
        )
        db.add(new_admin)
        db.commit()
        return {"message": "Administrateur créé avec succès"}
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# ROUTES TOOLS (PROTÉGÉES)
# =========================

@app.post("/generate-mrz")
def generate_mrz_endpoint(req: MRZRequest, admin: str = Depends(get_current_admin)):
    if req.mode.lower() == "aleatoire" or req.mode.lower() == "random":
        data = generate_random_data()
        mrz = generate_mrz(data)
        return {"mrz": [f"{mrz['line1']}\n{mrz['line2']}"]}

    if req.mode.lower() == "manuel":
        data = {
            "nom": req.nom,
            "prenom": req.prenom,
            "dep": req.dep,
            "canton": req.canton,
            "bureau": req.bureau,
            "date_delivrance": req.date_delivrance,
            "random_code": req.random_code,
            "naissance": req.naissance,
            "sexe": req.sexe.upper() if req.sexe else "M",
        }
        mrz = generate_mrz(data)
        return {"mrz": [f"{mrz['line1']}\n{mrz['line2']}"]}

    raise HTTPException(status_code=400, detail="Mode invalide")

@app.post("/generate-zip")
def generate_zip_endpoint(req: QRRequest, admin: str = Depends(get_current_admin)):
    try:
        zip_path = generate_qr_zip(req.lines)
        return FileResponse(zip_path, media_type="application/zip", filename="qr_codes.zip")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =========================
# ROUTES DASHBOARD ADMIN
# =========================

@app.get("/admin/stats")
async def get_stats(admin: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_payments = db.query(Payment).count()
    paid_payments = db.query(Payment).filter(Payment.status == "PAID").count()
    total_revenue = db.query(Payment).filter(Payment.status == "PAID").with_entities(Payment.amount).all()
    revenue = sum([p[0] for p in total_revenue]) if total_revenue else 0
    

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    generated_today = db.query(Payment).filter(Payment.is_generated == 1, Payment.created_at >= today).count()

    return {
        "total_payments": total_payments,
        "paid_payments": paid_payments,
        "total_revenue": round(revenue, 2),
        "generated_today": generated_today
    }

@app.get("/admin/payments")
async def list_payments(
    skip: int = 0, 
    limit: int = 50, 
    admin: str = Depends(get_current_admin), 
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return payments

@app.get("/admin/verify-session")
async def verify_session(admin: str = Depends(get_current_admin)):
    return {"status": "ok", "admin": admin}
