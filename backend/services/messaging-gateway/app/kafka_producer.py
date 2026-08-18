"""
Kafka producer for the Messaging Gateway Service.

Publishes events to Kafka for other services to consume.
"""
import json
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer
from app.config import settings
from app.models import SMSReceivedEvent, USSDUpdatedEvent

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Async Kafka producer.
    
    Publishes events to Kafka topics.
    """
    
    def __init__(self):
        """Initialize the Kafka producer."""
        self.producer: Optional[AIOKafkaProducer] = None
    
    async def connect(self):
        """Connect to Kafka."""
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
                max_batch_size=16384,
            )
            await self.producer.start()
            logger.info(f"✅ Connected to Kafka at {settings.kafka_bootstrap_servers}")
    
    async def disconnect(self):
        """Disconnect from Kafka."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("✅ Disconnected from Kafka")
    
    async def publish_sms_received(self, event: SMSReceivedEvent):
        """
        Publish an SMS received event.
        
        Other services (Fraud Service, User Service) consume this.
        """
        if not self.producer:
            await self.connect()
        
        # Convert to dict
        data = event.dict()
        
        # Send to Kafka
        await self.producer.send(
            topic=settings.kafka_topic_sms_received,
            value=data
        )
        logger.info(f"📤 Published sms.received: {event.phone}")
    
    async def publish_ussd_updated(self, event: USSDUpdatedEvent):
        """
        Publish a USSD session updated event.
        """
        if not self.producer:
            await self.connect()
        
        # Convert to dict
        data = event.dict()
        
        # Send to Kafka
        await self.producer.send(
            topic=settings.kafka_topic_ussd_session,
            value=data
        )
        logger.info(f"📤 Published ussd.session.updated: {event.session_id}")


# Create a singleton instance
kafka_producer = KafkaProducer()
