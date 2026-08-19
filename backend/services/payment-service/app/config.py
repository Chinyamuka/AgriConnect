"""
================================================================================
CONFIGURATION FOR PAYMENT SERVICE
================================================================================

This file loads all configuration from environment variables.

Why use Pydantic Settings?
1. Type validation - ensures correct data types
2. Environment variable support - reads from .env automatically
3. Default values - sensible defaults for development

================================================================================
"""
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """
    Service configuration loaded from environment variables.
    """
    
    # ========================================================================
    # SERVICE CONFIGURATION
    # ========================================================================
    service_name: str = "payment-service"
    log_level: str = "INFO"
    
    # ========================================================================
    # DATABASE - PostgreSQL
    # ========================================================================
    db_type: str = "postgresql"
    db_name: str = "agriconnect_payment"
    db_user: str = "dc5400"
    db_password: str = "adon@DC5400"
    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    
    @property
    def database_url(self) -> str:
        """Build the database connection URL."""
        encoded_password = quote_plus(self.db_password)
        return f"postgresql+psycopg://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # ========================================================================
    # FLUTTERWAVE - Payment Gateway
    # ========================================================================
    # These keys come from your Flutterwave dashboard
    # Use sandbox keys for development
    flutterwave_public_key: str = ""
    flutterwave_secret_key: str = ""
    flutterwave_encryption_key: str = ""
    flutterwave_webhook_secret: str = ""
    
    @property
    def flutterwave_base_url(self) -> str:
        """Flutterwave API base URL."""
        # Use sandbox for development, production for live
        return "https://api.flutterwave.com/v3"
    
    # ========================================================================
    # KAFKA - Event Streaming
    # ========================================================================
    kafka_bootstrap_servers: str = "127.0.0.1:9092"
    kafka_topic_payment_initiated: str = "payment.initiated"
    kafka_topic_payment_completed: str = "payment.completed"
    kafka_topic_payout_released: str = "payout.released"
    
    # ========================================================================
    # BIDDING SERVICE - For Validation
    # ========================================================================
    bidding_service_url: str = "http://127.0.0.1:8003"
    
    # ========================================================================
    # PLATFORM FEES
    # ========================================================================
    # Percentage taken from each transaction
    # Example: 5.0 means 5% platform fee
    platform_fee_percentage: float = 5.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
