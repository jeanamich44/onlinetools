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
                    # On le fait dans un thread car c'est synchrone
                    loop = asyncio.get_event_loop()
                    payment = await loop.run_in_executor(
                        None, 
                        lambda: db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                    )

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
                                
                                # Mise à jour dans un thread
                                def update_status_db():
                                    payment.status = new_status
                                    db.commit()
                                
                                await loop.run_in_executor(None, update_status_db)
                                
                                if new_status in ["PAID", "FAILED"]:
                                    break # Terminé
                        else:
                            logger.warning(f"Polling: Erreur API {response.status}: {response_text}")

                except Exception as e:
                    logger.error(f"Erreur Boucle Polling: {e}")

                await asyncio.sleep(interval)
            
    except Exception as e:
        logger.error(f"Erreur Fatale Polling: {e}")
    finally:
        db.close()
        logger.info(f"Polling arrière-plan terminé pour {checkout_id}")
