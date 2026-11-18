"""
Spectral profile endpoints.
"""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.spectral import SpectralProfileResponse
from backend.app.services.spectral_service import spectral_service

router = APIRouter(prefix="/datasets", tags=["Spectral Analytics"])


@router.get("/{image_id}/spectral-profile", response_model=SpectralProfileResponse)
def get_spectral_profile(image_id: str):
    """
    Retrieve mean and median spectral profiles across all 204 bands.
    Wavelength values (nm) are provided strictly for image 2436.
    Images 2973 and 3079 use zero-based band indices (0 to 203).
    """
    profile = spectral_service.get_spectral_profile(image_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Spectral profile for cube '{image_id}' is not available."
        )
    return profile
