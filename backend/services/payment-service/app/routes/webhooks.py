"""
================================================================================
FLUTTERWAVE WEBHOOKS
================================================================================

This file handles incoming webhooks from Flutterwave.
"""
import json
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import PaymentStatus
from app.crud import update_transaction_status, get_transaction
from app.kafka_producer import kafka_producer
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(
    request: Request,
    verif_hash: str = Header(None, alias="verif-hash"),
):
    """
    Handle Flutterwave webhook.
    
    Security:
        1. Verify the webhook signature using the Secret Hash
        2. Validate the request is from Flutterwave
    """
    try:
        # Get the raw body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # ====================================================================
        # VERIFY WEBHOOK SIGNATURE
        # ====================================================================
        if not settings.flutterwave_webhook_secret:
            logger.warning("⚠️ FLUTTERWAVE_WEBHOOK_SECRET not set. Skipping verification.")
        else:
            expected_signature = hmac.new(
                settings.flutterwave_webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not verif_hash or verif_hash != expected_signature:
                logger.error(f"❌ Invalid webhook signature: {verif_hash}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            logger.info("✅ Webhook signature verified")
        
        # Parse the webhook data
        data = json.loads(body_str)
        logger.info(f"📩 Flutterwave webhook received: {data}")
        
        event = data.get("event")
        event_data = data.get("data", {})
        
        # ====================================================================
        # HANDLE CHARGE COMPLETED (Payment success)
        # ====================================================================
        if event == "charge.completed":
            flutterwave_ref = event_data.get("flw_ref")
            tx_ref = event_data.get("tx_ref")
            status_value = event_data.get("status")
            amount = event_data.get("amount")
            
            logger.info(f"💰 Payment completed: {flutterwave_ref}, Status: {status_value}, tx_ref: {tx_ref}")
            
            if status_value == "successful":
                # Get a database session
                db = next(await get_db())
                
                try:
                    # Try to find transaction by tx_ref or flutterwave_ref
                    from app.models import Transaction
                    from sqlalchemy import select
                    
                    # First try by flutterwave_reference
                    query = select(Transaction).where(Transaction.flutterwave_reference == flutterwave_ref)
                    result = await db.execute(query)
                    transaction = result.scalar_one_or_none()
                    
                    # If not found, try by tx_ref (which should be the transaction ID)
                    if not transaction and tx_ref:
                        try:
                            from uuid import UUID
                            tx_uuid = UUID(tx_ref)
                            transaction = await get_transaction(db, tx_uuid)
                        except ValueError:
                            pass
                    
                    if transaction:
                        # Update transaction status
                        await update_transaction_status(
                            db=db,
                            transaction_id=transaction.id,
                            status=PaymentStatus.PAID_ESCROW,
                            flutterwave_reference=flutterwave_ref,
                            extra_data={"webhook": data},
                        )
                        logger.info(f"✅ Transaction {transaction.id} updated to paid_escrow")
                        
                        # Publish event
                        await kafka_producer.publish_payment_completed(transaction)
                    else:
                        logger.warning(f"⚠️ No transaction found for ref: {flutterwave_ref} or tx_ref: {tx_ref}")
                        
                finally:
                    await db.close()
            
            return {"status": "received"}
        
        elif event == "transfer.completed":
            flutterwave_ref = event_data.get("reference")
            status_value = event_data.get("status")
            amount = event_data.get("amount")
            
            logger.info(f"💸 Transfer completed: {flutterwave_ref}, Status: {status_value}")
            
            return {"status": "received"}
        
        else:
            logger.info(f"ℹ️ Unhandled webhook event: {event}")
            return {"status": "ignored"}
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
