import asyncio
import aiohttp
import logging
from sqlalchemy.orm import Session
from .database import Payment, SessionLocal
from .payment import get_access_token

logger = logging.getLogger(__name__)

async def reconcile_all_pending_payments():
    """
    Parcourt tous les paiements PENDING en base et vérifie leur statut réel chez SumUp.
    Version asynchrone pour ne pas bloquer les autres processus.
    """
    logger.info("Démarrage de la réconciliation globale (ASYNCHRONE) des paiements PENDING...")
    
    # On utilise SessionLocal() dans un bloc contextuel pour assurer la fermeture
    db = SessionLocal()
    try:
        # Récupérer tous les paiements marqués PENDING
        # On exécute la requête synchrone dans un thread
        loop = asyncio.get_event_loop()
        pending_payments = await loop.run_in_executor(
            None, 
            lambda: db.query(Payment).filter(Payment.status == "PENDING").all()
        )
        
        if not pending_payments:
            logger.info("Aucun paiement PENDING à réconcilier.")
            return

        token = await get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            for p in pending_payments:
                try:
                    CHECKOUT_URL = f"https://api.sumup.com/v0.1/checkouts/{p.checkout_id}"
                    async with session.get(CHECKOUT_URL, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            new_status = data.get("status")
                            
                            if new_status and new_status != p.status:
                                logger.info(f"Réconciliation : {p.checkout_id} passé de {p.status} à {new_status}")
                                
                                # Mise à jour synchrone dans un thread
                                def do_update(payment_obj, status):
                                    payment_obj.status = status
                                    db.commit()
                                
                                await loop.run_in_executor(None, do_update, p, new_status)
                        else:
                            text = await response.text()
                            logger.warning(f"Réconciliation : Impossible de vérifier {p.checkout_id} (Code {response.status}): {text}")
                
                except Exception as e:
                    logger.error(f"Erreur réconciliation pour {p.checkout_id}: {e}")
                
        logger.info("Réconciliation globale terminée.")
        
    except Exception as e:
        logger.error(f"Erreur lors de la réconciliation globale : {e}")
    finally:
        db.close()

async def start_reconciliation_loop(interval: int = 300):
    """
    Boucle infinie de réconciliation.
    """
    while True:
        try:
            await reconcile_all_pending_payments()
        except Exception as e:
            logger.error(f"Boucle réconciliation interrompue par une erreur: {e}")
        
        await asyncio.sleep(interval)
