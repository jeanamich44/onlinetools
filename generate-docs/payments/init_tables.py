import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

try:
    from .database import init_db, engine
    logger.info("🔄 Tentative de connexion à la base de données...")
    
    url_str = str(engine.url)
    if '@' in url_str:
        masked_url = url_str.replace(url_str.split('@')[0], '****')
    else:
        masked_url = url_str
        
    logger.info(f"URL (masked): {masked_url}")
    
    logger.info("🛠️ Création des tables...")
    init_db()
    logger.info("✅ Tables créées avec succès !")
except Exception as e:
    logger.error(f"❌ Erreur lors de l'initialisation : {e}")
