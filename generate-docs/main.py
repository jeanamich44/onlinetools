# =========================
# IMPORTS
# =========================

import os
import uuid
import asyncio
import logging
import requests
import aiohttp
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, parse_obj_as
from sqlalchemy.orm import Session

# Base de données & Paiement
from payments.database import init_db, get_db, Payment, SessionLocal
from payments.payment import create_checkout, get_access_token
from securite.payment_guard import is_payment_allowed_fast, security_worker, increment_payment_counter
# from payments.polling import poll_sumup_status
# from payments.reconcile import start_reconciliation_loop

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
from script.nike import generate_nike_pdf, generate_nike_preview

# Mapping des generateurs
GENERATORS = {
    "lbp": generate_lbp_pdf,
    "sg": generate_sg_pdf,
    "bfb": generate_bfb_pdf,
    "revolut": generate_revolut_pdf,
    "ca": generate_ca_pdf,
    "cm": generate_cm_pdf,
    "cic": generate_cic_pdf,
    "qonto": generate_qonto_pdf,
    "maxance": generate_maxance_pdf,
    "nike": generate_nike_pdf
}

# Mapping des previews
PREVIEWS = {
    "lbp": generate_lbp_preview,
    "sg": generate_sg_preview,
    "bfb": generate_bfb_preview,
    "revolut": generate_revolut_preview,
    "ca": generate_ca_preview,
    "cm": generate_cm_preview,
    "cic": generate_cic_preview,
    "qonto": generate_qonto_preview,
    "maxance": generate_maxance_preview,
    "nike": generate_nike_preview
}

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
    from payments.reconcile import start_reconciliation_loop
    # Lancer les tâches de fond en parallèle pour ne pas entraver le processus de base
    asyncio.create_task(start_reconciliation_loop(interval=900))
    asyncio.create_task(security_worker())
    logger.info("Serveur démarré - Tâches de fond (Réconciliation & Sécurité) lancées.")

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
    
    # Champs Nike
    nfacture: Optional[str] = None
    ncommande: Optional[str] = None
    date: Optional[str] = None
    prixbb: Optional[str] = None
    tva: Optional[str] = None
    prixx: Optional[str] = None
    moyenpaiement: Optional[str] = None
    idproduit1: Optional[str] = None
    desc1: Optional[str] = None
    desc1suite: Optional[str] = None
    quan1: Optional[str] = None
    prixbrut1: Optional[str] = None
    prixnet1: Optional[str] = None
    prixtotal1: Optional[str] = None
    idproduit2: Optional[str] = None
    desc2: Optional[str] = None
    desc2suite: Optional[str] = None
    quan2: Optional[str] = None
    prixbrut2: Optional[str] = None
    prixnet2: Optional[str] = None
    prixtotal2: Optional[str] = None
    
    checkout_ref: Optional[str] = None
    sendToThirdPersonInfo: Optional[str] = None

    # --- Champs Chronopost (Ajoutés pour l'automatisation) ---
    valeurproduct: Optional[str] = None
    
    # Expéditeur
    senderType: Optional[str] = None
    senderCompanyName: Optional[str] = None
    senderLastname: Optional[str] = None
    senderFirstname: Optional[str] = None
    senderCP: Optional[str] = None
    senderHandphone: Optional[str] = None
    senderCity: Optional[str] = None
    senderEmail: Optional[str] = None
    senderAddress: Optional[str] = None
    senderAddress2: Optional[str] = None
    senderRef: Optional[str] = None
    senderCountry: Optional[str] = None

    # Destinataire
    receiverType: Optional[str] = None
    receiverCompanyName: Optional[str] = None
    receiverLastname: Optional[str] = None
    receiverFirstname: Optional[str] = None
    receiverCP: Optional[str] = None
    receiverCity: Optional[str] = None
    receiverHandphone: Optional[str] = None
    receiverAddress: Optional[str] = None
    receiverEmail: Optional[str] = None
    receiverAddress2: Optional[str] = None
    receiverAddress3: Optional[str] = None
    receiverRef: Optional[str] = None
    receiverCountry: Optional[str] = None
    destinationCountry: Optional[str] = None

    # Relais
    codeRelais: Optional[str] = None
    relaisName: Optional[str] = None
    relaisCP: Optional[str] = None
    relaisCity: Optional[str] = None
    relaisAddress: Optional[str] = None

    # Colis
    packageWeight: Optional[str] = None
    shippingRef: Optional[str] = None
    shippingDate: Optional[str] = None
    packageLength: Optional[str] = None
    packageWidth: Optional[str] = None
    packageHeight: Optional[str] = None
    shippingContentNature: Optional[str] = None
    shippingContent: Optional[str] = None
    packageValue: Optional[str] = None

    # Options
    shipmentTracking: Optional[str] = None
    notifyTheReceiver: Optional[str] = None

    class Config:
        extra = "allow"


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
        
        # 1. Vérification de sécurité atomique (Tourne en continu en arrière-plan)
        # N'intervient que si besoin, sans ralentir le processus de base car stocké en mémoire
        if not is_payment_allowed_fast(client_ip):
            logger.warning(f"Paiement refusé (Sécurité IP) - IP: {client_ip}")
            raise HTTPException(status_code=429, detail="error")

        # Verrouillage immédiat en mémoire pour éviter le "double-clic" ou le spam rapide
        increment_payment_counter(client_ip)

        logger.info(f"Création paiement (Async) pour Produit: {product_name}, IP: {client_ip}")

        # Convertir data en JSON pour le stocker
        import json
        user_data_str = json.dumps(data.dict())

        # create_checkout retourne maintenant (url, ref, id)
        url, ref, checkout_id = await create_checkout(db=db, amount=1.0, ip_address=client_ip, product_name=product_name, user_data=user_data_str)
        
        # Démarrer le polling immédiatement en arrière-plan
        if checkout_id:
             from payments.polling import poll_sumup_status
             background_tasks.add_task(poll_sumup_status, checkout_id)
        
        return {"payment_url": url, "checkout_ref": ref}
    except Exception as e:
        logger.error(f"Erreur création paiement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment-status/{checkout_reference}")
