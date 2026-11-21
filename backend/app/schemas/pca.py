"""
PCA artifact response schemas.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class PcaSpectralAxis(BaseModel):
    axis_type: str
    axis_label: str
    values: List[object]
    calibration_status: str


class PcaCubeSummary(BaseModel):
    image_id: str
    status: str
    available: bool
    spectral_axis: Optional[PcaSpectralAxis] = None
    spectral_features_per_pixel: Optional[int] = None
    valid_pixel_count: Optional[int] = None
    fit_sample_count: Optional[int] = None
    cumulative_explained_variance_ratio: Optional[float] = None
    region_distributions_available: bool
    region_distributions_reason: Optional[str] = None
    scientific_disclaimer: str


class PcaExplainedVariancePoint(BaseModel):
    component: str
    explained_variance_ratio: float
    cumulative_explained_variance_ratio: float


class PcaExplainedVarianceResponse(BaseModel):
    image_id: str
    independent_fit: bool
    cumulative_explained_variance_ratio: float
    data: List[PcaExplainedVariancePoint]
    spectral_axis: PcaSpectralAxis


class PcaLoadingPoint(BaseModel):
    spectral_position: float
    pc1: float
    pc2: float
    pc3: float


class PcaLoadingResponse(BaseModel):
    image_id: str
    independent_fit: bool
    spectral_axis: PcaSpectralAxis
    data: List[PcaLoadingPoint]


class PcaSpatialPoint(BaseModel):
    row: int
    column: int
    pc1: Optional[float] = None
    pc2: Optional[float] = None
    pc3: Optional[float] = None
    valid_pixel_count: int


class PcaSpatialScoresResponse(BaseModel):
    image_id: str
    independent_fit: bool
    width: int
    height: int
    downsampled_width: int
    downsampled_height: int
    data: List[PcaSpatialPoint]
    spectral_axis: PcaSpectralAxis
