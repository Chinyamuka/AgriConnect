"""
Kafka producer for the Messaging Gateway Service.

Publishes events to Kafka for other services to consume.
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import aiokafka, but don't fail if not available
try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
    logger.info("✅ Kafka is available")
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("⚠️ Kafka not available. Events will not be published.")

from app.config import settings
from app.models import SMSReceivedEvent, USSDUpdatedEvent


class KafkaProducer:
    """
    Async Kafka producer.
    
    Publishes events to Kafka topics.
    """
    
    def __init__(self):
        """Initialize the Kafka producer."""
        self.producer: Optional[object] = None
        self.enabled = KAFKA_AVAILABLE
    
    async def connect(self):
        """Connect to Kafka."""
        if not self.enabled or self.producer:
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
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
    
    async def publish_sms_received(self, event: SMSReceivedEvent):
        """Publish an SMS received event."""
        if not self.enabled:
            logger.debug(f"📤 Skipping Kafka publish (disabled): {event.phone}")
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_sms_received,
                value=data
            )
            logger.info(f"📤 Published sms.received: {event.phone}")
        except Exception as e:
            logger.error(f"❌ Failed to publish SMS event: {str(e)}")
    
    async def publish_ussd_updated(self, event: USSDUpdatedEvent):
        """Publish a USSD session updated event."""
        if not self.enabled:
            logger.debug(f"📤 Skipping Kafka publish (disabled): {event.session_id}")
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        try:
            data = event.dict()
            await self.producer.send(
                topic=settings.kafka_topic_ussd_session,
                value=data
            )
            logger.info(f"📤 Published ussd.session.updated: {event.session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish USSD event: {str(e)}")


# Create a singleton instance
kafka_producer = KafkaProducer()
