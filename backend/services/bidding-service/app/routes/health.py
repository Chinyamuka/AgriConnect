"""
================================================================================
HEALTH CHECK ENDPOINTS
================================================================================
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.redis_client import redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.service_name,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check with database and Redis verification."""
    try:
        # Check database
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.scalar()
        if test_result != 1:
            raise Exception("Database query failed")
        
        # Check Redis
        await redis_client.get("health_check")
        
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected",
            "service": settings.service_name,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
        )


@router.get("/health/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive"}
