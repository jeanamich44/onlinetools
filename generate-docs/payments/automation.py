import aiohttp
import json
import logging
import os

logger = logging.getLogger(__name__)

async def trigger_automatic_generation(payment, db=None):
    if not payment or payment.status != "PAID" or payment.is_generated:
        return False

    try:
        user_data = json.loads(payment.user_data)
        type_pdf = user_data.get("type_pdf")
        
        if type_pdf and type_pdf.startswith("chrono"):
            logger.info(f"Déclenchement automatique Chronopost pour {payment.checkout_ref}")
            
            chrono_api_url = "https://transporteur.up.railway.app/generate/chronopost"
            payload = {"data": user_data}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(chrono_api_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        if res_json.get("status") == "success":
                            logger.info(f"Génération automatique réussie pour {payment.checkout_ref}")
                            
                            storage_dir = "paid_pdfs"
                            os.makedirs(storage_dir, exist_ok=True)
                            output_path = os.path.join(storage_dir, f"{payment.checkout_ref}.pdf")
                            
                            pdfs_to_merge = []
                            import base64
                            from io import BytesIO
                            import PyPDF2
                            
                            for key in ["label", "proforma", "cn23"]:
                                b64_str = res_json.get(key)
                                if b64_str:
                                    try:
                                        pdfs_to_merge.append(BytesIO(base64.b64decode(b64_str)))
                                    except Exception as e:
                                        logger.error(f"Erreur décodage base64 pour {key}: {e}")

                            if pdfs_to_merge:
                                try:
                                    if len(pdfs_to_merge) == 1:
                                        with open(output_path, "wb") as f:
                                            f.write(pdfs_to_merge[0].getvalue())
                                    else:
                                        import PyPDF2
                                        merger = PyPDF2.PdfMerger()
                                        for pdf in pdfs_to_merge:
                                            try:
                                                merger.append(pdf)
                                            except Exception as append_err:
                                                logger.error(f"Erreur fusion PDF partiel: {append_err}")
                                        with open(output_path, "wb") as f:
                                            merger.write(f)
                                        merger.close()
                                    
                                    payment.is_generated = 1
                                    if db: db.commit()
                                    logger.info(f"PDF sauvegardé pour {payment.checkout_ref} dans {output_path}")
                                    return True
                                except Exception as e:
                                    logger.error(f"Erreur de sauvegarde finale du PDF: {e}")
                            else:
                                logger.error(f"API Transporteur SUCCESS mais aucun PDF (label/proforma) reçu pour {payment.checkout_ref}")
                            
                            return False
                        else:
                            logger.error(f"Echec génération automatique ({type_pdf}): {res_json.get('message')}")
                    else:
                        text = await response.text()
                        logger.error(f"Erreur API Externe ({response.status}): {text}")
        
        elif type_pdf:
            logger.info(f"Déclenchement génération automatique (Arrière-plan) pour {type_pdf} - Ref: {payment.checkout_ref}")
            
            from main import GENERATORS, PDFRequest
            
            storage_dir = "paid_pdfs"
            os.makedirs(storage_dir, exist_ok=True)
            output_path = os.path.join(storage_dir, f"{payment.checkout_ref}.pdf")
            
            data_obj = PDFRequest(**user_data)
            
            if type_pdf in GENERATORS:
                try:
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
