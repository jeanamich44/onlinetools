import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration (Hardcoded for now as requested)
CLIENT_ID = "cc_classic_ju7wWOSlsh"
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS6jLCizbf"
MERCHANT_CODE = "MCHYQUG3"
TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

def get_access_token():
    """Retrieves an access token from SumUp API using client credentials."""
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    # The documentation for client_credentials flow usually just requires client_id/secret in body 
    # OR Basic Auth header. The Go code setup is a bit specific. 
    # Verification: In the Go code:
    # req1.Header.Set("Authorization", "Bearer sup_sk_3pYZm9Maezj1XgpL76qxKvKUc")
    # This looks like an initial bearer token or a mix-up. 
    # However, standard OAuth2 client_credentials usually works with just    # The previous attempt failed with "invalid_client". 
    # This often means the client_id/secret are not being read correctly from the body 
    # or the endpoint expects them in the Authorization header (Basic Auth).
    #
    # Standard OAuth2 allows sending client credentials in the Authorization header.
    # We will try sending them as Basic Auth.
    
    payload = {
        "grant_type": "client_credentials"
    }
    
    # requests.post(..., auth=(user, pass)) automatically adds the Basic Auth header
    response = requests.post(
        TOKEN_URL, 
        data=payload, 
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Include the response body in the error message for debugging
        raise Exception(f"Failed to get token: {e}. Body: {response.text}") from e
        
    return response.json().get("access_token")

def create_checkout(amount=1.0, currency="EUR", email=None):
    """Creates a checkout session and returns the payment URL."""
    token = get_access_token()
    if not token:
        raise Exception("Failed to retrieve access token")

    checkout_ref = str(uuid.uuid4())
    
    # Valid until 15 minutes from now (ISO 8601 format)
    # Go code used: future.Format(time.RFC3339) which produces "2006-01-02T15:04:05Z07:00"
    valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"

    payload = {
        "amount": amount,
        "currency": currency,
        "checkout_reference": checkout_ref,
        "merchant_code": MERCHANT_CODE,
        "description": "Payment for OnlineTools service",
        "valid_until": valid_until,
        "redirect_url": "https://google.com",  # Placeholder as in Go code
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
    response.raise_for_status()
    
    data = response.json()
    return data.get("hosted_checkout_url")
