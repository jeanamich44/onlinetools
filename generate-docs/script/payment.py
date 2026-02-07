import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
CLIENT_ID = "cc_classic_ju7wWOSlsh"
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS6jLCizbf"
MERCHANT_CODE = "MCHYQUG3"
API_KEY = "sup_sk_3pYZm9Maezj1XgpL76qxKvKUc" # The 'sup_sk' key

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

def get_access_token():
    """
    Retrieves an access token.
    Attempts multiple methods to resolve 'invalid_client' errors.
    """
    
    # Method 1: Standard OAuth2 (Client Credentials in Body, no Auth header)
    # This is the most common way to fix 'invalid_client' if Basic Auth fails.
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    # Note: We explicitly DO NOT send the Authorization header here first,
    # as mixing them can cause conflicts.
    response = requests.post(TOKEN_URL, data=payload)
    
    if response.status_code == 200:
        return response.json().get("access_token")
        
    print(f"Method 1 failed: {response.status_code} {response.text}")

    # Method 2: The exact replication of the Go code (Body string + Bearer Header)
    # Go code used: req1.Header.Set("Authorization", "Bearer sup_sk_...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # Manually construct string to ensure no encoding differences
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    response = requests.post(TOKEN_URL, data=payload_str, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")

    print(f"Method 2 failed: {response.status_code} {response.text}")
    
    # If both fail, we will try to use the API_KEY directly as the token
    # This isn't a "token retrieval" success, but we return None to signal fallback
    return None

def create_checkout(amount=1.0, currency="EUR", email=None):
    """Creates a checkout session and returns the payment URL."""
    
    # Try to get a token
    token = get_access_token()
    
    # If token retrieval failed, fallback to using the API Key directly
    if not token:
        print("Falling back to using API Key directly as Bearer token.")
        token = API_KEY

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
