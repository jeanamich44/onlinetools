import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
CLIENT_ID = "cc_classic_ju7wWOSlsh".strip()
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS6jLCizbf".strip()
MERCHANT_CODE = "MCHYQUG3".strip()
API_KEY = "sup_sk_3pYZm9Maezj1XgpL76qxKvKUc".strip() # The 'sup_sk' key

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

def get_access_token():
    """
    Retrieves an access token.
    Attempts multiple methods to resolve 'invalid_client' errors.
    """
    errors = []

    # Method 1: The exact replication of the client's Go code (Body string + Bearer Header)
    # This is our best bet since the client said it worked in Go.
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        response = requests.post(TOKEN_URL, data=payload_str, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        errors.append(f"Method 1 (Go-style) failed: {response.status_code} {response.text}")
    except Exception as e:
        errors.append(f"Method 1 error: {str(e)}")

    # Method 2: Standard OAuth2 (Client Credentials in Body, no Auth header)
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    try:
        response = requests.post(TOKEN_URL, data=payload)
        if response.status_code == 200:
            return response.json().get("access_token")
        errors.append(f"Method 2 (Body) failed: {response.status_code} {response.text}")
    except Exception as e:
        errors.append(f"Method 2 error: {str(e)}")

    # Method 3: Basic Auth (Client ID/Secret as user/pass)
    # Some older clients or specific configs require this.
    try:
        response = requests.post(
            TOKEN_URL, 
            data={"grant_type": "client_credentials"},
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        errors.append(f"Method 3 (Basic Auth) failed: {response.status_code} {response.text}")
    except Exception as e:
        errors.append(f"Method 3 error: {str(e)}")
    
    # If we get here, all methods failed. Raise an exception with all details.
    raise Exception("Token retrieval failed. Details: " + " | ".join(errors))

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
