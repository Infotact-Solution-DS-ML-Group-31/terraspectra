"""
Dataset management endpoints.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.schemas.dataset import DatasetSummary, DatasetMetadata
from backend.app.schemas.quality import QualityMetricsResponse
from backend.app.services.dataset_service import dataset_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=List[DatasetSummary])
def list_datasets():
    """List all locally available hyperspectral cubes with summary attributes."""
    return dataset_service.list_datasets()


@router.get("/{image_id}/metadata", response_model=DatasetMetadata)
def get_dataset_metadata(image_id: str):
    """Retrieve verified acquisition metadata for a specific cube."""
    metadata = dataset_service.get_metadata(image_id)
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"Hyperspectral cube '{image_id}' not found among locally available datasets."
        )
    return metadata


@router.get("/{image_id}/preview")
def get_dataset_preview(image_id: str):
    """Return the false-color RGB preview image for the specified cube."""
    preview_path = dataset_service.get_preview_path(image_id)
    if not preview_path or not preview_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Preview image for cube '{image_id}' is not available."
        )
    return FileResponse(preview_path, media_type="image/png")


@router.get("/{image_id}/quality", response_model=QualityMetricsResponse)
def get_dataset_quality(image_id: str):
    """Retrieve data quality metrics, NaN counts, and uncalibrated values exceeding 1.0."""
    metrics = dataset_service.get_quality_metrics(image_id)
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"Quality metrics for cube '{image_id}' could not be computed or cube is missing."
        )
    return metrics
