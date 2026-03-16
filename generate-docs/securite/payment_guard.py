import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from payments.database import Payment, SessionLocal

BLOCKED_IPS = set()

TEMP_COUNTERS = {}

logger = logging.getLogger(__name__)

async def security_worker():
    logger.info("Démarrage du garde-fou sécuritaire (Background Worker)...")
    while True:
        try:
            db = SessionLocal()
            try:
                threshold = datetime.utcnow() - timedelta(minutes=15)
                
                results = db.query(Payment.ip_address).filter(
                    Payment.status == "PENDING",
                    Payment.created_at > threshold
                ).group_by(Payment.ip_address).having(func.count(Payment.id) >= 2).all()
                
                BLOCKED_IPS = {r[0] for r in results if r[0]}
                
                TEMP_COUNTERS = {}
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur de synchronisation sécurité: {e}")
            
        await asyncio.sleep(5)

def is_payment_allowed_fast(ip_address: str) -> bool:
    if ip_address in BLOCKED_IPS:
        return False
        
    if TEMP_COUNTERS.get(ip_address, 0) >= 2:
        return False
        
    return True

def increment_payment_counter(ip_address: str):
    global TEMP_COUNTERS
    TEMP_COUNTERS[ip_address] = TEMP_COUNTERS.get(ip_address, 0) + 1
