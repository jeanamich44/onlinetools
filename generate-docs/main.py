# =========================
# IMPORTS
# =========================

import os
import uuid
import asyncio
import logging
import requests
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Database & Payment
from payments.database import init_db, get_db, Payment, SessionLocal
from payments.payment import create_checkout, get_access_token
from payments.polling import poll_sumup_status
from payments.reconcile import start_reconciliation_loop
import aiohttp

# Scripts (PDF Generation)
from script.lbp import generate_lbp_pdf, generate_lbp_preview
from script.sg import generate_sg_pdf, generate_sg_preview
from script.bfb import generate_bfb_pdf, generate_bfb_preview
from script.revolut import generate_revolut_pdf, generate_revolut_preview
from script.ca import generate_ca_pdf, generate_ca_preview
from script.cm import generate_cm_pdf, generate_cm_preview
from script.cic import generate_cic_pdf, generate_cic_preview
from script.qonto import generate_qonto_pdf, generate_qonto_preview
from script.maxance import generate_maxance_pdf, generate_maxance_preview


# =========================
# CONFIGURATION
# =========================

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# BASE DE DONNÉES & SETUP APP
# =========================

# Initialisation des tables
app = FastAPI()

# =========================
# TÂCHES DE FOND (RECONCILIATION)
# =========================

@app.on_event("startup")
async def startup_event():
    """Au démarrage du serveur."""
    # Lancer la boucle de réconciliation asynchrone (non-bloquante)
    asyncio.create_task(start_reconciliation_loop(interval=900))
    logger.info("Serveur démarré - Tâche de réconciliation ASYNC lancée (Toutes les 15 min).")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API Generate-Docs is running"}

# Initialisation des tables
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# =========================
# MODÈLES PYDANTIC
# =========================

class PDFRequest(BaseModel):
    type_pdf: str  # "lbp" | "sg" | "bfb" | "revolut" | "credit_agricole" | "cm" | "cic" | "qonto" | "maxance"
    preview: Optional[bool] = False

    sexe: Optional[str] = "m"

    # Champs communs
    nom_prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp_ville: Optional[str] = None
    telephone: Optional[str] = None

    # Champs détaillés
    cp: Optional[str] = None
    ville: Optional[str] = None
    depart: Optional[str] = None

    banque: Optional[str] = None
    guichet: Optional[str] = None
    compte: Optional[str] = None
    cle: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None

    domiciliation: Optional[str] = None

    agence: Optional[str] = None
    agence_adresse: Optional[str] = None
    agence_cp_ville: Optional[str] = None
    bank: Optional[str] = None

    nclient: Optional[str] = None
    ncontrat: Optional[str] = None
    norias: Optional[str] = None
    plaque: Optional[str] = None
    typevehicule: Optional[str] = None
    checkout_ref: Optional[str] = None # Added for paid PDF generation


# =========================
# ROUTES DE PAIEMENT
# =========================

@app.post("/create-payment")
async def create_payment_endpoint(request: Request, data: PDFRequest, background_tasks: BackgroundTasks, product_name: str = "default", db: Session = Depends(get_db)):
    """
    Crée une nouvelle session de paiement.
    """
    try:
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        logger.info(f"Création paiement (Async) pour Produit: {product_name}, IP: {client_ip}")

        # Convertir data en JSON pour le stocker
        import json
        user_data_str = json.dumps(data.dict())

        # create_checkout retourne maintenant (url, ref, id)
        url, ref, checkout_id = await create_checkout(db=db, amount=1.0, ip_address=client_ip, product_name=product_name, user_data=user_data_str)
        
        # Démarrer le polling immédiatement en arrière-plan
        if checkout_id:
             background_tasks.add_task(poll_sumup_status, checkout_id)
        
        return {"payment_url": url, "checkout_ref": ref}
    except Exception as e:
        logger.error(f"Erreur création paiement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment-success")
def payment_success(checkout_reference: Optional[str] = None):
    """
    Redirige vers la page produit spécifique au lieu de l'accueil.
    """
    if not checkout_reference:
        return RedirectResponse(url="https://jeanamich44.github.io/onlinetools/index.html")

    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        if payment and payment.product_name:
            # Mapping Simple: rib-lbp -> lbp.html
            product = payment.product_name
            if product.startswith("rib-"):
                page = product.replace("rib-", "") + ".html"
                logger.info(f"Redirection vers produit: {page} pour ref {checkout_reference}")
                return RedirectResponse(url=f"https://jeanamich44.github.io/onlinetools/docs/rib/{page}?checkout_ref={checkout_reference}")
        
        # Fallback accueil si produit inconnu
        logger.warning(f"Produit inconnu pour {checkout_reference}, fallback accueil.")
        return RedirectResponse(url=f"https://jeanamich44.github.io/onlinetools/index.html?checkout_ref={checkout_reference}")
    finally:
        db.close()

