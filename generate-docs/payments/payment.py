import aiohttp
import asyncio
import os
import uuid
import time
import logging
from datetime import datetime, timedelta

# Configuration
CLIENT_ID = "cc_classic_ju7wWXPLFWeNtFgwerzub54kOSlsh".strip()
CLIENT_SECRET = "cc_sk_classic_zGdCSOq3BzS2lPsVFmKZHpQKI8fwt8V6zoIFQLqpl46jLCizbf".strip()
# CODE_MARCHAND = "MCHYQUG3".strip() # Invalide
PAY_TO_EMAIL = "dupuisrenov83@outlook.fr"
API_KEY = "sup_sk_3pYZm9Maezj1XgpL76qxKvKUc".strip() 

TOKEN_URL = "https://api.sumup.com/token"
CHECKOUT_URL = "https://api.sumup.com/v0.1/checkouts"

from .database import Payment
from sqlalchemy.orm import Session

import logging
logger = logging.getLogger(__name__)

# Cache de Token
_token_cache = {
    "access_token": None,
    "expires_at": 0 # Timestamp
}

async def get_access_token():
    """
    Récupère un token d'accès de manière asynchrone, en utilisant un cache global.
    """
    global _token_cache
    
    # Vérifier si on a un token valide
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    # Méthode 1: Corps + En-tête Bearer (Confirmé fonctionnel en debug)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(TOKEN_URL, data=payload_str, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600) # Par défaut 1h
                    
                    # Mettre à jour le cache 
                    _token_cache["access_token"] = token
                    _token_cache["expires_at"] = time.time() + expires_in - 60
                    
                    logger.info("🔑 Nouveau Token d'accès SumUp récupéré (Async).")
                    return token
                
                text = await response.text()
                logger.error(f"Echec Auth Token: {response.status} {text}")
                raise Exception(f"Echec Auth Token: {response.status} {text}")

    except Exception as e:
        raise Exception(f"Erreur Récupération Token: {str(e)}")

def get_access_token_sync():
    """
    Récupère un token d'accès de manière synchrone (pour le polling).
    """
    global _token_cache
    
    # Vérifier si on a un token valide
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload_str = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        import requests
        response = requests.post(TOKEN_URL, data=payload_str, headers=headers)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            expires_in = data.get("expires_in", 3600) # Par défaut 1h
            
            # Mettre à jour le cache 
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = time.time() + expires_in - 60
            
            logger.info("🔑 Nouveau Token d'accès SumUp récupéré (Sync).")
            return token
        
        logger.error(f"Echec Auth Token (Sync): {response.status_code} {response.text}")
        raise Exception(f"Echec Auth Token (Sync): {response.status_code} {response.text}")

    except Exception as e:
        raise Exception(f"Erreur Récupération Token (Sync): {str(e)}")


async def create_checkout(db_session_unused: Session, amount=1.0, currency="EUR", ip_address=None, product_name=None):
    """
    Crée une session de paiement.
    Nouveau flux : Insertion DB immédiate -> Appel API SumUp -> Mise à jour DB.
    """
    # 1. Générer une référence locale
    checkout_ref = str(uuid.uuid4())
    logger.info(f"Début création paiement: Ref={checkout_ref}")
    
    # 2. Insertion DB immédiate (Session indépendante pour commit instantané)
    db = SessionLocal()
    try:
        start_init = time.time()
        new_payment = Payment(
            checkout_ref=checkout_ref,
            amount=amount,
            currency=currency,
            status="PRE_API", # Statut temporaire
            ip_address=ip_address,
            product_name=product_name
        )
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment) # On récupère l'ID pour être sûr
        db_id = new_payment.id
        logger.info(f"DB Pre-insertion OK (ID={db_id}) en {time.time()-start_init:.3f}s")
        
        # 3. Appel API SumUp
        token = await get_access_token()
        valid_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"
        APP_DOMAIN = "https://generate-docs-production.up.railway.app"
        
        payload = {
            "amount": amount,
            "currency": currency,
            "checkout_reference": checkout_ref,
            "pay_to_email": PAY_TO_EMAIL,
            "description": f"Payment Ref: {checkout_ref}", 
            "valid_until": valid_until,
            "redirect_url": f"{APP_DOMAIN}/payment-success?checkout_reference={checkout_ref}",
            "hosted_checkout": {"enabled": True}
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            logger.info(f"Appel API SumUp...")
            async with session.post(CHECKOUT_URL, json=payload, headers=headers) as response:
                status_code = response.status
                if status_code >= 400:
                    text = await response.text()
                    logger.error(f"Echec API SumUp ({status_code}): {text}")
                    # On marque en FAILED en base avant de lever l'erreur
                    new_payment.status = "API_ERROR"
                    db.commit()
                    raise Exception(f"Echec Checkout: {status_code} {text}")
                    
                data = await response.json()
                checkout_id = data.get("id")
                payment_url = data.get("hosted_checkout_url")
                
                # 4. Mise à jour finale
                start_update = time.time()
                new_payment.checkout_id = checkout_id
                new_payment.payment_url = payment_url
                new_payment.status = "PENDING"
                db.commit()
                logger.info(f"DB Update SUCCESS: {checkout_id} enregistré en {time.time()-start_update:.3f}s")
                
                return (payment_url, checkout_ref, checkout_id)

    except Exception as e:
        logger.error(f"Erreur globale create_checkout: {e}")
        db.rollback()
        raise e
    finally:
        db.close()
