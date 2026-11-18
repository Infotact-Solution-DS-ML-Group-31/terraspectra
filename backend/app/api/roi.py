"""
ROI Analysis endpoints for Image 3079.
"""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.roi import RoiAnalysisResponse
from backend.app.services.roi_service import roi_service

router = APIRouter(prefix="/datasets", tags=["ROI Analysis"])


@router.get("/3079/roi-analysis", response_model=RoiAnalysisResponse)
def get_3079_roi_analysis():
    """
    Retrieve three-region stem ROI analysis for image 3079:
    1. Visible necrotic lesion (ROI 1)
    2. Visually unaffected adjacent stem tissue (ROI 2)
    3. Preserved comparison stem (ROI 3)
    """
    analysis = roi_service.get_3079_roi_analysis()
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="ROI analysis for image 3079 is not available."
        )
    return analysis
