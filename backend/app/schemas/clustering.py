"""
Unsupervised spectral clustering response schemas (Phase F3).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ClusteringSpectralAxis(BaseModel):
    axis_type: str
    axis_label: str
    values: List[float]
    calibration_status: str


class ClusterSizeInfo(BaseModel):
    cluster_id: int
    pixel_count: int
    percentage: float
    mean_within_cluster_std: float


class ClusteringKResult(BaseModel):
    k: int
    inertia_standardized: float
    silhouette_score: Optional[float] = None
    silhouette_sample_size: int
    cluster_sizes: List[ClusterSizeInfo]
    seed_stability_ari_mean: Optional[float] = None
    seed_stability_ari_min: Optional[float] = None
    spatial_block_stability_ari: Optional[float] = None
    posthoc_roi_comparison: Optional[Dict[str, Any]] = None


class ClusteringCubeSummary(BaseModel):
    image_id: str
    status: str
    available: bool
    reason: Optional[str] = None
    spectral_axis: Optional[ClusteringSpectralAxis] = None
    valid_pixel_count: Optional[int] = None
    fit_sample_count: Optional[int] = None
    silhouette_sample_size: Optional[int] = None
    k_values: List[int] = []
    k_results: Dict[str, ClusteringKResult] = {}
    scientific_disclaimer: str


class ClusterProfileSeries(BaseModel):
    cluster_id: int
    pixel_count: int
    percentage: float
    mean_profile: List[float]
    std_profile: List[float]


class ClusteringProfilesResponse(BaseModel):
    image_id: str
    k: int
    independent_fit: bool
    spectral_axis: ClusteringSpectralAxis
    clusters: List[ClusterProfileSeries]
    scientific_disclaimer: str


class ClusteringSpatialPoint(BaseModel):
    row: int
    column: int
    cluster_id: Optional[int] = None
    valid_pixel_count: int


class ClusteringSpatialMapResponse(BaseModel):
    image_id: str
    k: int
    independent_fit: bool
    width: int
    height: int
    downsampled_width: int
    downsampled_height: int
    data: List[ClusteringSpatialPoint]
    spectral_axis: ClusteringSpectralAxis
    scientific_disclaimer: str
