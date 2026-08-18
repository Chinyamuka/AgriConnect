"""
================================================================================
CONFIGURATION FOR LISTING SERVICE
================================================================================

This file loads all configuration from environment variables.
All sensitive data (passwords, keys) come from .env file.

Why use Pydantic Settings?
1. Type validation - ensures correct data types
2. Environment variable support - reads from .env automatically
3. Default values - sensible defaults for development
4. Property methods - computed values like database_url

================================================================================
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Service configuration loaded from environment variables.
    
    All values can be overridden by setting environment variables
    or adding them to the .env file.
    """
    
    # ========================================================================
    # SERVICE CONFIGURATION
    # ========================================================================
    # service_name: Used for logging and monitoring
    # log_level: Controls verbosity (DEBUG, INFO, WARNING, ERROR)
    service_name: str = "listing-service"
    log_level: str = "INFO"
    
    # ========================================================================
    # DATABASE - PostgreSQL with PostGIS
    # ========================================================================
    # These values connect to the separate listing database
    # Why separate database? See database-per-service pattern
    db_type: str = "postgresql"
    db_name: str = "agriconnect_listing"
    db_user: str = "dc5400"
    db_password: str = "adon@DC5400"
    db_host: str = "localhost"
    db_port: str = "5432"
    
    @property
    def database_url(self) -> str:
        """
        Build the database connection URL.
        
        Format: postgresql+asyncpg://user:password@host:port/database
        
        Why asyncpg?
        - Async PostgreSQL driver
        - Faster than psycopg2 for async operations
        - Supports PostgreSQL features like PostGIS
        """
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # ========================================================================
    # REDIS - Caching and Session Storage
    # ========================================================================
    # Used for:
    # - Caching frequently accessed listings
    # - Rate limiting
    # - Distributed locks (future)
    redis_url: str = "redis://localhost:6379/1"
    
    # ========================================================================
    # KAFKA - Event Streaming
    # ========================================================================
    # Topics for publishing listing events
    # Other services subscribe to these topics
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_listing_created: str = "listing.created"
    kafka_topic_listing_updated: str = "listing.updated"
    kafka_topic_listing_expired: str = "listing.expired"
    
    # ========================================================================
    # LISTING BUSINESS RULES
    # ========================================================================
    # max_listing_age_days: Listings expire after 14 days
    #   - Keeps marketplace fresh
    #   - Prevents stale listings
    #   - Encourages farmers to relist
    #
    # max_price_deviation_percentage: Flag price anomalies
    #   - If price is 50% above market average → flag for review
    #   - Prevents price gouging
    #   - Protects buyers
    max_listing_age_days: int = 14
    max_price_deviation_percentage: float = 50.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# ============================================================================
# SINGLE INSTANCE
# ============================================================================
# Create one settings object to import everywhere
# This ensures all parts of the service use the same configuration
settings = Settings()
