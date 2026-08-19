"""
================================================================================
CONFIGURATION FOR BIDDING SERVICE
================================================================================

This file loads all configuration from environment variables.

Why use Pydantic Settings?
1. Type validation - ensures correct data types
2. Environment variable support - reads from .env automatically
3. Default values - sensible defaults for development
4. Property methods - computed values like database_url

================================================================================
"""
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """
    Service configuration loaded from environment variables.
    
    All values can be overridden by setting environment variables
    or adding them to the .env file.
    """
    
    # ========================================================================
    # SERVICE CONFIGURATION
    # ========================================================================
    service_name: str = "bidding-service"
    log_level: str = "INFO"
    
    # ========================================================================
    # DATABASE - PostgreSQL
    # ========================================================================
    db_type: str = "postgresql"
    db_name: str = "agriconnect_bid"
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
    # REDIS - Distributed Locks
    # ========================================================================
    # Why Redis?
    # 1. Distributed locks - prevent double-selling
    # 2. Fast - in-memory operations
    # 3. Atomic operations - safe for concurrency
    # 4. TTL support - locks auto-expire
    redis_url: str = "redis://127.0.0.1:6379/1"
    
    # Lock timeout in seconds (30 seconds)
    # If a lock is held for more than 30 seconds, it auto-releases
    lock_timeout_seconds: int = 30
    
    # ========================================================================
    # KAFKA - Event Streaming
    # ========================================================================
    kafka_bootstrap_servers: str = "127.0.0.1:9092"
    kafka_topic_bid_placed: str = "bid.placed"
    kafka_topic_bid_accepted: str = "bid.accepted"
    kafka_topic_bid_rejected: str = "bid.rejected"
    
    # ========================================================================
    # LISTING SERVICE - For Validation
    # ========================================================================
    # Why call Listing Service?
    # 1. Validate listing exists before placing bid
    # 2. Check listing status (must be active)
    # 3. Get farmer_id for notifications
    # 4. Decoupled communication (HTTP API)
    listing_service_url: str = "http://127.0.0.1:8002"
    
    # ========================================================================
    # BIDDING BUSINESS RULES
    # ========================================================================
    # Minimum bid amount (must be > 0)
    # Bids are in Zambian Kwacha (K)
    min_bid_amount: float = 1.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
