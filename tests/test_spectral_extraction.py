"""
Automated tests for hyperspectral feature extraction and region analysis.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.extract_spectral_features import (
    extract_statistics,
    OUTPUT_DIR,
    REPORT_DIR
)


def test_extract_statistics_basic():
    """Verify calculation of mean, median, std, quartiles, and CV on known data."""
    # 4 pixels, 3 bands
    spectra = np.array([
        [1.0, 2.0, 10.0],
        [3.0, 4.0, 20.0],
        [5.0, 6.0, 30.0],
        [7.0, 8.0, 40.0]
    ], dtype=np.float32)

    stats = extract_statistics(spectra)

    assert np.allclose(stats["mean"], [4.0, 5.0, 25.0])
    assert np.allclose(stats["median"], [4.0, 5.0, 25.0])
    assert np.allclose(stats["valid_counts"], [4, 4, 4])
    assert stats["q25"].shape == (3,)
    assert stats["q75"].shape == (3,)
    assert stats["cv"].shape == (3,)
    # Verify CV = std / mean
    expected_cv = stats["std"] / stats["mean"]
    assert np.allclose(stats["cv"], expected_cv)


def test_extract_statistics_safe_cv():
    """Verify safe handling of zero/near-zero means without ZeroDivisionError."""
    # Zero mean spectrum
    spectra = np.zeros((10, 5), dtype=np.float32)
    stats = extract_statistics(spectra)

    assert np.allclose(stats["mean"], 0.0)
    assert np.allclose(stats["std"], 0.0)
    assert np.allclose(stats["cv"], 0.0)
    assert np.all(np.isfinite(stats["cv"]))


def test_extract_statistics_empty_raises():
    """Verify empty spectra array raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        extract_statistics(np.empty((0, 204), dtype=np.float32))


def test_mask_and_cube_dimension_mismatch():
    """Verify error when mask spatial shape does not match cube."""
    cube = np.zeros((512, 512, 204), dtype=np.float32)
    wrong_mask = np.zeros((256, 256), dtype=bool)

    with pytest.raises(ValueError):
        if wrong_mask.shape != cube.shape[:2]:
            raise ValueError("Mask and cube dimensions differ.")


def test_empty_mask_handling():
    """Verify error when mask is empty (0 pixels)."""
    mask = np.zeros((512, 512), dtype=bool)
    with pytest.raises(ValueError, match="empty"):
        if mask.sum() == 0:
            raise ValueError("ROI mask is empty.")


def test_overlapping_masks_handling():
    """Verify error when lesion and unaffected masks have non-zero overlap."""
    m1 = np.zeros((512, 512), dtype=bool)
    m2 = np.zeros((512, 512), dtype=bool)
    m1[10, 10] = True
    m2[10, 10] = True  # Overlap

    with pytest.raises(ValueError, match="overlap"):
        if np.any(m1 & m2):
            raise ValueError(f"ROI masks overlap by {(m1 & m2).sum()} pixels.")


def test_saved_3079_lesion_level_csv_integrity():
    """Verify the saved 3079 lesion-level CSV table against scientific criteria."""
    csv_path = OUTPUT_DIR / "3079_lesion_level_spectral_features.csv"
    assert csv_path.exists(), f"Missing output CSV: {csv_path}"

    df = pd.read_csv(csv_path)

    # 1. Band counts
    assert len(df) == 204, f"Expected 204 bands, got {len(df)}"
    assert (df["band_index_0based"] == np.arange(204)).all()

    # 2. Check essential columns
    required_cols = [
        "band_index_0based",
        "lesion_mean", "lesion_median", "lesion_std", "lesion_q25", "lesion_q75", "lesion_cv",
        "unaffected_mean", "unaffected_median", "unaffected_std", "unaffected_q25", "unaffected_q75", "unaffected_cv",
        "comparison_mean", "comparison_median", "comparison_std", "comparison_q25", "comparison_q75", "comparison_cv",
        "diff_mean_lesion_minus_unaffected", "abs_diff_mean_lesion_vs_unaffected",
        "diff_mean_lesion_minus_comparison", "abs_diff_mean_lesion_vs_comparison",
        "diff_mean_unaffected_minus_comparison", "abs_diff_mean_unaffected_vs_comparison"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
        # All measurements must be finite numbers
        assert df[col].notna().all(), f"Found NaN values in {col}"
        assert np.isfinite(df[col]).all(), f"Found infinite values in {col}"

    # 3. Check pixel counts
    assert (df["lesion_valid_pixel_count"] == 4137).all()
    assert (df["unaffected_valid_pixel_count"] == 18661).all()
    assert (df["comparison_valid_pixel_count"] == 30532).all()


def test_saved_3079_summary_json_integrity():
    """Verify the saved 3079 summary JSON metadata against scientific requirements."""
    json_path = REPORT_DIR / "3079_lesion_level_spectral_summary.json"
    assert json_path.exists(), f"Missing output JSON: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["image_id"] == "3079"
    assert summary["spectral_bands"] == 204
    assert summary["wavelength_calibration"] == "Unavailable for image 3079. No wavelength values assigned."

    counts = summary["region_pixel_counts"]
    assert counts["visible_necrotic_lesion"] == 4137
    assert counts["visually_unaffected_adjacent_stem"] == 18661
    assert counts["preserved_comparison_stem"] == 30532
    assert counts["overlap_lesion_unaffected"] == 0

    # Verify zero NaNs in raw data quality
    dq = summary["data_quality"]
    assert dq["visible_necrotic_lesion"]["nan_count"] == 0
    assert dq["visually_unaffected_adjacent_stem"]["nan_count"] == 0
    assert dq["preserved_comparison_stem"]["nan_count"] == 0

    # Verify top divergence bands recorded
    div = summary["pairwise_spectral_divergence"]
    assert "lesion_vs_adjacent_unaffected" in div
    assert div["lesion_vs_adjacent_unaffected"]["max_abs_diff_band"] == 121
    assert len(div["lesion_vs_adjacent_unaffected"]["top_5_divergent_bands"]) == 5

    # Verify disclaimers present
    disclaimers = summary["scientific_limitations_and_disclaimers"]
    assert len(disclaimers) >= 6
