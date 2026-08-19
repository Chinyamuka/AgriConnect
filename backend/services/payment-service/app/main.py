"""
================================================================================
MAIN FASTAPI APPLICATION FOR PAYMENT SERVICE
================================================================================
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.kafka_producer import kafka_producer
from app.routes import payments, webhooks, health

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
    """Handles startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Payment Service...")
    
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise
    
    try:
        await kafka_producer.connect()
        logger.info("✅ Connected to Kafka")
    except Exception as e:
        logger.warning(f"⚠️ Kafka not available: {str(e)}")
    
    logger.info(f"✅ Service '{settings.service_name}' is ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Payment Service...")
    await kafka_producer.disconnect()
    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================
app = FastAPI(
    title="AgriConnect Payment Service",
    description="Payment and escrow service for AgriConnect",
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
# INCLUDE ROUTES
# ============================================================================
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(health.router, tags=["health"])


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
