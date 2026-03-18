
# =================================================================================
# IMPORTS
# =================================================================================

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
from script.responses import chrono_redirect_url, success_download_page, waiting_spinner_page, payment_not_found_page, error_page

# ==============================================================================
# CONSTANTES
# ==============================================================================

DIRECT_FREE_PROCESS = True

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

# =================================================================================
# CONFIGURATION APP
# =================================================================================

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

# =================================================================================
# MODÈLES
# =================================================================================

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



# =================================================================================
# SIMULATION DE PRIX
# =================================================================================

SIMULATION_API_URL = "https://transporteur.up.railway.app"

async def get_price_from_simulator(data: dict, product_name: str):
    try:
        if "chronopost" in product_name or data.get("type_pdf") == "chronopost" or "chrono" in product_name:
            mapping = {
                "chrono-10": "Chrono 10",
                "chrono-13": "Chrono 13",
                "chrono-relais-13": "relais",
                "chrono-relais-europe": "relais",
                "chrono-express": "Chrono Express"
            }
            target_label = mapping.get(product_name)
            
            payload = {
                "sender_zip": data.get("senderCP") or data.get("senderZipCode") or data.get("sender_zip") or "75001",
                "sender_city": data.get("senderCity") or data.get("sender_city") or "PARIS",
                "recipient_zip": data.get("receiverCP") or data.get("receiverZipCode") or data.get("receiver_zip") or data.get("recipient_zip") or data.get("recipientZipCode") or data.get("recipient_cp") or "75001",
                "recipient_city": data.get("receiverCity") or data.get("receiver_city") or data.get("recipient_city") or "PARIS",
                "sender_iso": data.get("senderCountry") or data.get("sender_iso") or "FR",
                "recipient_iso": data.get("receiverCountry") or data.get("destinationCountry") or data.get("receiver_iso") or data.get("recipient_iso") or data.get("receiverCountryCode") or "FR"
            }

            try:
                payload["weight"] = float(data.get("packageWeight") or data.get("weight") or 1.0)
            except:
                payload["weight"] = 1.0

            logger.info(f"Simulate Chronopost payload: {payload} for product: {product_name}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{SIMULATION_API_URL}/api/chronopost/simulate", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        offers = res_json.get("offers", [])
                        logger.info(f"Chronopost Sim success: {len(offers)} offers found")
                        
                        target_clean = target_label.lower().replace(" ", "") if target_label else None
                        for offer in offers:
                            label_clean = offer["label"].lower().replace(" ", "")
                            if target_clean and (target_clean in label_clean or label_clean in target_clean):
                                logger.info(f"Match trouvé Chronopost: {offer['label']} -> {offer['price']}€")
                                return offer["price"]
                        
                        logger.warning(f"Aucun match Chronopost pour target: {target_label}. Offers dispo: {[o['label'] for o in offers]}")
                        raise HTTPException(status_code=400, detail="service_not_found")
                    else:
                        text = await resp.text()
                        logger.error(f"Erreur Simulator Chronopost ({resp.status}): {text}")
                        raise HTTPException(status_code=400, detail="simulator_error")
                    
        elif "colissimo" in product_name or data.get("type_pdf") == "colissimo":
            mapping = {
                "colissimo-standard": "Colissimo Domicile",
                "colissimo-expert": "Colissimo Expert",
                "colissimo-relais": "Colissimo Relais",
                "colissimo-europe": "Colissimo Europe",
                "colissimo-inter": "Colissimo International",
                "colissimo-om": "Colissimo Outre-Mer"
            }
            target_label = mapping.get(product_name)
            
            payload = {
                "sender_iso": data.get("senderCountry") or data.get("sender_iso") or "FR",
                "recipient_iso": data.get("receiverCountry") or data.get("destinationCountry") or data.get("receiver_iso") or data.get("recipient_iso") or data.get("receiverCountryCode") or "FR",
                "product_code": data.get("productCode") or "DOM"
            }
            try:
                payload["weight"] = float(data.get("packageWeight") or data.get("weight") or 1.0)
            except:
                payload["weight"] = 1.0

            logger.info(f"Simulate Colissimo payload: {payload} for product: {product_name}")
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{SIMULATION_API_URL}/api/colissimo/simulate", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        offers = res_json.get("offers", [])
                        logger.info(f"Colissimo Sim success: {len(offers)} offers found")
                        
                        target_clean = target_label.lower().replace(" ", "") if target_label else None
                        for offer in offers:
                            label_clean = offer["label"].lower().replace(" ", "")
                            if target_clean and (target_clean in label_clean or label_clean in target_clean):
                                logger.info(f"Match trouvé Colissimo: {offer['label']} -> {offer['price']}€")
                                return offer["price"]
                        
                        logger.warning(f"Aucun match Colissimo pour target: {target_label}. Offers dispo: {[o['label'] for o in offers]}")
                        raise HTTPException(status_code=400, detail="service_not_found")
                    else:
                        text = await resp.text()
                        logger.error(f"Erreur Simulator Colissimo ({resp.status}): {text}")
                        raise HTTPException(status_code=400, detail="simulator_error")
        
        raise HTTPException(status_code=400, detail="error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail="error")

# =================================================================================
# ENDPOINTS PAIEMENT
# =================================================================================

async def _run_bypass_async(checkout_ref: str):
    from payments.database import SessionLocal, Payment
    from payments.automation import trigger_automatic_generation
    db_local = SessionLocal()
    try:
        payment = db_local.query(Payment).filter(Payment.checkout_ref == checkout_ref).first()
        if payment:
            await trigger_automatic_generation(payment, db_local)
    finally:
        db_local.close()

@app.post("/create-payment")
async def create_payment_endpoint(request: Request, data: dict, background_tasks: BackgroundTasks, product_name: str = "default", db: Session = Depends(get_db)):
    try:
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        
        if not is_payment_allowed_fast(client_ip):
            logger.warning(f"Paiement refusé (Sécurité IP) - IP: {client_ip}")
            raise HTTPException(status_code=429, detail="error")

        amount = await get_price_from_simulator(data, product_name)
        increment_payment_counter(client_ip)
        
        # Enrichissement des données pour le transporteur
        if "chrono" in product_name:
            if "10" in product_name: data["valeurproduct"] = "10"
            elif "relais" in product_name: data["valeurproduct"] = "relais"
            else: data["valeurproduct"] = "13"
            
            # Détection pays si manquant
            if not data.get("destinationCountry"):
                if "europe" in product_name: data["destinationCountry"] = "BE" # Défaut Europe
                else: data["destinationCountry"] = "FR"

        user_data_str = json.dumps(data)

        # =========== SYSTÈME DE BYPASS DES PAIEMENTS ===========
        if DIRECT_FREE_PROCESS:
            import uuid
            checkout_ref = str(uuid.uuid4())
            new_payment = Payment(
                checkout_ref=checkout_ref,
                checkout_id=f"BYPASS_{checkout_ref}",
                amount=amount,
                currency="EUR",
                status="PAID",
                ip_address=client_ip,
                product_name=product_name,
                user_data=user_data_str
            )
            db.add(new_payment)
            db.commit()
            db.refresh(new_payment)

            logger.info(f"⚡ [BYPASS MODE] Paiement simulé pour {checkout_ref}. Lancement automatique de la génération...")
            background_tasks.add_task(_run_bypass_async, checkout_ref)

            APP_DOMAIN = "https://generate-docs-production.up.railway.app"
            bypass_url = f"{APP_DOMAIN}/payment-success?checkout_reference={checkout_ref}"
            return {"payment_url": bypass_url, "checkout_ref": checkout_ref}
        # =======================================================

        url, ref, checkout_id = await create_checkout(db=db, amount=amount, ip_address=client_ip, product_name=product_name, user_data=user_data_str)
        
        if checkout_id:
             background_tasks.add_task(poll_sumup_status, checkout_id)
        
        return {"payment_url": url, "checkout_ref": ref}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="error")

# =================================================================================
# STATUS PAIEMENT
# =================================================================================

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

# =================================================================================
# TÉLÉCHARGEMENT PDF
# =================================================================================

@app.get("/api/download-pdf/{checkout_reference}")
async def download_paid_pdf(checkout_reference: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
    if not payment or payment.status != "PAID":
        raise HTTPException(status_code=402, detail="error")
    
    file_path = os.path.join("paid_pdfs", f"{checkout_reference}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"document_{checkout_reference}.pdf", media_type="application/pdf")

    try:
        data = json.loads(payment.user_data)
        if "proforma_b64" in data:
            pdf_bytes = base64.b64decode(data["proforma_b64"])
            return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=proforma_{checkout_reference}.pdf"})
    except:
        pass
    
    raise HTTPException(status_code=404, detail="error")

# =================================================================================
# SUCCESS PAIEMENT
# =================================================================================

@app.get("/payment-success")
@app.get("/payment-success/")
async def payment_success(request: Request, checkout_reference: str):
    logger.info(f"Appel /payment-success pour ref: {checkout_reference}")
    
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        if not payment:
            return HTMLResponse(payment_not_found_page())

        if payment.is_generated:
            user_data_parsed = {}
            if payment.user_data:
                try:
                    user_data_parsed = json.loads(payment.user_data)
                except:
                    pass
                
            type_pdf = user_data_parsed.get("type_pdf", "")
            
            if type_pdf.startswith("chrono"):
                email = user_data_parsed.get("sendToThirdPersonInfo", "")
                return RedirectResponse(url=chrono_redirect_url(type_pdf, email))

            return HTMLResponse(success_download_page(checkout_reference))

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
        
        return HTMLResponse(waiting_spinner_page())

    except Exception as e:
        logger.error(f"Erreur Success Direct: {e}")
        return HTMLResponse(error_page(str(e)))
    finally:
        db.close()

# =================================================================================
# ENDPOINT GÉNÉRATION PDF
# =================================================================================

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


