"""
Quality metrics schema.
"""

from typing import List
from pydantic import BaseModel


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
