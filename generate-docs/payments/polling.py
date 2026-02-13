import asyncio
import aiohttp
import time
import requests
import logging
from sqlalchemy.orm import Session
from .database import Payment, SessionLocal
from .payment import get_access_token, get_access_token_sync

logger = logging.getLogger(__name__)

async def poll_sumup_status(checkout_id: str):
    """
    Sonde l'API SumUp pour les mises à jour de statut de paiement en arrière-plan (thread synchrone).
    S'exécute pendant jusqu'à 5 minutes, vérifie toutes les 5 secondes.
    S'arrête si le statut est PAID ou FAILED.
    """
    logger.info(f"Démarrage polling arrière-plan pour Checkout ID: {checkout_id}")
    
    start_time = time.time()
    timeout = 900 
    interval = 1   # 1 seconde (Vérification ultra-rapide)

    db = SessionLocal() # Créer une nouvelle session pour le thread
    
    try:
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                try:
                    # 1. Vérifier le statut actuel en DB d'abord
                    start_q = time.time()
                    payment = db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                    q_duration = time.time() - start_q
                    
                    if q_duration > 1.0:
                        logger.warning(f"DB Query SLOW: {q_duration:.3f}s pour {checkout_id}")

                    if not payment:
                        logger.warning(f"Polling: Paiement {checkout_id} non trouvé en DB.")
                        break
                    
                    if payment.status in ["PAID", "FAILED"]:
                        logger.info(f"Polling: Paiement {checkout_id} déjà finalisé: {payment.status}")
                        break

                    # 2. Interroger l'API SumUp
                    token = await get_access_token()
                    
                    headers = {"Authorization": f"Bearer {token}"}
                    url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
                    
                    # DEBUG TEMPORAIRE
                    logger.info(f"[DEBUG] Envoi requête Polling SumUp: {url}")
                    
                    async with session.get(url, headers=headers) as response:
                        response_text = await response.text()
                        # DEBUG TEMPORAIRE
                        logger.info(f"[DEBUG] Réponse SumUp ({response.status}): {response_text}")
                        
                        if response.status == 200:
                            data = await response.json()
                            new_status = data.get("status")

                            if new_status and new_status != payment.status:
                                logger.info(f"Polling: Statut changé pour {checkout_id}: {payment.status} -> {new_status}")
                                
                            if new_status and new_status != payment.status:
                                old_status = payment.status
                                logger.info(f"Polling: Statut changé pour {checkout_id}: {old_status} -> {new_status}")
                                
                                # Mise à jour synchrone sécurisée
                                start_db = time.time()
                                payment.status = new_status
                                db.commit()
                                db_duration = time.time() - start_db
                                logger.info(f"DB Update (Polling): Succès en {db_duration:.3f}s pour {checkout_id}")
                                
                                if new_status in ["PAID", "FAILED"]:
                                    break # Terminé
                        else:
                            logger.warning(f"Polling: Erreur API {response.status}: {response_text}")

                except Exception as e:
                    logger.error(f"Erreur Boucle Polling: {e}")

                # Intervalle dynamique : 1s pendant 60s, puis 5s
                elapsed = time.time() - start_time
                current_interval = 1 if elapsed <= 60 else 5
                await asyncio.sleep(current_interval)
            
    except Exception as e:
        logger.error(f"Erreur Fatale Polling: {e}")
    finally:
        db.close()
        logger.info(f"Polling arrière-plan terminé pour {checkout_id}")
