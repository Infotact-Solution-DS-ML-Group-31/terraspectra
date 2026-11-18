"""
ROI and Quality schemas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class RoiPixelCounts(BaseModel):
    visible_necrotic_lesion: int
    visually_unaffected_adjacent_stem: int
    preserved_comparison_stem: int
    lesion_bearing_stem_total: int
    unannotated_stem_margin: int
    overlap_pixels: int


class DivergenceStats(BaseModel):
    max_abs_diff_band: int
    max_abs_diff_value: float
    lesion_mean_at_max_band: float
    comparison_mean_at_max_band: float
    mean_abs_diff_all_bands: float
    top_5_divergent_bands: List[int]


class RoiAnalysisResponse(BaseModel):
    image_id: str
    spectral_axis: str
    wavelength_calibration: str
    region_pixel_counts: RoiPixelCounts
    pairwise_divergence: Dict[str, Any]
    scientific_disclaimers: List[str]


class QualityMetricsResponse(BaseModel):
    image_id: str
    nan_count: int
    inf_count: int
    min_value: float
    max_value: float
    values_exceeding_1_count: int
    values_exceeding_1_percentage: float
    has_values_exceeding_1: bool
    affected_bands_exceeding_1: List[int]
    warnings: List[str]
    scientific_notes: List[str]
