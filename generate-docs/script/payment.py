import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
CLIENT_ID = "cc_classic_ju7wWXPLFWeNtFgwerzub54kOSlsh".strip()
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS2lPsVFmKZHpQKI8fwt8V6zoIFQLqpl46jLCizbf".strip()
MERCHANT_CODE = "MCHYQUG3".strip()
API_KEY = "sup_sk_3pYZm9Maezj1XgpL76qxKvKUc".strip() 

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

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

def create_checkout(amount=1.0, currency="EUR", email=None):
    """Creates a checkout session and returns the payment URL."""
    
    # Try to get a token (will raise Exception if fails)
    token = get_access_token()
    
    checkout_ref = str(uuid.uuid4())

    checkout_ref = str(uuid.uuid4())
    valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"

    payload = {
        "amount": amount,
        "currency": currency,
        "checkout_reference": checkout_ref,
        "merchant_code": MERCHANT_CODE,
        "description": "Payment for OnlineTools service",
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
        raise Exception(f"Checkout failed: {response.status_code} {response.text}")
        
    response.raise_for_status()
    
    data = response.json()
    return data.get("hosted_checkout_url")
