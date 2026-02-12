import requests
import json
import uuid
import time
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

import logging
logger = logging.getLogger(__name__)

# Token Cache
_token_cache = {
    "access_token": None,
    "expires_at": 0 # Timestamp
}

def get_access_token():
    """
    Retrieves an access token, using a global cache to avoid repetitive requests.
    Tokens are valid for 1 hour approx.
    """
    global _token_cache
    
    # Check if we have a valid token
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    # Method 1: Body + Bearer Header (Confirmed working in debug)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        response = requests.post(TOKEN_URL, data=payload_str, headers=headers)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            expires_in = data.get("expires_in", 3600) # Default 1h
            
            # Update cache (subtract 60s for safety buffer)
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = time.time() + expires_in - 60
            
            logger.info("🔑 New SumUp Access Token retrieved and cached.")
            return token
        
        # Log failure
        logger.error(f"Token Auth Failed: {response.status_code} {response.text}")
        raise Exception(f"Token Auth Failed: {response.status_code} {response.text}")

    except Exception as e:
        raise Exception(f"Token Retrieval Error: {str(e)}")

def create_checkout(db: Session, amount=1.0, currency="EUR", ip_address=None, product_name=None):
    """Creates a checkout session and returns the payment URL."""
    
    # 1. Generate local reference
    checkout_ref = str(uuid.uuid4())
    
    # 2. Call SumUp API FIRST (Optimization: No DB insert before API call)
    try:
        # Try to get a token (will raise Exception if fails)
        token = get_access_token()
        
        valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"

        # Use the app's domain for webhook callback
        APP_DOMAIN = "https://generate-docs-production.up.railway.app"
        
        # We don't have payement.id yet, so we use checkout_ref in description
        payload = {
            "amount": amount,
            "currency": currency,
            "checkout_reference": checkout_ref,
            "pay_to_email": PAY_TO_EMAIL,
            "description": f"Payment Ref: {checkout_ref}", 
            "valid_until": valid_until,
            "redirect_url": f"{APP_DOMAIN}/payment-success?checkout_reference={checkout_ref}",
            "return_url": f"{APP_DOMAIN}/webhook", 
            "hosted_checkout": {
                "enabled": True
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(CHECKOUT_URL, json=payload, headers=headers)
    
        if response.status_code >= 400:
            raise Exception(f"Checkout failed: {response.status_code} {response.text}")
            
        response.raise_for_status()
        
        data = response.json()
        
        # 3. Create record in DB (Wait for API response success)
        # This is faster as it avoids an initial INSERT + COMMIT before the API call
        new_payment = Payment(
            checkout_ref=checkout_ref,
            amount=amount,
            currency=currency,
            status="PENDING", # It is created successfully at SumUp
            ip_address=ip_address,
            product_name=product_name,
            checkout_id=data.get("id"),
            payment_url=data.get("hosted_checkout_url")
        )
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        
        return (data.get("hosted_checkout_url"), checkout_ref, data.get("id"))

    except Exception as e:
        logger.error(f"Error in create_checkout: {e}")
        raise e
