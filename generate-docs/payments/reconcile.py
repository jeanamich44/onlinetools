import asyncio
import aiohttp
import time
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
    logger.info("Démarrage de la réconciliation globale (ASYNCHRONE) des paiements PENDING & FAILED...")
    
    # On utilise SessionLocal() dans un bloc contextuel pour assurer la fermeture
    try:
        # 1. Récupérer les IDs des paiements PENDING & FAILED (Session courte)
        db = SessionLocal()
        try:
            pending_payments_data = db.query(Payment.checkout_id, Payment.status).filter(Payment.status.in_(["PENDING", "FAILED"])).all()
        finally:
            db.close()
            
        if not pending_payments_data:
            logger.info("Aucun paiement PENDING ou FAILED à réconcilier.")
            return

        logger.info(f"Réconciliation : {len(pending_payments_data)} paiements (PENDING/FAILED) à vérifier.")

        token = await get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            for checkout_id, current_status in pending_payments_data:
                try:
                    url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            new_status = data.get("status")
                            
                            if new_status and new_status != current_status:
                                logger.info(f"Réconciliation : {checkout_id} -> {new_status}")
                                
                                # Mise à jour (Session courte)
                                db_update = SessionLocal()
                                try:
                                    p = db_update.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                                    if p:
                                        p.status = new_status
                                        db_update.commit()
                                        
                                        if new_status == "PAID" and not p.is_generated:
                                            from .automation import trigger_automatic_generation
                                            await trigger_automatic_generation(p, db=db_update)
                                finally:
                                    db_update.close()
                        else:
                            text = await response.text()
                            logger.warning(f"Réconciliation : Erreur API pour {checkout_id} ({response.status})")
                
                except Exception as e:
                    logger.error(f"Erreur réconciliation pour {checkout_id}: {e}")
                
        logger.info("Réconciliation globale terminée.")
        
    except Exception as e:
        logger.error(f"Erreur lors de la réconciliation globale : {e}")

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
