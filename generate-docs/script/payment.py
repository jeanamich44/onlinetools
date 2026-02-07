import requests
import uuid
from datetime import datetime, timedelta

CLIENT_ID = "cc_classic_ju7wWOSlsh"
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS6jLCizbf"
MERCHANT_CODE = "MCHYQUG3"

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"


def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    res = requests.post(TOKEN_URL, data=payload, headers=headers)
    res.raise_for_status()

    data = res.json()
    return data["access_token"]


def create_checkout(amount):
    token = get_access_token()

    checkout_ref = str(uuid.uuid4())

    valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"

    payload = {
        "amount": amount,
        "currency": "EUR",
        "checkout_reference": checkout_ref,
        "merchant_code": MERCHANT_CODE,
        "description": "Payment",
        "valid_until": valid_until,
        "redirect_url": "https://google.com",
        "hosted_checkout": {
            "enabled": True
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    res = requests.post(CHECKOUT_URL, json=payload, headers=headers)
    res.raise_for_status()

    data = res.json()
    return data["hosted_checkout_url"]


if __name__ == "__main__":
    link = create_checkout(5)
    print("PAYMENT LINK:", link)
