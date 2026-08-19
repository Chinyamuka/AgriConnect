"""
================================================================================
DATABASE CONNECTION FOR LISTING SERVICE
================================================================================

This file manages the PostgreSQL connection with SQLAlchemy.

Why SQLAlchemy?
1. ORM - Object Relational Mapping (models as Python classes)
2. Async support - works with FastAPI's async/await
3. Connection pooling - efficient database connections
4. Migration support - schema changes with Alembic
5. PostGIS support - spatial queries

================================================================================
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
# Get the URL from settings (password is already URL-encoded)
DATABASE_URL = settings.database_url

# Log the URL with password hidden for security
logger.info(f"Database URL: {DATABASE_URL.replace(settings.db_password, '*****')}")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
)


# ============================================================================
# SYNC FUNCTION FOR INSPECTION
# ============================================================================
def _check_and_create_tables(sync_conn):
    """
    Sync function to check if tables exist and create them if needed.
    
    This is run inside conn.run_sync() because async engines don't support
    direct inspection. The run_sync() method runs a sync function with
    a sync connection.
    
    Why this approach?
    - AsyncEngine doesn't support inspect() directly
    - run_sync() gives us a sync connection
    - We can use inspect() on the sync connection
    - This is the recommended SQLAlchemy async pattern
    """
    # Get inspector from the sync connection
    inspector = inspect(sync_conn)
    existing_tables = inspector.get_table_names()
    
    if "listings" in existing_tables:
        logger.info("📋 Table 'listings' already exists, skipping creation")
        # Get count of existing listings
        result = sync_conn.execute(text("SELECT COUNT(*) FROM listings"))
        count = result.scalar()
        logger.info(f"📊 Found {count} existing listings")
        return False  # Tables already exist
    else:
        logger.info("📋 Creating tables...")
        # Create all tables
        Base.metadata.create_all(sync_conn)
        logger.info("✅ Database tables created successfully")
        return True  # Tables were created


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

# ============================================================================
# BASE MODEL
# ============================================================================
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
    """Initialize database tables and enable PostGIS."""
    try:
        logger.info(f"Connecting to database...")
        logger.info(f"Host: {settings.db_host}, Port: {settings.db_port}, Database: {settings.db_name}")
        
        async with engine.begin() as conn:
            # ====================================================================
            # ENABLE POSTGIS EXTENSION
            # ====================================================================
            # CREATE EXTENSION IF NOT EXISTS postgis
            # - Safe to run multiple times
            # - Only creates if not exists
            # - Required for spatial queries
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            logger.info("✅ PostGIS extensions enabled")
            
            # ====================================================================
            # CHECK AND CREATE TABLES
            # ====================================================================
            # Run the sync function inside run_sync
            # This is required because async engines don't support inspect()
            # The run_sync() method gives us a sync connection
            # We can then use inspect() on that sync connection
            await conn.run_sync(_check_and_create_tables)
            
            logger.info("✅ Database initialization complete!")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
