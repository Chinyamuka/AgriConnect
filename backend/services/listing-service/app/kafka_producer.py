"""
================================================================================
KAFKA PRODUCER FOR LISTING SERVICE
================================================================================

Publishes events to Kafka when listings are created, updated, or expired.

Why publish events?
1. Other services need to know about listings
2. Fraud Service → Check for suspicious listings
3. Price Index → Update market prices
4. Analytics → Track listing activity
5. Notifications → Alert buyers

Event Types:
1. listing.created → When a new listing is created
2. listing.updated → When a listing is updated
3. listing.expired → When a listing expires

================================================================================
"""
import json
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.config import settings
from app.models import Listing
from app.schemas import ListingCreatedEvent, ListingUpdatedEvent, ListingExpiredEvent

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
    Async Kafka producer for listing events.
    
    Publishes events to Kafka topics:
    - listing.created
    - listing.updated
    - listing.expired
    
    Why use Kafka?
    1. Asynchronous communication (services don't wait)
    2. Decoupled services (services don't know about each other)
    3. Reliable (messages are persisted)
    4. Scalable (can have multiple consumers)
    5. Ordered (messages in order per partition)
    """
    
    def __init__(self):
        """Initialize the Kafka producer."""
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
                max_batch_size=16384,
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
            logger.info("✅ Disconnected from Kafka")
    
    async def publish_listing_created(self, listing: Listing):
        """
        Publish an event when a listing is created.
        
        Why:
        - Fraud Service checks for price anomalies
        - Price Index updates market averages
        - Analytics tracks listing activity
        - Notifications alert interested buyers
        """
        if not self.enabled:
            logger.debug(f"📤 Skipping Kafka publish (disabled): listing {listing.id}")
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        # Create event
        event = ListingCreatedEvent(
            listing_id=listing.id,
            farmer_id=listing.farmer_id,
            produce_type=listing.produce_type,
            quantity=listing.quantity,
            unit=listing.unit,
            price=listing.price,
            district=listing.district,
            province=listing.province,
            latitude=listing.location.x if hasattr(listing.location, 'x') else 0,
            longitude=listing.location.y if hasattr(listing.location, 'y') else 0,
        )
        
        try:
            # Convert to dict and publish
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_listing_created,
                value=data
            )
            logger.info(f"📤 Published listing.created: {listing.id} ({listing.produce_type})")
        except Exception as e:
            logger.error(f"❌ Failed to publish listing.created: {str(e)}")
    
    async def publish_listing_updated(self, listing: Listing, changes: dict):
        """
        Publish an event when a listing is updated.
        
        Why:
        - Fraud Service re-checks if price changed
        - Search index updates
        """
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = ListingUpdatedEvent(
            listing_id=listing.id,
            farmer_id=listing.farmer_id,
            changes=changes,
        )
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_listing_updated,
                value=data
            )
            logger.info(f"📤 Published listing.updated: {listing.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish listing.updated: {str(e)}")
    
    async def publish_listing_expired(self, listing: Listing):
        """
        Publish an event when a listing expires.
        
        Why:
        - Analytics tracks expired listings
        - Notification to farmer to renew
        """
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = ListingExpiredEvent(
            listing_id=listing.id,
            farmer_id=listing.farmer_id,
            produce_type=listing.produce_type,
        )
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_listing_expired,
                value=data
            )
            logger.info(f"📤 Published listing.expired: {listing.id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish listing.expired: {str(e)}")


# Create a singleton instance
kafka_producer = KafkaProducer()
