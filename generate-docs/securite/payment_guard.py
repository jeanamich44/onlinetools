import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from payments.database import Payment, SessionLocal

# Cache en mémoire des IPs bloquées pour un accès instantané
# Ce set est mis à jour par le security_worker en arrière-plan
BLOCKED_IPS = set()

# Compteurs temporaires en mémoire pour bloquer instantanément entre deux tours du worker
TEMP_COUNTERS = {} # { "ip_address": nombre_de_sessions_actives }

logger = logging.getLogger(__name__)

async def security_worker():
    """
    Tâche de fond qui tourne en continu pour surveiller les abus.
    Elle synchronise l'état de la sécurité avec la base de données sans bloquer les requêtes clients.
    """
    logger.info("Démarrage du garde-fou sécuritaire (Background Worker)...")
    while True:
        try:
            # Création d'une session locale dédiée au worker
            db = SessionLocal()
            try:
                # Un paiement SumUp expire après environ 15 minutes
                threshold = datetime.utcnow() - timedelta(minutes=15)
                
                # Requête optimisée : on groupe par IP et on ne garde que celles qui ont >= 2 paiements PENDING
                results = db.query(Payment.ip_address).filter(
                    Payment.status == "PENDING",
                    Payment.created_at > threshold
                ).group_by(Payment.ip_address).having(func.count(Payment.id) >= 2).all()
                
                # Mise à jour de la mémoire globale
                global BLOCKED_IPS, TEMP_COUNTERS
                BLOCKED_IPS = {r[0] for r in results if r[0]}
                
                # On réinitialise les compteurs temporaires à chaque tour de "vérité" de la base de données
                TEMP_COUNTERS = {}
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur de synchronisation sécurité: {e}")
            
        # On vérifie toutes les 5 secondes pour un bon compromis réactivité/performance
        await asyncio.sleep(5)

def is_payment_allowed_fast(ip_address: str) -> bool:
    """
    Vérification ultra-rapide en mémoire (O(1)).
    Combine la liste noire du worker et les tentatives en cours.
    """
    # 1. Bloqué si le worker a détecté trop de paiements en DB
    if ip_address in BLOCKED_IPS:
        return False
        
    # 2. Bloqué si le compteur temporaire (temps réel) a atteint 2
    if TEMP_COUNTERS.get(ip_address, 0) >= 2:
        return False
        
    return True

def increment_payment_counter(ip_address: str):
    """
    Incrémente instantanément le compteur en mémoire pour cette IP.
    """
    global TEMP_COUNTERS
    TEMP_COUNTERS[ip_address] = TEMP_COUNTERS.get(ip_address, 0) + 1
