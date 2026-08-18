"""
================================================================================
HEALTH CHECK ENDPOINTS
================================================================================

Health checks are used for monitoring and orchestration.

Why health checks?
1. Kubernetes uses them for liveness and readiness probes
2. Load balancers use them to check if service is up
3. Monitoring systems use them for alerting
4. Debugging - quick way to check service status

Types of health checks:
1. /health - Basic health check (is the service running?)
2. /health/ready - Readiness check (is the service ready to serve traffic?)
3. /health/live - Liveness check (is the service alive?)

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
    """
    Basic health check.

    Returns:
        {"status": "healthy", "service": "listing-service"}

    This is the simplest check.
    It just confirms the service is running.
    Used by load balancers to check if the service is up.
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check.

    Checks if the service is ready to handle requests.
    This verifies:
    1. The service is running
    2. The database is accessible
    3. The database schema is ready

    Returns:
        {"status": "ready", "database": "connected"}

    Raises:
        HTTPException 503: If the service is not ready

    Why check database?
    - If the database is down, the service can't function
    - Kubernetes will stop sending traffic
    - Prevents cascading failures
    """
    try:
        # Try a simple database query
        # This verifies the database connection is working
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.scalar()

        if test_result != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database query failed",
            )

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
    """
    Liveness check.

    Checks if the service is alive.
    If this fails, Kubernetes will restart the pod.

    Returns:
        {"status": "alive"}

    Note:
        This should be as simple as possible.
        It should not check external dependencies.
        If the service is running, it should return success.
    """
    return {"status": "alive"}
