"""
Kafka producer for the Messaging Gateway Service.
"""
import json
import logging
from typing import Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import aiokafka
try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
    logger.info("✅ Kafka is available")
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("⚠️ Kafka not available. Events will not be published.")


class KafkaProducer:
    """Async Kafka producer for messaging events."""
    
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
    
    async def publish_sms_received(
        self,
        phone: str,
        text: str,
        command: str,
        args: list,
        language: str,
        session_id: Optional[str] = None,
    ):
        """
        Publish an SMS received event.
        
        Args:
            phone: Sender's phone number
            text: Raw SMS text
            command: Parsed command
            args: Command arguments
            language: Detected language
            session_id: Optional session ID
        """
        if not self.enabled:
            logger.debug(f"📤 Skipping Kafka publish (disabled): {phone}")
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = {
            "event_type": "sms.received",
            "phone": phone,
            "text": text,
            "command": command,
            "args": args,
            "language": language,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            await self.producer.send(
                topic=settings.kafka_topic_sms_received,
                value=event
            )
            logger.info(f"📤 Published sms.received: {phone}")
        except Exception as e:
            logger.error(f"❌ Failed to publish SMS event: {str(e)}")
    
    async def publish_ussd_updated(self, session_id: str, phone: str, state: str, text: str):
        """Publish a USSD session updated event."""
        if not self.enabled:
            return
        
        if not self.producer:
            await self.connect()
        
        if not self.producer:
            return
        
        event = {
            "event_type": "ussd.session.updated",
            "session_id": session_id,
            "phone": phone,
            "state": state,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            await self.producer.send(
                topic=settings.kafka_topic_ussd_session,
                value=event
            )
            logger.info(f"📤 Published ussd.session.updated: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish USSD event: {str(e)}")


# Create a singleton instance
kafka_producer = KafkaProducer()
