"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Check API health status."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Check API readiness."""
    return {"ready": True}
