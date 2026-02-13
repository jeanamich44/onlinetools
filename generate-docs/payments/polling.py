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
    logger.info(f"Démarrage polling arrière-plan pour Checkout ID: {checkout_id}")
    
    start_time = time.time()
    timeout = 900 
    
    try:
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                try:
                    # 1. Obtenir une session courte uniquement pour cette vérifications
                    db = SessionLocal()
                    try:
                        payment = db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                        
                        if not payment:
                            logger.warning(f"Polling: Paiement {checkout_id} non trouvé en DB. Attente...")
                            await asyncio.sleep(2)
                            continue
                        
                        if payment.status in ["PAID", "FAILED"]:
                            logger.info(f"Polling: Paiement {checkout_id} déjà finalisé: {payment.status}")
                            break

                        # 2. Interroger l'API SumUp EN DEHORS d'un bloc de commit
                        token = await get_access_token()
                        headers = {"Authorization": f"Bearer {token}"}
                        url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
                        
                        async with session.get(url, headers=headers) as response:
                            status_code = response.status
                            
                            if status_code == 200:
                                data = await response.json()
                                new_status = data.get("status")

                                if new_status and new_status != payment.status:
                                    logger.info(f"Changement de statut pour {checkout_id}: {payment.status} -> {new_status}")
                                    
                                    payment.status = new_status
                                    db.commit()
                                    
                                    if new_status in ["PAID", "FAILED"]:
                                        break # Terminé
                            else:
                                logger.warning(f"Erreur polling API {checkout_id}: {status_code}")
                    
                    finally:
                        db.close() # CRITIQUE : Libère la connexion immédiatement

                except Exception as e:
                    logger.error(f"Erreur Boucle Polling: {e}")

                # Intervalle dynamique
                elapsed = time.time() - start_time
                if elapsed <= 60:
                    current_interval = 1
                elif elapsed <= 180:
                    current_interval = 5
                else:
                    current_interval = 15
                    
                await asyncio.sleep(current_interval)
            
    except Exception as e:
        logger.error(f"Erreur Fatale Polling: {e}")
    finally:
        logger.info(f"Polling arrière-plan terminé pour {checkout_id}")
