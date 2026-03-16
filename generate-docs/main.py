
# ---------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------

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
from pydantic import BaseModel, parse_obj_as, root_validator
from sqlalchemy.orm import Session
import base64
from io import BytesIO
import uvicorn

from payments.database import init_db, get_db, Payment, SessionLocal
from payments.payment import create_checkout, get_access_token
from securite.payment_guard import is_payment_allowed_fast, security_worker, increment_payment_counter

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
from payments.reconcile import start_reconciliation_loop
from payments.polling import poll_sumup_status

# ---------------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------------
# CONFIGURATION APP
# ---------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_reconciliation_loop(interval=900))
    asyncio.create_task(security_worker())
    logger.info("Serveur démarré - Tâches de fond (Réconciliation & Sécurité) lancées.")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API Generate-Docs is running"}

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ---------------------------------------------------------------------------------
# MODÈLES
# ---------------------------------------------------------------------------------

class PDFRequest(BaseModel):
    type_pdf: str 
    preview: Optional[bool] = False

    sexe: Optional[str] = "m"

    nom_prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp_ville: Optional[str] = None
    telephone: Optional[str] = None

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
    agence_cp: Optional[str] = None
    agence_ville: Optional[str] = None
    agence_cp_ville: Optional[str] = None
    bank: Optional[str] = None

    @root_validator(pre=True)
    def handle_cp_ville(cls, values):
        if not values.get("cp_ville") and values.get("cp") and values.get("ville"):
            values["cp_ville"] = f"{values['cp']} {values['ville']}"
        
        if not values.get("agence_cp_ville") and values.get("agence_cp") and values.get("agence_ville"):
            values["agence_cp_ville"] = f"{values['agence_cp']} {values['agence_ville']}"
            
        return values

    nclient: Optional[str] = None
    ncontrat: Optional[str] = None
    norias: Optional[str] = None
    plaque: Optional[str] = None
    typevehicule: Optional[str] = None
    
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

    valeurproduct: Optional[str] = None
    
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

    codeRelais: Optional[str] = None
    relaisName: Optional[str] = None
    relaisCP: Optional[str] = None
    relaisCity: Optional[str] = None
    relaisAddress: Optional[str] = None

    packageWeight: Optional[str] = None
    shippingRef: Optional[str] = None
    shippingDate: Optional[str] = None
    packageLength: Optional[str] = None
    packageWidth: Optional[str] = None
    packageHeight: Optional[str] = None
    shippingContentNature: Optional[str] = None
    shippingContent: Optional[str] = None
    packageValue: Optional[str] = None

    shipmentTracking: Optional[str] = None
    notifyTheReceiver: Optional[str] = None

    class Config:
        extra = "allow"



# ---------------------------------------------------------------------------------
# SIMULATION DE PRIX
# ---------------------------------------------------------------------------------

SIMULATION_API_URL = "https://transporteur.up.railway.app"