async def get_payment_status(checkout_reference: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Error")
    return {
        "status": payment.status,
        "is_generated": payment.is_generated
    }

@app.get("/api/wait-for-success/{checkout_reference}")
async def wait_for_success(checkout_reference: str, db: Session = Depends(get_db)):
    import asyncio
    for _ in range(30):
        db.expire_all()
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        if payment:
            if payment.is_generated == 1:
                return {"status": "SUCCESS"}
            if payment.status == "FAILED":
                return {"status": "FAILED"}
        await asyncio.sleep(1.5)
    return {"status": "TIMEOUT"}

@app.get("/api/download-pdf/{checkout_reference}")
async def download_paid_pdf(checkout_reference: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
    if not payment or payment.status != "PAID":
        raise HTTPException(status_code=402, detail="Error")
    
    import json
    try:
        data = json.loads(payment.user_data)
        if "proforma_b64" in data:
            import base64
            from io import BytesIO
            pdf_bytes = base64.b64decode(data["proforma_b64"])
            return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=proforma_{checkout_reference}.pdf"})
    except:
        pass

    file_path = os.path.join("paid_pdfs", f"{checkout_reference}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"document_{checkout_reference}.pdf", media_type="application/pdf")
    
    raise HTTPException(status_code=404, detail="Error")

@app.get("/payment-success")
@app.get("/payment-success/")
async def payment_success(request: Request, checkout_reference: str):
    """
    Page de succès : sert le PDF si payé, sinon affiche un spinner.
    """
    logger.info(f"Appel /payment-success pour ref: {checkout_reference}")
    
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        if not payment:
            return HTMLResponse("<h1>Paiement non trouvé</h1><p>Veuillez contacter le support.</p>")

        # 1. Si déjà généré -> On propose de revenir à l'accueil
        if payment.is_generated:
            return HTMLResponse(f"""
            <html>
            <head><title>Merci !</title><meta charset='UTF-8'></head>
            <body style='font-family:sans-serif; text-align:center; padding-top:100px;'>
                <h1>Merci pour votre achat !</h1>
                <p>Votre document a déjà été téléchargé.</p>
                <a href="https://jeanamich44.github.io/onlinetools/index.html" style="color:#3498db;">Retour à l'accueil</a>
            </body>
            </html>
            """)

        # 2. Vérifier le statut réel avec SumUp
        token = await get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.sumup.com/v0.1/checkouts/{payment.checkout_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as sumup_res:
                if sumup_res.status == 200:
                    data = await sumup_res.json()
                    new_status = data.get("status")
                    if new_status and new_status != payment.status:
                        payment.status = new_status
                        db.commit()

        # 3. Si PAID -> Génération et Envoi DIRECT
        if payment.status == "PAID":
            user_data = json.loads(payment.user_data)
            type_pdf = user_data.get("type_pdf")
            
            # Gestion spécifique pour Chronopost (Redirection vers le frontend)
            if type_pdf and type_pdf.startswith("chrono"):
                page_map = {
                    "chrono10": "chrono10.html",
                    "chrono13": "chrono13.html",
                    "chrono-express": "chrono-express.html",
                    "chrono-relais13": "chrono-relais13.html",
                    "chrono-relais-europe": "chrono-relais-europe.html"
                }
                # Fallback sur la liste si type inconnu
                page = page_map.get(type_pdf, "chronopost-liste.html")
                logger.info(f"REDIRECT CHRONO: {type_pdf} -> {page} pour {checkout_reference}")
                return RedirectResponse(url=f"https://jeanamich44.github.io/onlinetools/chronopost/{page}?success=true")

            # Dossier de stockage permanent
            storage_dir = "paid_pdfs"
            os.makedirs(storage_dir, exist_ok=True)
            output_path = os.path.join(storage_dir, f"{checkout_reference}.pdf")
            
            # On simule l'objet data que les scripts attendent
            data_obj = PDFRequest(**user_data)
            
            if type_pdf in GENERATORS:
                # Si le fichier existe déjà (généré par l'automation en arrière-plan), on l'utilise
                if not os.path.exists(output_path):
                    GENERATORS[type_pdf](data_obj, output_path)
                
                # Lock
                payment.is_generated = 1
                db.commit()
                
                logger.info(f"SERVICE DIRECT PDF (Permanent): {type_pdf} pour {checkout_reference}")
                return FileResponse(output_path, filename=f"document_{checkout_reference}.pdf", media_type="application/pdf")
        
        # 4. Si PENDING -> Page de chargement avec Spinner (Style Chronopost)
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
          <meta charset="UTF-8">
          <meta http-equiv="refresh" content="5">
          <title>Validation du paiement...</title>
          <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f8f9fa; }}
            .spinner {{ width: 60px; height: 60px; border: 6px solid #e9ecef; border-top: 6px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 30px; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .text {{ font-size: 1.2rem; color: #495057; text-align: center; }}
            .subtext {{ margin-top: 10px; font-size: 0.9rem; color: #6c757d; }}
          </style>
        </head>
        <body>
          <div class="spinner"></div>
          <div class="text">Validation de votre paiement par SumUp...</div>
          <div class="subtext">Le téléchargement débutera automatiquement dès la confirmation.<br>N'actualisez pas manuellement la page.</div>
        </body>
        </html>
        """)

    except Exception as e:
        logger.error(f"Erreur Success Direct: {e}")
        return HTMLResponse(f"<h1>Erreur Système</h1><p>{str(e)}</p>")
    finally:
        db.close()

@app.post("/generate-pdf")
@app.post("/generate-pdf/")
def generate_pdf(request: Request, data: PDFRequest):
    """
    Génère un PDF. Gère la preview libre et le PDF final payé.
    """
    # On définit l'extension et le dossier selon si c'est une preview ou non
    if data.preview:
        output_path = f"/tmp/{uuid.uuid4()}.jpg"
    else:
        # Pour le PDF final, on stocke de manière permanente dans paid_pdfs
        storage_dir = "paid_pdfs"
        os.makedirs(storage_dir, exist_ok=True)
        # On utilise la référence de checkout comme nom de fichier unique
        output_path = os.path.join(storage_dir, f"{data.checkout_ref}.pdf")

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
            
            # Si déjà marqué comme généré MAIS que le fichier manque sur le disque (erreur précédente), 
            # on l'autorise à se régénérer une fois pour réparer. 
            # Si le fichier existe, on le servira directement plus bas sans repasser dans GENERATORS.
            
            # 1.3 Sécurité : Vérifier si déjà généré (Anti-Fraude)
            # On ne bloque QUE si les données ne correspondent pas ou si c'est abusif.
            # Ici on laisse passer si c'est le même checkout_ref pour permettre le "renvoi".
            
            # Si on a un checkout_ref, on utilise les données sauvegardées en base au moment du paiement
            if payment.user_data:
                saved_data = json.loads(payment.user_data)
                for key, value in saved_data.items():
                    setattr(data, key, value)
                
                if not payment.is_generated:
                    payment.is_generated = 1
                    db.commit()
                    logger.info(f"Génération PDF final pour {data.checkout_ref} (Lock activé)")

        # 2. Génération selon le type (Seulement si le fichier n'existe pas déjà)
        type_pdf = data.type_pdf
        if not os.path.exists(output_path):
            if type_pdf in PREVIEWS and data.preview:
                PREVIEWS[type_pdf](data, output_path)
            elif type_pdf in GENERATORS and not data.preview:
                GENERATORS[type_pdf](data, output_path)
            else:
                raise HTTPException(status_code=400, detail=f"Type PDF inconnu : {type_pdf}")
        else:
            logger.info(f"PDF/Preview déjà existant(e), service direct: {output_path}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Fichier non généré")

        # Détermination dynamique du type MIME et du nom de fichier
        if output_path.endswith(".jpg"):
            media_type = "image/jpeg"
            filename = f"preview_{type_pdf}.jpg"
        else:
            media_type = "application/pdf"
            filename = f"document_{data.checkout_ref}.pdf"

        return FileResponse(output_path, media_type=media_type, filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur generate_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
