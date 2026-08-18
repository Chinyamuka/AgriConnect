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
5. PostGIS support - spatial queries with GeoAlchemy2

Why Async?
- FastAPI is async
- Non-blocking database operations
- Better concurrency (handle more requests)

================================================================================
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ASYNC ENGINE
# ============================================================================
# create_async_engine: Creates the database connection pool
# 
# Parameters:
# - settings.database_url: Connection string
# - echo=False: Don't log SQL queries (set to True for debugging)
# - future=True: Use SQLAlchemy 2.0 style
# - pool_size=10: Number of connections to keep open
# - max_overflow=20: Extra connections when pool is full
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

# ============================================================================
# SESSION FACTORY
# ============================================================================
# async_sessionmaker: Creates new database sessions
# 
# Each request gets its own session.
# Sessions are closed after the request completes.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objects remain usable after commit
    autocommit=False,        # Manual commit control
    autoflush=False,         # Manual flush control
)

# ============================================================================
# BASE MODEL
# ============================================================================
# declarative_base(): Base class for all models
# 
# All models inherit from Base.
# SQLAlchemy uses this to create database tables.
Base = declarative_base()


# ============================================================================
# DEPENDENCY: Get Database Session
# ============================================================================
async def get_db() -> AsyncSession:
    """
    Dependency for getting a database session.
    
    Used in FastAPI routes:
        @app.get("/listings")
        async def get_listings(db: AsyncSession = Depends(get_db)):
            ...
    
    Why a dependency?
    1. Automatic session management
    2. Clean up after request
    3. Testability (can mock the session)
    4. Reusability across routes
    
    Yields:
        AsyncSession: Database session for the request
    
    Note:
        The session is automatically closed after the request.
        This prevents connection leaks.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# INITIALIZE DATABASE
# ============================================================================
async def init_db():
    """
    Initialize database tables and enable PostGIS.
    
    Called on application startup.
    
    What it does:
    1. Enable PostGIS extension (if not already enabled)
    2. Create all tables (if they don't exist)
    
    Why enable PostGIS?
    - Spatial queries (find listings within distance)
    - GiST indexes for fast location searches
    - ST_DWithin for radius queries
    
    Note:
        In production, use Alembic for migrations instead.
        This is for development convenience.
    """
    async with engine.begin() as conn:
        # Enable PostGIS extension
        # CREATE EXTENSION IF NOT EXISTS postgis
        # - Safe to run multiple times
        # - Only creates if not exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
        
        # Create tables
        # Base.metadata.create_all: Creates all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ PostgreSQL with PostGIS initialized successfully")
