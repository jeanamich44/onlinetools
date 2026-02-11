from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uuid, logging, os, requests

from script.lbp import generate_lbp_pdf, generate_lbp_preview
from script.sg import generate_sg_pdf, generate_sg_preview
from script.bfb import generate_bfb_pdf, generate_bfb_preview
from script.revolut import generate_revolut_pdf, generate_revolut_preview
from script.ca import generate_ca_pdf, generate_ca_preview
from script.cm import generate_cm_pdf, generate_cm_preview
from script.cic import generate_cic_pdf, generate_cic_preview
from script.qonto import generate_qonto_pdf, generate_qonto_preview
from script.maxance import generate_maxance_pdf, generate_maxance_preview
from payments.payment import create_checkout
from payments.database import init_db, get_db, Payment
from sqlalchemy.orm import Session
from fastapi import Depends

# =========================
# INITIALISATION
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
# SCHEMA
# =========================

class PDFRequest(BaseModel):
    type_pdf: str  # "lbp" | "sg" | "bfb" | "revolut" | "credit_agricole"
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
# =========================

from fastapi import Request

@app.post("/create-payment")
def create_payment_endpoint(request: Request, product_name: str = "default", db: Session = Depends(get_db)):
    try:
        # Get real client IP if behind proxy (like Railway)
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        
        logger.info(f"Creating payment for Product: {product_name}, IP: {client_ip}")

        url = create_checkout(db=db, amount=1.0, ip_address=client_ip, product_name=product_name)
        return {"payment_url": url}
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from payments.database import Payment

@app.get("/payment-success")
def payment_success(checkout_reference: Optional[str] = None, db: Session = Depends(get_db)):
    # LOGGING FOR DEBUGGING
    logger.info(f"Payment Success Page Hit. Ref: {checkout_reference}")
    
    status_message = "Merci ! Votre transaction a été enregistrée avec succès."
    status_color = "#28a745" # Green
    status_title = "✅ Paiement Validé !"

    if checkout_reference:
        try:
            # Find payment by our local ref
            payment = db.query(Payment).filter(Payment.checkout_ref == checkout_reference).first()
            
            if payment:
                logger.info(f"Payment found in DB: {payment.id}, Status: {payment.status}")
                if payment.status == "PENDING":
                    # Force verification with SumUp API
                    from payments.payment import get_access_token
                    try:
                        token = get_access_token()
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        if payment.checkout_id:
                            logger.info(f"Verifying with SumUp API for ID: {payment.checkout_id}")
                            CHECKOUT_URL = f"https://api.sumup.com/v0.1/checkouts/{payment.checkout_id}"
                            response = requests.get(CHECKOUT_URL, headers=headers)
                            
                            logger.info(f"SumUp API Response: {response.status_code} {response.text}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                new_status = data.get("status")
                                logger.info(f"New Status from SumUp: {new_status}")
                                if new_status == "PAID":
                                    payment.status = "PAID"
                                    db.commit()
                                    logger.info(f"Payment {payment.id} validated via success page.")
                                elif new_status == "FAILED":
                                    payment.status = "FAILED"
                                    db.commit()
                                    status_title = "❌ Paiement Échoué"
                                    status_message = "Le paiement a échoué ou a été annulé."
                                    status_color = "#dc3545"
                            else:
                                logger.error(f"Failed to check status: {response.text}")
                        else:
                             logger.warning("Payment has no checkout_id in DB yet.")
                    except Exception as ex:
                        logger.error(f"Error calling SumUp: {ex}")

                elif payment.status == "FAILED":
                     status_title = "❌ Paiement Échoué"
                     status_message = "Ce paiement est marqué comme échoué."
                     status_color = "#dc3545"
            else:
                logger.warning(f"Payment success page hit with unknown ref: {checkout_reference}")
        except Exception as e:
            logger.error(f"Error checking status on success page: {e}")
    else:
        logger.warning("Payment success page hit WITHOUT checkout_reference!")

    html_content = f"""
    <html>
        <head>
            <title>Statut du Paiement</title>
             <style>
                body {{ font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }}
                .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }}
                h1 {{ color: {status_color}; }}
                p {{ color: #555; }}
                .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>{status_title}</h1>
                <p>{status_message}</p>
                <p>Vous pouvez fermer cette page ou retourner à l'accueil.</p>
                <a href="/" class="btn">Retour à l'accueil</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        from script.payment import get_access_token
        
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

@app.post("/generate-pdf")
def generate_pdf(data: PDFRequest):
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
