"""
Configuration for the Messaging Gateway Service.

All settings are loaded from environment variables.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Service configuration.
    
    All values can be overridden with environment variables.
    """
    
    # ========================================================================
    # SERVICE CONFIGURATION
    # ========================================================================
    service_name: str = "messaging-gateway"
    log_level: str = "INFO"
    
    # ========================================================================
    # AFRICA'S TALKING - SMS/USSD Gateway
    # ========================================================================
    # Username for Africa's Talking API
    africastalking_username: str = "sandbox"
    
    # API Key from Africa's Talking dashboard
    africastalking_api_key: str = ""
    
    # Sender ID shown to recipients (must be registered)
    africastalking_sender_id: str = "AgriConnect"
    
    # ========================================================================
    # REDIS - Session Management
    # ========================================================================
    # Redis connection URL
    # Format: redis://host:port/db
    redis_url: str = "redis://localhost:6379/1"
    
    # USSD session timeout in seconds (10 minutes)
    ussd_session_timeout: int = 600
    
    # ========================================================================
    # KAFKA - Event Streaming
    # ========================================================================
    # Kafka bootstrap servers
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # Kafka topics
    kafka_topic_sms_received: str = "sms.received"
    kafka_topic_ussd_session: str = "ussd.session.updated"
    
    # ========================================================================
    # OTP CONFIGURATION
    # ========================================================================
    # OTP expiry time in seconds (5 minutes)
    otp_expiry_seconds: int = 300
    
    # ========================================================================
    # COMMAND CONFIGURATION
    # ========================================================================
    # Maximum length of SMS command
    max_command_length: int = 160
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a single instance of settings to import
settings = Settings()
