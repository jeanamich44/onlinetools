from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import logging

# Imports locaux
from database import init_db, get_db, Payment, Admin
from security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_admin,
    check_ip_whitelist
)
from script.mrz import generate_mrz, generate_random_data
from script.qr_zip import generate_qr_zip

# =========================
# SETUP
# =========================

app = FastAPI(title="Rheyy Services", version="2.0.0")

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
    
    # Mise à jour de la dernière connexion
    admin.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin/setup-first-admin")
async def setup_first_admin(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Route temporaire pour créer le premier admin (protégée par IP)."""
    check_ip_whitelist(request)
    
    existing = db.query(Admin).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un administrateur existe déjà")
    
    new_admin = Admin(
        username=req.username,
        hashed_password=get_password_hash(req.password)
    )
    db.add(new_admin)
    db.commit()
    return {"message": "Administrateur créé avec succès"}

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
    """Statistiques globales pour le dashboard."""
    total_payments = db.query(Payment).count()
    paid_payments = db.query(Payment).filter(Payment.status == "PAID").count()
    total_revenue = db.query(Payment).filter(Payment.status == "PAID").with_entities(Payment.amount).all()
    revenue = sum([p[0] for p in total_revenue]) if total_revenue else 0
    
    # PDF générés aujourd'hui
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
    """Liste les derniers paiements."""
    payments = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return payments

@app.get("/admin/verify-session")
async def verify_session(admin: str = Depends(get_current_admin)):
    """Vérifie si le token est toujours valide."""
    return {"status": "ok", "admin": admin}
