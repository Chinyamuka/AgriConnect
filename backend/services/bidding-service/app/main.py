"""
================================================================================
MAIN FASTAPI APPLICATION FOR BIDDING SERVICE
================================================================================

This is the entry point for the Bidding Service.

What this file does:
1. Creates the FastAPI application
2. Sets up CORS
3. Configures logging
4. Initializes database on startup
5. Includes route handlers
6. Provides health checks

================================================================================
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import init_db, get_db
from app.redis_client import redis_client
from app.kafka_producer import kafka_producer
from app.routes import bids, health

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN MANAGER
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    
    Startup:
        - Initialize database tables
        - Connect to Redis
        - Connect to Kafka
    
    Shutdown:
        - Disconnect from Redis
        - Disconnect from Kafka
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting Bidding Service...")
    
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise
    
    try:
        await redis_client.connect()
        logger.info("✅ Connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {str(e)}")
        raise
    
    try:
        await kafka_producer.connect()
        logger.info("✅ Connected to Kafka")
    except Exception as e:
        logger.warning(f"⚠️ Kafka not available: {str(e)}")
    
    logger.info(f"✅ Service '{settings.service_name}' is ready")
    
    # ========================================================================
    # RUNNING
    # ========================================================================
    yield
    
    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("🛑 Shutting down Bidding Service...")
    await redis_client.disconnect()
    await kafka_producer.disconnect()
    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================
app = FastAPI(
    title="AgriConnect Bidding Service",
    description="""
    API for managing bids on produce listings.
    
    Features:
    - Place bids on active listings
    - View bids on listings
    - Accept/reject bids with Redis locks
    - Prevent double-selling
    - Event-driven communication
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# INCLUDE ROUTES
# ============================================================================
app.include_router(
    bids.router,
    prefix="/api/v1/bids",
    tags=["bids"],
)

app.include_router(
    health.router,
    tags=["health"],
)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
    }
