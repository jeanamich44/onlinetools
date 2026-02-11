import time
import requests
import logging
from sqlalchemy.orm import Session
from .database import Payment, SessionLocal
from .payment importGX get_access_token

logger = logging.getLogger(__name__)

def poll_sumup_status(checkout_id: str):
    """
    Polls SumUp API for payment status updates in the background.
    Runs for up to 5 minutes, checking every 5 seconds.
    Stops if status is PAID or FAILED.
    """
    logger.info(f"Starting background polling for Checkout ID: {checkout_id}")
    
    start_time = time.time()
    timeout = 300 # 5 minutes
    interval = 5   # 5 seconds

    db = SessionLocal() # Create a new session for the background thread

    try:
        while time.time() - start_time < timeout:
            try:
                # 1. Check current status in DB first (in case webhook updated it)
                payment = db.query(Payment).filter(Payment.checkout_id == checkout_id).first()
                if not payment:
                    logger.warning(f"Polling: Payment {checkout_id} not found in DB.")
                    break
                
                if payment.status in ["PAID", "FAILED"]:
                    logger.info(f"Polling: Payment {checkout_id} already finalized: {payment.status}")
                    break

                # 2. Query SumUp API
                token = get_access_token()
                headers = {"Authorization": f"Bearer {token}"}
                url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    new_status = data.get("status")

                    if new_status and new_status != payment.status:
                        logger.info(f"Polling: Status changed for {checkout_id}: {payment.status} -> {new_status}")
                        payment.status = new_status
                        db.commit()
                        
                        if new_status in ["PAID", "FAILED"]:
                            break # We are done
                else:
                    logger.warning(f"Polling: API Error {response.status_code}: {response.text}")

            except Exception as e:
                logger.error(f"Polling Loop Error: {e}")

            time.sleep(interval)
            
    except Exception as e:
        logger.error(f"Polling Fatal Error: {e}")
    finally:
        db.close()
        logger.info(f"Background polling finished for {checkout_id}")
