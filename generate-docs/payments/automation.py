import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

async def trigger_automatic_generation(payment, db=None):
    """
    Déclenche automatiquement la génération ou l'envoi de documents 
    dès qu'un paiement est marqué comme PAID, si nécessaire.
    """
    if not payment or payment.status != "PAID" or payment.is_generated:
        return False

    try:
        user_data = json.loads(payment.user_data)
        type_pdf = user_data.get("type_pdf")
        
        # Cas spécifique Chronopost : On appelle l'API de génération externe
        if type_pdf and type_pdf.startswith("chrono"):
            logger.info(f"Déclenchement automatique Chronopost pour {payment.checkout_ref}")
            
            chrono_api_url = "https://chronopost.up.railway.app/generate-chronopost/generate-chronopost"
            payload = {"data": user_data}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(chrono_api_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        if res_json.get("status") == "success":
                            logger.info(f"Génération automatique réussie pour {payment.checkout_ref}")
                            payment.is_generated = 1
                            if db: db.commit()
                            return True
                        else:
                            logger.error(f"Echec génération automatique Chronopost: {res_json.get('message')}")
                    else:
                        text = await response.text()
                        logger.error(f"Erreur API Chronopost ({response.status}): {text}")
        
        # --- NOUVEAU : Automatisation pour RIB, Factures, Assurance ---
        elif type_pdf:
            logger.info(f"Déclenchement génération automatique (Arrière-plan) pour {type_pdf} - Ref: {payment.checkout_ref}")
            
            # Imports locaux pour éviter les cycles
            from main import GENERATORS, PDFRequest
            import os
            
            # Dossier de stockage
            storage_dir = "paid_pdfs"
            os.makedirs(storage_dir, exist_ok=True)
            output_path = os.path.join(storage_dir, f"{payment.checkout_ref}.pdf")
            
            data_obj = PDFRequest(**user_data)
            
            if type_pdf in GENERATORS:
                try:
                    # Génération physique du fichier sur le serveur
                    GENERATORS[type_pdf](data_obj, output_path)
                    
                    if os.path.exists(output_path):
                        logger.info(f"PDF généré et stocké localement: {output_path}")
                        payment.is_generated = 1
                        if db:
                            db.commit()
                        return True
                    else:
                        logger.error(f"Échec de création du fichier PDF pour {payment.checkout_ref}")
                except Exception as gen_err:
                    logger.error(f"Erreur lors de la génération PDF ({type_pdf}): {gen_err}")
        
    except Exception as e:
        logger.error(f"Erreur lors du trigger d'automatisation: {e}")
    
    return False
