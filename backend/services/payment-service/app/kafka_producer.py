"""
================================================================================
KAFKA PRODUCER FOR PAYMENT SERVICE
================================================================================

Publishes events to Kafka when payment actions occur.

Events:
1. payment.initiated → When a payment is initiated
2. payment.completed → When payment is confirmed and in escrow
3. payout.released → When funds are released to farmer

Why events?
- Notification Service → Send SMS/email to buyer and farmer
- Analytics → Track payment volume
- Fraud Service → Monitor suspicious transactions
- Audit → Complete audit trail

================================================================================
"""
import json
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.config import settings
from app.models import Transaction

logger = logging.getLogger(__name__)

# Try to import aiokafka, but don't fail if not available
try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
    logger.info("✅ Kafka is available")
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("⚠️ Kafka not available. Events will not be published.")


class KafkaProducer:
    """
    Async Kafka producer for payment events.
    """
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.enabled = KAFKA_AVAILABLE
    
    async def connect(self):
        """Connect to Kafka."""
        if not self.enabled or self.producer:
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                compression_type='gzip',
            )
            await self.producer.start()
            logger.info(f"✅ Connected to Kafka at {settings.kafka_bootstrap_servers}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {str(e)}")
            self.enabled = False
    
    async def disconnect(self):
        """Disconnect from Kafka."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
    
    async def publish_payment_initiated(self, transaction: Transaction):
        """Publish when a payment is initiated."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = {
            "event_type": "payment.initiated",
            "transaction_id": str(transaction.id),
            "bid_id": str(transaction.bid_id),
            "buyer_id": str(transaction.buyer_id),
            "farmer_id": str(transaction.farmer_id),
            "amount": transaction.amount,
            "status": transaction.status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            await self.producer.send(
                topic=settings.kafka_topic_payment_initiated,
                value=event
            )
            logger.info(f"📤 Published payment.initiated: {transaction.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish payment.initiated: {str(e)}")
    
    async def publish_payment_completed(self, transaction: Transaction):
        """Publish when payment is completed (in escrow)."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = {
            "event_type": "payment.completed",
            "transaction_id": str(transaction.id),
            "bid_id": str(transaction.bid_id),
            "buyer_id": str(transaction.buyer_id),
            "farmer_id": str(transaction.farmer_id),
            "amount": transaction.amount,
            "flutterwave_reference": transaction.flutterwave_reference,
            "status": transaction.status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            await self.producer.send(
                topic=settings.kafka_topic_payment_completed,
                value=event
            )
            logger.info(f"📤 Published payment.completed: {transaction.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish payment.completed: {str(e)}")
    
    async def publish_payout_released(self, transaction: Transaction):
        """Publish when payout is released to farmer."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = {
            "event_type": "payout.released",
            "transaction_id": str(transaction.id),
            "bid_id": str(transaction.bid_id),
            "buyer_id": str(transaction.buyer_id),
            "farmer_id": str(transaction.farmer_id),
            "amount": transaction.farmer_payout,
            "platform_fee": transaction.platform_fee,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            await self.producer.send(
                topic=settings.kafka_topic_payout_released,
                value=event
            )
            logger.info(f"📤 Published payout.released: {transaction.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish payout.released: {str(e)}")


# Create a singleton instance
kafka_producer = KafkaProducer()
