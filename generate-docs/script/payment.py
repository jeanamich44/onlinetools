import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
CLIENT_ID = "cc_classic_ju7wWXPLFWeNtFgwerzub54kOSlsh".strip()
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS2lPsVFmKZHpQKI8fwt8V6zoIFQLqpl46jLCizbf".strip()
# MERCHANT_CODE = "MCHYQUG3".strip() # Invalid
PAY_TO_EMAIL = "dupuisrenov83@outlook.fr"
API_KEY = "sup_sk_3pYZm9Maezj1XgpL76qxKvKUc".strip() 

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

from .database import Payment
from sqlalchemy.orm import Session

def get_access_token():
    """
    Retrieves an access token using the Method that worked in debug (Go-style).
    """
    # Method 1: Body + Bearer Header (Confirmed working in debug)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        response = requests.post(TOKEN_URL, data=payload_str, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        
        # Log failure
        print(f"Token Auth Failed: {response.status_code} {response.text}")
        raise Exception(f"Token Auth Failed: {response.status_code} {response.text}")

    except Exception as e:
        raise Exception(f"Token Retrieval Error: {str(e)}")

def create_checkout(db: Session, amount=1.0, currency="EUR", email=None):
    """Creates a checkout session and returns the payment URL."""
    
    # 1. Generate local reference
    checkout_ref = str(uuid.uuid4())
    
    # 2. Create PENDING record in DB
    new_payment = Payment(
        checkout_ref=checkout_ref,
        amount=amount,
        currency=currency,
        status="PENDING",
        email=email or PAY_TO_EMAIL
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # 3. Call SumUp API
    # Try to get a token (will raise Exception if fails)
    token = get_access_token()
    
    valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"

    payload = {
        "amount": amount,
        "currency": currency,
        "checkout_reference": checkout_ref,
        # "merchant_code": MERCHANT_CODE, # Removed as it was invalid
        "pay_to_email": PAY_TO_EMAIL,
        "description": f"Payment #{new_payment.id}",
        "valid_until": valid_until,
        "redirect_url": "https://google.com",
        "hosted_checkout": {
            "enabled": True
        }
    }
    
    if email:
        payload["pay_to_email"] = email

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(CHECKOUT_URL, json=payload, headers=headers)
    
    if response.status_code >= 400:
        # Update status to FAILED
        new_payment.status = "FAILED"
        db.commit()
        raise Exception(f"Checkout failed: {response.status_code} {response.text}")
        
    response.raise_for_status()
    
    data = response.json()
    
    # 4. Update DB with real checkout ID from SumUp
    new_payment.checkout_id = data.get("id")
    new_payment.payment_url = data.get("hosted_checkout_url")
    db.commit()
    
    return data.get("hosted_checkout_url")