async def get_price_from_simulator(data: dict, product_name: str):
    try:
        if "chronopost" in product_name or data.get("type_pdf") == "chronopost" or "chrono" in product_name:
            mapping = {
                "chrono-10": "Chrono 10",
                "chrono-13": "Chrono 13",
                "chrono-relais-13": "relais",
                "chrono-express": "Chrono Express"
            }
            target_label = mapping.get(product_name)
            
            payload = {
                "sender_zip": data.get("senderCP") or data.get("senderZipCode"),
                "sender_city": data.get("senderCity"),
                "recipient_zip": data.get("receiverCP") or data.get("receiverZipCode"),
                "recipient_city": data.get("receiverCity"),
                "weight": float(data.get("packageWeight") or 1.0),
                "sender_iso": data.get("senderCountry", "FR"),
                "recipient_iso": data.get("receiverCountry", "FR")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{SIMULATION_API_URL}/api/chronopost/simulate", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        offers = res_json.get("offers", [])
                        for offer in offers:
                            if target_label and target_label.lower() in offer["label"].lower():
                                return offer["price"]
                        raise HTTPException(status_code=400, detail="error")
                    
        elif "colissimo" in product_name or data.get("type_pdf") == "colissimo":
            mapping = {
                "colissimo-standard": "Colissimo Domicile",
                "colissimo-expert": "Colissimo Expert",
                "colissimo-relais": "Colissimo Relais"
            }
            target_label = mapping.get(product_name)
            
            payload = {
                "weight": float(data.get("packageWeight") or 1.0),
                "sender_iso": data.get("senderCountry", "FR"),
                "recipient_iso": data.get("receiverCountry", "FR"),
                "product_code": data.get("productCode") or "DOM"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{SIMULATION_API_URL}/api/colissimo/simulate", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        offers = res_json.get("offers", [])
                        for offer in offers:
                            if target_label and target_label.lower() in offer["label"].lower():
                                return offer["price"]
                        raise HTTPException(status_code=400, detail="error")
        
        raise HTTPException(status_code=400, detail="error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail="error")

# ---------------------------------------------------------------------------------
# ENDPOINTS PAIEMENT
# ---------------------------------------------------------------------------------

@app.post("/create-payment")
async def create_payment_endpoint(request: Request, data: PDFRequest, background_tasks: BackgroundTasks, product_name: str = "default", db: Session = Depends(get_db)):
    try:
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        
        if not is_payment_allowed_fast(client_ip):
            logger.warning(f"Paiement refusé (Sécurité IP) - IP: {client_ip}")
            raise HTTPException(status_code=429, detail="error")

        increment_payment_counter(client_ip)

        logger.info(f"Création paiement (Async) pour Produit: {product_name}, IP: {client_ip}")

        user_data_str = json.dumps(data.dict())
        amount = await get_price_from_simulator(data.dict(), product_name)
        
        url, ref, checkout_id = await create_checkout(db=db, amount=amount, ip_address=client_ip, product_name=product_name, user_data=user_data_str)
        
        if checkout_id:
             background_tasks.add_task(poll_sumup_status, checkout_id)
        
        return {"payment_url": url, "checkout_ref": ref}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="error")

# ---------------------------------------------------------------------------------
# STATUS PAIEMENT
# ---------------------------------------------------------------------------------

@app.get("/api/payment-status/{checkout_reference}")
async def get_payment_status(checkout_reference: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="error")
    return {
        "status": payment.status,
        "is_generated": payment.is_generated
    }

@app.get("/api/wait-for-success/{checkout_reference}")
async def wait_for_success(checkout_reference: str, db: Session = Depends(get_db)):
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

# ---------------------------------------------------------------------------------
# TÉLÉCHARGEMENT PDF
# ---------------------------------------------------------------------------------

@app.get("/api/download-pdf/{checkout_reference}")
async def download_paid_pdf(checkout_reference: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
    if not payment or payment.status != "PAID":
        raise HTTPException(status_code=402, detail="error")
    
    try:
        data = json.loads(payment.user_data)
        if "proforma_b64" in data:
            pdf_bytes = base64.b64decode(data["proforma_b64"])
            return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=proforma_{checkout_reference}.pdf"})
    except:
        pass

    file_path = os.path.join("paid_pdfs", f"{checkout_reference}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"document_{checkout_reference}.pdf", media_type="application/pdf")
    
    raise HTTPException(status_code=404, detail="error")

# ---------------------------------------------------------------------------------
# SUCCESS PAIEMENT
# ---------------------------------------------------------------------------------

@app.get("/payment-success")
@app.get("/payment-success/")
async def payment_success(request: Request, checkout_reference: str):
    logger.info(f"Appel /payment-success pour ref: {checkout_reference}")
    
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        if not payment:
            return HTMLResponse("<h1>Paiement non trouvé</h1><p>Veuillez contacter le support.</p>")

        if payment.is_generated:
            return HTMLResponse(f"""
            <html>
            <head><title>Merci !</title><meta charset='UTF-8'></head>
            <body style='font-family:sans-serif; text-align:center; padding-top:100px;'>
                <h1>Merci pour votre achat !</h1>
                <p>Votre document a déjà été téléchargé.</p>
                <a href="https://chezrheyy.ink/" style="color:#3498db;">Retour à l'accueil</a>
            </body>
            </html>
            """)

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

        if payment.status == "PAID":
            user_data = json.loads(payment.user_data)
            type_pdf = user_data.get("type_pdf")
            
            if type_pdf and type_pdf.startswith("chrono"):
                page_map = {
                    "chrono10": "chrono10.html",
                    "chrono13": "chrono13.html",
                    "chrono-express": "chrono-express.html",
                    "chrono-relais13": "chrono-relais13.html",
                    "chrono-relais-europe": "chrono-relais-europe.html"
                }
                page = page_map.get(type_pdf, "chronopost-liste.html")
                logger.info(f"REDIRECT CHRONO: {type_pdf} -> {page} pour {checkout_reference}")
                return RedirectResponse(url=f"https://www.chezrheyy.ink/chronopost/{page}?success=true")

            storage_dir = "paid_pdfs"
            os.makedirs(storage_dir, exist_ok=True)
            output_path = os.path.join(storage_dir, f"{checkout_reference}.pdf")
            
            data_obj = PDFRequest(**user_data)
            
            if type_pdf in GENERATORS:
                if not os.path.exists(output_path):
                    GENERATORS[type_pdf](data_obj, output_path)
                
                payment.is_generated = 1
                db.commit()
                
                logger.info(f"SERVICE DIRECT PDF (Permanent): {type_pdf} pour {checkout_reference}")
                return FileResponse(output_path, filename=f"document_{checkout_reference}.pdf", media_type="application/pdf")
        
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

# ---------------------------------------------------------------------------------
# ENDPOINT GÉNÉRATION PDF
# ---------------------------------------------------------------------------------

@app.post("/generate-pdf")
@app.post("/generate-pdf/")
def generate_pdf(request: Request, data: PDFRequest):
    if data.preview:
        output_path = f"/tmp/{uuid.uuid4()}.jpg"
    else:
        storage_dir = "paid_pdfs"
        os.makedirs(storage_dir, exist_ok=True)
        output_path = os.path.join(storage_dir, f"{data.checkout_ref}.pdf")

    db = SessionLocal()

    try:
        if not data.preview:
            if not data.checkout_ref:
                raise HTTPException(status_code=402, detail="error")
            
            payment = db.query(Payment).filter(Payment.checkout_ref == data.checkout_ref).first()
            if not payment or payment.status != "PAID":
                logger.warning(f"Unauthorized download: {data.checkout_ref}")
                raise HTTPException(status_code=402, detail="error")
            
            if payment.user_data:
                saved_data = json.loads(payment.user_data)
                for key, value in saved_data.items():
                    setattr(data, key, value)
                
                if not payment.is_generated:
                    payment.is_generated = 1
                    db.commit()
                    logger.info(f"Génération PDF final pour {data.checkout_ref} (Lock activé)")

        type_pdf = data.type_pdf
        if not os.path.exists(output_path):
            if type_pdf in PREVIEWS and data.preview:
                PREVIEWS[type_pdf](data, output_path)
            elif type_pdf in GENERATORS and not data.preview:
                GENERATORS[type_pdf](data, output_path)
            else:
                raise HTTPException(status_code=400, detail="error")
        else:
            logger.info(f"PDF/Preview déjà existant(e), service direct: {output_path}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="error")

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
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="error")
    finally:
        db.close()


