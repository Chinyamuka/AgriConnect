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
from urllib.parse import quote_plus  # For URL-encoding special characters


class Settings(BaseSettings):
    """
    Service configuration loaded from environment variables.
    
    All values can be overridden by setting environment variables
    or adding them to the .env file.
    """
    
    # ========================================================================
    # SERVICE CONFIGURATION
    # ========================================================================
    service_name: str = "listing-service"
    log_level: str = "INFO"
    
    # ========================================================================
    # DATABASE - PostgreSQL with PostGIS
    # ========================================================================
    # Why PostgreSQL with PostGIS?
    # 1. Spatial queries - find listings within a radius
    # 2. GiST indexes - fast location searches
    # 3. ST_DWithin - radius queries with indexes
    # 4. Production-grade - reliable for financial transactions
    #
    # Why psycopg instead of asyncpg?
    # 1. asyncpg has 'localhost' hardcoded as a fallback in WSL
    # 2. This causes "Name or service not known" errors
    # 3. psycopg is the modern PostgreSQL driver
    # 4. psycopg works reliably on all platforms
    #
    # Why 127.0.0.1 instead of localhost?
    # 1. WSL sometimes can't resolve 'localhost'
    # 2. 127.0.0.1 is the loopback IP address
    # 3. Always works regardless of DNS
    #
    # IMPORTANT: The password contains '@' which must be URL-encoded!
    # Without encoding, the '@' is misinterpreted as a separator.
    # quote_plus('adon@DC5400') → 'adon%40DC5400'
    db_type: str = "postgresql"
    db_name: str = "agriconnect_listing"
    db_user: str = "dc5400"
    db_password: str = "adon@DC5400"
    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    
    @property
    def database_url(self) -> str:
        """
        Build the database connection URL with URL-encoded password.
        
        Why URL-encode the password?
        - The password contains '@' which is a special character in URLs
        - @ is used to separate user:password from host
        - Without encoding, 'dc5400:adon@DC5400@127.0.0.1' is parsed incorrectly
        - URL-encoding: '@' becomes '%40'
        - Result: 'dc5400:adon%40DC5400@127.0.0.1' ✅
        
        Format: postgresql+psycopg://user:password@host:port/database
        
        Example: postgresql+psycopg://dc5400:adon%40DC5400@127.0.0.1:5432/agriconnect_listing
        """
        # URL-encode the password to handle special characters (@, #, $, etc.)
        encoded_password = quote_plus(self.db_password)
        return f"postgresql+psycopg://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # ========================================================================
    # REDIS - Caching and Session Storage
    # ========================================================================
    redis_url: str = "redis://127.0.0.1:6379/1"
    
    # ========================================================================
    # KAFKA - Event Streaming
    # ========================================================================
    kafka_bootstrap_servers: str = "127.0.0.1:9092"
    kafka_topic_listing_created: str = "listing.created"
    kafka_topic_listing_updated: str = "listing.updated"
    kafka_topic_listing_expired: str = "listing.expired"
    
    # ========================================================================
    # LISTING BUSINESS RULES
    # ========================================================================
    max_listing_age_days: int = 14
    max_price_deviation_percentage: float = 50.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
