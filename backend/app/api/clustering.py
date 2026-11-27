"""
Exploratory unsupervised spectral clustering endpoints (Phase F3).
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.clustering import (
    ClusteringCubeSummary,
    ClusteringProfilesResponse,
    ClusteringSpatialMapResponse,
)
from backend.app.services.clustering_service import clustering_service


router = APIRouter(prefix="/clustering", tags=["Exploratory Clustering"])


@router.get("/cubes", response_model=List[ClusteringCubeSummary])
def list_clustering_cubes():
    """List cubes and their Phase F3 unsupervised clustering availability."""
    return clustering_service.list_cubes()


@router.get("/{image_id}/summary", response_model=ClusteringCubeSummary)
def get_clustering_summary(image_id: str):
    summary = clustering_service.get_summary(image_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Clustering summary for cube '{image_id}' is not available.")
    if not summary.available:
        raise HTTPException(
            status_code=404,
            detail=f"Clustering for cube '{image_id}' is unavailable: {summary.reason}",
        )
    return summary


@router.get("/{image_id}/profiles", response_model=ClusteringProfilesResponse)
def get_clustering_profiles(
    image_id: str,
    k: int = Query(default=3, ge=2, le=5),
):
    res = clustering_service.get_profiles(image_id, k=k)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Cluster profiles for cube '{image_id}' (k={k}) are not available.")
    return res


@router.get("/{image_id}/spatial-map", response_model=ClusteringSpatialMapResponse)
def get_clustering_spatial_map(
    image_id: str,
    k: int = Query(default=3, ge=2, le=5),
    max_size: int = Query(default=64, ge=16, le=256),
):
    res = clustering_service.get_spatial_map(image_id, k=k, max_size=max_size)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Spatial cluster map for cube '{image_id}' (k={k}) is not available.")
    return res
