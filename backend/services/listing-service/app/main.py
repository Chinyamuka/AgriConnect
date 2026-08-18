"""
================================================================================
MAIN FASTAPI APPLICATION FOR LISTING SERVICE
================================================================================

This is the entry point for the Listing Service.

What this file does:
1. Creates the FastAPI application
2. Sets up CORS (allows frontend to call API)
3. Configures logging
4. Initializes database on startup
5. Includes route handlers
6. Provides health checks

Why FastAPI?
1. Fast (asynchronous, high performance)
2. Async support (non-blocking I/O)
3. Auto-generated API documentation (/docs)
4. Type hints with Pydantic validation
5. Dependency injection (database sessions)

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
from app.routes import listings, health

# ============================================================================
# LOGGING SETUP
# ============================================================================
# Why configure logging?
# 1. Track application behavior
# 2. Debug issues
# 3. Monitor performance
# 4. Audit trail
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
        - Enable PostGIS extension

    Shutdown:
        - Clean up resources
        - Close connections

    Why use lifespan?
        1. Run code on application startup
        2. Run code on application shutdown
        3. Manage resources (database connections, etc.)
        4. Clean up after the application stops

    Example:
        @asynccontextmanager
        async def lifespan(app):
            # Startup
            await init_db()
            yield
            # Shutdown
            await cleanup()
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting Listing Service...")

    try:
        # Initialize database tables
        # This creates the listings table if it doesn't exist
        # Also enables PostGIS extension
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise

    logger.info(f"✅ Service '{settings.service_name}' is ready")

    # ========================================================================
    # RUNNING
    # ========================================================================
    # The application runs here
    # All requests are handled during this period
    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("🛑 Shutting down Listing Service...")
    # Clean up resources if needed
    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================
app = FastAPI(
    title="AgriConnect Listing Service",
    description="""
    API for managing produce listings in AgriConnect.

    Features:
    - Create listings with location data (PostGIS)
    - Search listings with filters
    - Spatial search (find listings within radius)
    - Update and delete listings
    - Auto-expiry (14 days)

    The listing is the core of the marketplace.
    Farmers list produce, buyers find and bid on them.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
# Why CORS?
# 1. Allow frontend (React) to call the API
# 2. Cross-Origin Resource Sharing
# 3. Without this, browsers block requests from different origins
#
# In production, restrict allowed_origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions with consistent JSON response.

    Example:
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )
        Returns: {"detail": "Listing not found"}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle uncaught exceptions.

    Logs the error and returns a generic 500 response.
    In production, don't expose internal error details.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# INCLUDE ROUTES
# ============================================================================
# Routes are organized by functionality:
#
# /api/v1/listings   → Listing CRUD operations
# /health            → Service health checks
#
# Why version the API?
# 1. Backward compatibility
# 2. Allow breaking changes in future versions
# 3. Clients can migrate at their own pace
app.include_router(
    listings.router,
    prefix="/api/v1/listings",
    tags=["listings"],
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
    """
    Root endpoint for service information.

    Returns basic service information.
    Useful for checking if the service is running.
    """
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
    }


# ============================================================================
# DATABASE DEPENDENCY (Optional, for route testing)
# ============================================================================
@app.get("/api/test/db")
async def test_db(db: AsyncSession = Depends(get_db)):
    """
    Test database connection.

    This is useful for debugging.
    Returns a list of all listings (limited to 5).
    """
    from sqlalchemy import text

    try:
        # Test connection
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.scalar()

        # Get count of listings
        result = await db.execute(text("SELECT COUNT(*) FROM listings"))
        count = result.scalar()

        return {
            "status": "connected",
            "test_query": test_result,
            "listing_count": count,
        }
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )
