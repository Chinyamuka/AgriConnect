"""
================================================================================
DATABASE CONNECTION FOR BIDDING SERVICE
================================================================================

This file manages the PostgreSQL connection with SQLAlchemy.

Note: Bidding Service doesn't need PostGIS (no spatial queries),
so we don't need to create the postgis extension.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, inspect
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE
# ============================================================================
DATABASE_URL = settings.database_url
logger.info(f"Database URL: {DATABASE_URL.replace(settings.db_password, '*****')}")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
)


# ============================================================================
# SYNC FUNCTION FOR TABLE INSPECTION
# ============================================================================
def _check_and_create_tables(sync_conn):
    """Check if tables exist and create them if needed."""
    inspector = inspect(sync_conn)
    existing_tables = inspector.get_table_names()
    
    if "bids" in existing_tables:
        logger.info("📋 Table 'bids' already exists")
        return False
    
    logger.info("📋 Creating tables...")
    Base.metadata.create_all(sync_conn)
    logger.info("✅ Database tables created successfully")
    return True


# ============================================================================
# SESSION FACTORY
# ============================================================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


# ============================================================================
# DEPENDENCY: Get Database Session
# ============================================================================
async def get_db() -> AsyncSession:
    """Dependency for getting a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# INITIALIZE DATABASE
# ============================================================================
async def init_db():
    """Initialize database tables."""
    try:
        logger.info(f"Connecting to database...")
        logger.info(f"Host: {settings.db_host}, Port: {settings.db_port}, Database: {settings.db_name}")
        
        async with engine.begin() as conn:
            # Bidding Service doesn't need PostGIS
            # No spatial queries, so no need for postgis extension
            
            # Check and create tables
            await conn.run_sync(_check_and_create_tables)
            
            logger.info("✅ Database initialization complete!")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
