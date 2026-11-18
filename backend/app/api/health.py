"""
Health check endpoint.
"""

from fastapi import APIRouter
from backend.app.config import API_VERSION, APP_NAME

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Return backend status, version, and platform identity."""
    return {
        "status": "healthy",
        "app_name": APP_NAME,
        "version": API_VERSION,
        "platform": "TerraSpectra Exploratory Hyperspectral Analytics"
    }
