"""
Service for ROI analysis (Image 3079).
Reuses validated lesion-level annotations and extraction outputs.
"""

from typing import Optional
import json

from backend.app.config import REPORTS_DIR, SEGMENTATION_DIR
from backend.app.schemas.roi import RoiAnalysisResponse, RoiPixelCounts


class RoiService:
    def get_3079_roi_analysis(self) -> Optional[RoiAnalysisResponse]:
        summary_file = REPORTS_DIR / "3079_lesion_level_spectral_summary.json"
        seg_summary_file = SEGMENTATION_DIR / "3079_lesion_level_summary.json"

        if not summary_file.exists():
            return None

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

        counts_dict = summary["region_pixel_counts"]
        pixel_counts = RoiPixelCounts(
            visible_necrotic_lesion=counts_dict["visible_necrotic_lesion"],
            visually_unaffected_adjacent_stem=counts_dict["visually_unaffected_adjacent_stem"],
            preserved_comparison_stem=counts_dict["preserved_comparison_stem"],
            lesion_bearing_stem_total=counts_dict["lesion_bearing_stem_total"],
            unannotated_stem_margin=counts_dict["unannotated_stem_margin"],
            overlap_pixels=counts_dict["overlap_lesion_unaffected"]
        )

        return RoiAnalysisResponse(
            image_id="3079",
            spectral_axis="zero_based_band_indices",
            wavelength_calibration="Unavailable for image 3079. No wavelength values assigned.",
            region_pixel_counts=pixel_counts,
            pairwise_divergence=summary["pairwise_spectral_divergence"],
            scientific_disclaimers=summary["scientific_limitations_and_disclaimers"]
        )


roi_service = RoiService()
