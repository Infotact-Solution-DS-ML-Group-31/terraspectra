"""
Dataset schemas for cube listings and metadata responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    image_id: str
    shape: List[int]
    spectral_bands: int
    data_type: str
    file_size_mb: float
    calibration_status: str
    has_wavelength_calibration: bool
    pathogen: str
    replicate: int
    sample: int
    part: str
    date: str


class DatasetMetadata(BaseModel):
    image_id: str
    replicate: int
    pathogen: str
    sample: int
    part: str
    date: str
    imaging_distance_cm: Optional[float] = None
    integration_time_ms: int
    weather: str
    plant_id: str
    organ_id: str
    calibration_status: str
    verified_wavelengths: bool
    scientific_disclaimer: str
