"""
================================================================================
KAFKA PRODUCER FOR BIDDING SERVICE
================================================================================

Publishes events to Kafka when bids are placed, accepted, or rejected.

Why publish events?
1. Other services need to know about bids
2. Fraud Service → Check for suspicious bidding patterns
3. Notification Service → Send SMS to farmer/buyer
4. Analytics → Track bidding activity
5. Payment Service → Create transaction when bid is accepted

================================================================================
"""
import json
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.config import settings
from app.models import Bid
from app.schemas import BidPlacedEvent, BidAcceptedEvent, BidRejectedEvent

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
    Async Kafka producer for bid events.
    
    Publishes events to Kafka topics:
    - bid.placed
    - bid.accepted
    - bid.rejected
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
    
    async def publish_bid_placed(self, bid: Bid):
        """Publish an event when a bid is placed."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = BidPlacedEvent(
            bid_id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
        )
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_bid_placed,
                value=data
            )
            logger.info(f"📤 Published bid.placed: {bid.id} (K{bid.amount})")
        except Exception as e:
            logger.error(f"❌ Failed to publish bid.placed: {str(e)}")
    
    async def publish_bid_accepted(self, bid: Bid, transaction_id: UUID):
        """Publish an event when a bid is accepted."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = BidAcceptedEvent(
            bid_id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
            transaction_id=transaction_id,
        )
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_bid_accepted,
                value=data
            )
            logger.info(f"📤 Published bid.accepted: {bid.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish bid.accepted: {str(e)}")
    
    async def publish_bid_rejected(self, bid: Bid):
        """Publish an event when a bid is rejected."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = BidRejectedEvent(
            bid_id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
        )
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_bid_rejected,
                value=data
            )
            logger.info(f"📤 Published bid.rejected: {bid.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish bid.rejected: {str(e)}")


# Create a singleton instance
kafka_producer = KafkaProducer()
