"""
Saved real-cube PCA artifact endpoints.
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.pca import (
    PcaCubeSummary,
    PcaExplainedVarianceResponse,
    PcaLoadingResponse,
    PcaSpatialScoresResponse,
)
from backend.app.services.pca_service import pca_service


router = APIRouter(prefix="/pca", tags=["PCA Analytics"])


@router.get("/cubes", response_model=List[PcaCubeSummary])
def list_pca_cubes():
    """List cubes with available saved real-cube PCA results."""
    return pca_service.list_cubes()


@router.get("/{image_id}/summary", response_model=PcaCubeSummary)
def get_pca_summary(image_id: str):
    summary = pca_service.get_summary(image_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"PCA summary for cube '{image_id}' is not available.")
    if not summary.available:
        raise HTTPException(
            status_code=404,
            detail=f"PCA analysis for cube '{image_id}' is unavailable: no appropriate ROI mask was saved.",
        )
    return summary


@router.get("/{image_id}/explained-variance", response_model=PcaExplainedVarianceResponse)
def get_pca_explained_variance(image_id: str):
    response = pca_service.get_explained_variance(image_id)
    if response is None:
        raise HTTPException(status_code=404, detail=f"Explained-variance PCA data for cube '{image_id}' is not available.")
    return response


@router.get("/{image_id}/loadings", response_model=PcaLoadingResponse)
def get_pca_loadings(image_id: str):
    response = pca_service.get_loadings(image_id)
    if response is None:
        raise HTTPException(status_code=404, detail=f"Component-loading PCA data for cube '{image_id}' is not available.")
    return response


@router.get("/{image_id}/spatial-scores", response_model=PcaSpatialScoresResponse)
def get_pca_spatial_scores(
    image_id: str,
    max_size: int = Query(default=64, ge=16, le=256),
):
    response = pca_service.get_spatial_scores(image_id, max_size=max_size)
    if response is None:
        raise HTTPException(status_code=404, detail=f"Spatial PCA score data for cube '{image_id}' is not available.")
    return response


@router.get("/{image_id}/region-scores")
def get_pca_region_scores(image_id: str):
    raise HTTPException(
        status_code=404,
        detail=(
            f"Structured region-wise PCA score distributions for cube '{image_id}' are not available. "
            "Only a saved figure is present for image 3079."
        ),
    )
