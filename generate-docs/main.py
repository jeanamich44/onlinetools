# =========================
# IMPORTS
# =========================

import os
import uuid
import logging
import requests
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Database & Payment
from payments.database import init_db, get_db, Payment
from payments.payment import create_checkout, get_access_token # Corrected import
from payments.polling import poll_sumup_status

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# DATABASE & APP SETUP
# =========================

# Initialize tables
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# =========================
# PYDANTIC MODELS
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


# =========================
# PAYMENT ROUTES
# =========================

@app.post("/create-payment")
def create_payment_endpoint(request: Request, background_tasks: BackgroundTasks, product_name: str = "default", db: Session = Depends(get_db)):
    """
    Creates a new payment checkout session.
    Automatically captures client IP (handling proxies) and product context.
    Starts background polling immediately for faster status updates.
    """
    try:
        # Get real client IP if behind proxy (like Railway)
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        
        logger.info(f"Creating payment for Product: {product_name}, IP: {client_ip}")

        # create_checkout now returns (url, ref, id)
        url, ref, checkout_id = create_checkout(db=db, amount=1.0, ip_address=client_ip, product_name=product_name)
        
        # Start polling immediately in background
        if checkout_id:
             background_tasks.add_task(poll_sumup_status, checkout_id)
        
        return {"payment_url": url}
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payment-success")
def payment_success(checkout_reference: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Handles payment success redirect.
    Renders a page that polls /check-status until payment is confirmed.
    """
    logger.info(f"Payment Success Page Hit. Ref: {checkout_reference}")
    
    html_content = f"""
    <html>
        <head>
            <title>Vérification du Paiement</title>
             <style>
                body {{ font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }}
                .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }}
                h1 {{ color: #007bff; }}
                p {{ color: #555; }}
                .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .hidden {{ display: none; }}
                .loader {{ border: 5px solid #f3f3f3; border-top: 5px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
            <script>
                async function checkStatus() {{
                    const ref = "{checkout_reference}";
                    if (!ref || ref === "None") return;

                    try {{
                        const response = await fetch(`/check-status?checkout_reference=${{ref}}`);
                        const data = await response.json();

                        if (data.status === "PAID") {{
                            document.getElementById("loader").classList.add("hidden");
                            document.getElementById("status-title").innerText = "✅ Paiement Validé !";
                            document.getElementById("status-title").style.color = "#28a745";
                            document.getElementById("status-message").innerText = "Merci ! Votre transaction a été enregistrée avec succès.";
                            document.getElementById("home-btn").classList.remove("hidden");
                            return; // Stop polling
                        }} else if (data.status === "FAILED") {{
                            document.getElementById("loader").classList.add("hidden");
                            document.getElementById("status-title").innerText = "❌ Paiement Échoué";
                            document.getElementById("status-title").style.color = "#dc3545";
                            document.getElementById("status-message").innerText = "Le paiement a échoué ou a été annulé.";
                            document.getElementById("home-btn").classList.remove("hidden");
                            return; // Stop polling
                        }}
                    }} catch (error) {{
                        console.error("Error checking status:", error);
                    }}

                    // Retry every 5 seconds
                    setTimeout(checkStatus, 5000);
                }}

                window.onload = checkStatus;
            </script>
        </head>
        <body>
            <div class="card">
                <h1 id="status-title">Vérification en cours...</h1>
                <div id="loader" class="loader"></div>
                <p id="status-message">Veuillez patienter pendant que nous confirmons votre paiement.</p>
                <p>Ne fermez pas cette page.</p>
                <a id="home-btn" href="/index.html" class="btn hidden">Retour à l'accueil</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/check-status")
def check_payment_status(checkout_reference: str, db: Session = Depends(get_db)):
    """
    Endpoint to check payment status.
    Called by the frontend polling script.
    """
    try:
        payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
        
        if not payment:
            return {"status": "UNKNOWN", "message": "Payment not found"}
        
        # If already finalized, return status immediately
        if payment.status in ["PAID", "FAILED"]:
            return {"status": payment.status}
        
        # If PENDING, verify with SumUp API
        try:
            token = get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            if payment.checkout_id:
                CHECKOUT_URL = f"https://api.sumup.com/v0.1/checkouts/{payment.checkout_id}"
                response = requests.get(CHECKOUT_URL, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    new_status = data.get("status")
                    
                    if new_status and new_status != payment.status:
                        payment.status = new_status
                        db.commit()
                        logger.info(f"Create-Check-Status: Payment {payment.id} updated to {new_status}")
                    
                    return {"status": payment.status}
            
        except Exception as e:
            logger.error(f"Error checking SumUp API: {e}")
            
        return {"status": payment.status} # Return current status (likely PENDING)
        
    except Exception as e:
        logger.error(f"Check status endpoint error: {e}")
        return {"status": "ERROR", "detail": str(e)}


@app.post("/webhook")
async def webhook_endpoint(data: dict, db: Session = Depends(get_db)):
    """
    Webhook called by SumUp when a payment status changes.
    Payload: {"event_type": "CHECKOUT_STATUS_CHANGED", "id": "..."}
    """
    try:
        checkout_id = data.get("id")
        
        if not checkout_id:
            return {"status": "ignored", "reason": "no_id"}

        # Find payment by checkout_id
        payment = db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
        
        if not payment:
            return {"status": "ignored", "reason": "not_found"}

        # Verify status with SumUp API
        # We need a fresh token
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Determine endpoint based on ID format (v0.1 checkouts usually start with 'c-')
        # But for V0.1 API, the endpoint is GET /v0.1/checkouts/{id}
        CHECKOUT_URL = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
        
        response = requests.get(CHECKOUT_URL, headers=headers)
        
        if response.status_code == 200:
            checkout_data = response.json()
            new_status = checkout_data.get("status") # e.g., "PAID", "PENDING", "FAILED"
            
            if new_status and new_status != payment.status:
                payment.status = new_status
                db.commit()
                return {"status": "updated", "id": checkout_id, "new_status": new_status}
            else:
                return {"status": "unchanged", "current_status": payment.status}
        else:
             logger.error(f"Failed to verify checkout {checkout_id}: {response.text}")
             return {"status": "error", "reason": "verification_failed"}

    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return {"status": "error", "detail": str(e)}


# =========================
# PDF GENERATION ROUTES
# =========================

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):
    """
    Generates a PDF based on the requested type (LBP, SG, etc.).
    Supports preview mode.
    """
    output_path = f"/tmp/{uuid.uuid4()}.pdf"

    try:
        if data.type_pdf == "lbp":
            if data.preview:
                generate_lbp_preview(data, output_path)
            else:
                generate_lbp_pdf(data, output_path)

        elif data.type_pdf == "sg":
            if data.preview:
                generate_sg_preview(data, output_path)
            else:
                generate_sg_pdf(data, output_path)

        elif data.type_pdf == "bfb":
            if data.preview:
                generate_bfb_preview(data, output_path)
            else:
                generate_bfb_pdf(data, output_path)

        elif data.type_pdf == "revolut":
            if data.preview:
                generate_revolut_preview(data, output_path)
            else:
                generate_revolut_pdf(data, output_path)

        elif data.type_pdf == "ca":
            if data.preview:
                generate_ca_preview(data, output_path)
            else:
                generate_ca_pdf(data, output_path)

        elif data.type_pdf == "cm":
            if data.preview:
                generate_cm_preview(data, output_path)
            else:
                generate_cm_pdf(data, output_path)

        elif data.type_pdf == "cic":
            if data.preview:
                generate_cic_preview(data, output_path)
            else:
                generate_cic_pdf(data, output_path)

        elif data.type_pdf == "qonto":
            if data.preview:
                generate_qonto_preview(data, output_path)
            else:
                generate_qonto_pdf(data, output_path)

        elif data.type_pdf == "maxance":
            if data.preview:
                generate_maxance_preview(data, output_path)
            else:
                generate_maxance_pdf(data, output_path)

        else:
            raise HTTPException(status_code=400, detail="type_pdf invalide")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="PDF non généré")

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="rib.pdf",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
