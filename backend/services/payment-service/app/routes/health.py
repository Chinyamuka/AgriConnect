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
    """Readiness check with database verification."""
    try:
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.scalar()
        if test_result != 1:
            raise Exception("Database query failed")
        
        return {
            "status": "ready",
            "database": "connected",
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