@app.post("/generate-pdf")
@app.post("/generate-pdf/")
def generate_pdf(request: Request, data: PDFRequest):
    """
    Génère un PDF. Gère la preview libre et le PDF final payé.
    """
    output_path = f"/tmp/{uuid.uuid4()}.pdf"
    db = SessionLocal()

    try:
        # 1. Vérification du paiement si ce n'est pas une preview
        if not data.preview:
            if not data.checkout_ref:
                raise HTTPException(status_code=402, detail="Paiement requis pour le PDF final")
            
            # Vérifier en base si le paiement est PAID
            payment = db.query(Payment).filter(Payment.checkout_ref == data.checkout_ref).first()
            if not payment or payment.status != "PAID":
                logger.warning(f"Tentative téléchargement PDF sans paiement valide: {data.checkout_ref}")
                raise HTTPException(status_code=402, detail="Paiement non confirmé")
            
            # 1.3 Sécurité : Vérifier si déjà généré (Anti-Fraude)
            if payment.is_generated:
                client_ip = request.headers.get("x-forwarded-for", request.client.host)
                now = datetime.utcnow().isoformat()
                logger.warning(
                    f"\n🚨 [SUSPICION DE FRAUDE] "
                    f"\n- IP: {client_ip} "
                    f"\n- REF: {data.checkout_ref} "
                    f"\n- DATE: {now} "
                    f"\n- TENTATIVE DATA: {data.dict()}"
                    f"\n- ORIGINALE DATA: {payment.user_data}\n"
                )
                # On ne renvoie RIEN d'explicite (403 Forbidden est le plus discret)
                return Response(status_code=403)

            # Si on a un checkout_ref, on utilise les données sauvegardées en base au moment du paiement
            # pour éviter que l'utilisateur ne change les infos après avoir payé.
            if payment.user_data:
                import json
                saved_data = json.loads(payment.user_data)
                # Fusionner/Ecraser avec les données de la base
                for key, value in saved_data.items():
                    setattr(data, key, value)
                
                # Marquer comme généré immédiatement (Lock)
                payment.is_generated = 1
                db.commit()
                logger.info(f"Génération PDF final pour {data.checkout_ref} (Lock activé)")

        # 2. Génération selon le type
        if data.type_pdf == "lbp":
            if data.preview:
                generate_lbp_preview(data, output_path)
            else:
                generate_lbp_pdf(data, output_path)
        
        # ... (les autres types restent identiques, ils utilisent 'data')
        elif data.type_pdf == "sg":
            if data.preview: generate_sg_preview(data, output_path)
            else: generate_sg_pdf(data, output_path)
        elif data.type_pdf == "bfb":
            if data.preview: generate_bfb_preview(data, output_path)
            else: generate_bfb_pdf(data, output_path)
        elif data.type_pdf == "revolut":
            if data.preview: generate_revolut_preview(data, output_path)
            else: generate_revolut_pdf(data, output_path)
        elif data.type_pdf == "ca":
            if data.preview: generate_ca_preview(data, output_path)
            else: generate_ca_pdf(data, output_path)
        elif data.type_pdf == "cm":
            if data.preview: generate_cm_preview(data, output_path)
            else: generate_cm_pdf(data, output_path)
        elif data.type_pdf == "cic":
            if data.preview: generate_cic_preview(data, output_path)
            else: generate_cic_pdf(data, output_path)
        elif data.type_pdf == "qonto":
            if data.preview: generate_qonto_preview(data, output_path)
            else: generate_qonto_pdf(data, output_path)
        elif data.type_pdf == "maxance":
            if data.preview: generate_maxance_preview(data, output_path)
            else: generate_maxance_pdf(data, output_path)
        else:
            raise HTTPException(status_code=400, detail="type_pdf invalide")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="PDF non généré")

        filename = "preview.pdf" if data.preview else "rib.pdf"
        return FileResponse(output_path, media_type="application/pdf", filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur generate_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
