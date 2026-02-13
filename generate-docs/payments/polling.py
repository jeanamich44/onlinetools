import time
import requests
import logging
from sqlalchemy.orm import Session
from .database import Payment, SessionLocal
from .payment import get_access_token_sync

logger = logging.getLogger(__name__)

def poll_sumup_status(checkout_id: str):
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
        while time.time() - start_time < timeout:
            try:
                # 1. Vérifier le statut actuel en DB d'abord
                payment = db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                if not payment:
                    logger.warning(f"Polling: Paiement {checkout_id} non trouvé en DB.")
                    break
                
                if payment.status in ["PAID", "FAILED"]:
                    logger.info(f"Polling: Paiement {checkout_id} déjà finalisé: {payment.status}")
                    break

                # 2. Interroger l'API SumUp
                # Utiliser la version SYNC car nous sommes dans un thread
                token = get_access_token_sync()
                
                headers = {"Authorization": f"Bearer {token}"}
                url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
                
                # DEBUG TEMPORAIRE
                logger.info(f"[DEBUG] Envoi requête Polling SumUp: {url}")
                
                response = requests.get(url, headers=headers)
                
                # DEBUG TEMPORAIRE
                logger.info(f"[DEBUG] Réponse SumUp ({response.status_code}): {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    new_status = data.get("status")

                    if new_status and new_status != payment.status:
                        logger.info(f"Polling: Statut changé pour {checkout_id}: {payment.status} -> {new_status}")
                        payment.status = new_status
                        db.commit()
                        
                        if new_status in ["PAID", "FAILED"]:
                            break # Terminé
                else:
                    logger.warning(f"Polling: Erreur API {response.status_code}: {response.text}")

            except Exception as e:
                logger.error(f"Erreur Boucle Polling: {e}")

            time.sleep(interval)
            
    except Exception as e:
        logger.error(f"Erreur Fatale Polling: {e}")
    finally:
        db.close()
        logger.info(f"Polling arrière-plan terminé pour {checkout_id}")
