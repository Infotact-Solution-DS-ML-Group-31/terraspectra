"""
Spectral profile schemas.
"""

from typing import List, Optional
from pydantic import BaseModel


class SpectralBandPoint(BaseModel):
    band_index: int
    wavelength_nm: Optional[float] = None
    mean: float
    median: float
    std: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None


class SpectralProfileResponse(BaseModel):
    image_id: str
    spectral_axis: str  # 'wavelength_nm' or 'zero_based_band_indices'
    total_bands: int
    has_verified_wavelengths: bool
    data: List[SpectralBandPoint]
    scientific_notes: List[str]
