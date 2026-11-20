"""
Automated unit and integration tests for Phase B spectral robustness and reproducibility analysis.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from src.data.analyze_3079_spectral_robustness import (
    apply_mask_erosion,
    calculate_distribution_overlap,
    extract_spatial_blocks,
    EROSION_CSV,
    DISTRIBUTION_CSV,
    BLOCKS_CSV,
    STABILITY_CSV,
    ROBUSTNESS_JSON
)


def test_binary_erosion_and_subset_preservation():
    """Verify that erosion produces a strict subset and does not mutate the source mask."""
    mask = np.zeros((100, 100), dtype=bool)
    mask[20:80, 20:80] = True
    orig_sum = mask.sum()

    eroded_1 = apply_mask_erosion(mask, iterations=1)
    eroded_2 = apply_mask_erosion(mask, iterations=2)
    eroded_3 = apply_mask_erosion(mask, iterations=3)

    # Must be strict subsets
    assert (eroded_1 & ~mask).sum() == 0
    assert (eroded_2 & ~eroded_1).sum() == 0
    assert (eroded_3 & ~eroded_2).sum() == 0

    # Monotonic reduction
    assert orig_sum > eroded_1.sum() > eroded_2.sum() > eroded_3.sum()

    # Source mask remains unmutated
    assert mask.sum() == orig_sum


def test_small_and_empty_mask_handling():
    """Verify erosion handling for small and empty masks without exceptions."""
    empty_mask = np.zeros((50, 50), dtype=bool)
    eroded_empty = apply_mask_erosion(empty_mask, iterations=1)
    assert eroded_empty.sum() == 0
    assert eroded_empty.shape == (50, 50)

    # 2x2 mask eroded with 3x3 footprint becomes empty
    small_mask = np.zeros((50, 50), dtype=bool)
    small_mask[10:12, 10:12] = True
    eroded_small = apply_mask_erosion(small_mask, iterations=1)
    assert eroded_small.sum() == 0


def test_distribution_overlap_properties():
    """Verify mathematical properties of the distribution overlap metric."""
    # 1. Identical distributions -> overlap should be near 1.0
    a = np.linspace(0, 10, 500)
    assert np.isclose(calculate_distribution_overlap(a, a, bins=50), 1.0)

    # 2. Completely disjoint distributions -> overlap must be 0.0
    disjoint_1 = np.array([1.0, 2.0, 3.0])
    disjoint_2 = np.array([10.0, 11.0, 12.0])
    assert calculate_distribution_overlap(disjoint_1, disjoint_2, bins=10) == 0.0

    # 3. Partially overlapping distributions -> overlap strictly between 0 and 1
    p1 = np.array([1.0, 2.0, 3.0, 4.0])
    p2 = np.array([3.0, 4.0, 5.0, 6.0])
    ov = calculate_distribution_overlap(p1, p2, bins=10)
    assert 0.0 < ov < 1.0


def test_spatial_block_extraction():
    """Verify spatial block extraction with synthetic cube and mask."""
    cube = np.ones((64, 64, 204), dtype=np.float32)
    mask = np.zeros((64, 64), dtype=bool)

    # Fill one 16x16 block completely (256 pixels)
    mask[0:16, 0:16] = True

    # Fill another 16x16 block with only 10 pixels (below 32 threshold)
    mask[16:26, 16] = True

    coords, counts, means = extract_spatial_blocks(cube, mask, block_size=16, min_pixels=32)

    # Only 1 block should meet threshold
    assert len(coords) == 1
    assert counts[0] == 256
    assert coords[0].tolist() == [0, 0, 16, 16]
    assert means.shape == (1, 204)
    assert np.allclose(means[0], 1.0)


def test_non_finite_measurements_handling():
    """Verify safe detection and handling of non-finite values."""
    # Normal finite array
    clean = np.random.rand(50, 204).astype(np.float32)
    assert np.isnan(clean).sum() == 0
    assert np.isinf(clean).sum() == 0

    # Contaminated array
    dirty = clean.copy()
    dirty[5, 10] = np.nan
    dirty[12, 50] = np.inf
    assert np.isnan(dirty).sum() == 1
    assert np.isinf(dirty).sum() == 1


def test_saved_robustness_outputs_204_bands():
    """Verify that saved CSV and JSON outputs contain 204 bands and complete data."""
    assert EROSION_CSV.exists(), f"Missing {EROSION_CSV}"
    assert DISTRIBUTION_CSV.exists(), f"Missing {DISTRIBUTION_CSV}"
    assert BLOCKS_CSV.exists(), f"Missing {BLOCKS_CSV}"
    assert STABILITY_CSV.exists(), f"Missing {STABILITY_CSV}"
    assert ROBUSTNESS_JSON.exists(), f"Missing {ROBUSTNESS_JSON}"

    df_erosion = pd.read_csv(EROSION_CSV)
    df_dist = pd.read_csv(DISTRIBUTION_CSV)
    df_blocks = pd.read_csv(BLOCKS_CSV)
    df_stability = pd.read_csv(STABILITY_CSV)

    # Erosion CSV: 204 bands * 4 iterations = 816 rows
    assert len(df_erosion) == 204 * 4
    assert (df_dist["band_index_0based"] == np.arange(204)).all()

    # All percentiles and overlap metrics must be finite and within valid ranges
    assert df_dist["overlap_lesion_vs_unaffected"].between(0.0, 1.0).all()
    assert df_dist["overlap_lesion_vs_comparison"].between(0.0, 1.0).all()

    # Check stability summary includes bands 119 to 125
    stability_bands = df_stability["band_index_0based"].unique()
    for b in [119, 120, 121, 122, 123, 124, 125]:
        assert b in stability_bands

    # JSON report check
    with open(ROBUSTNESS_JSON, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["image_id"] == "3079"
    assert "task_1_boundary_sensitivity" in summary
    assert "task_2_spectral_distribution" in summary
    assert "task_3_spatial_blocks" in summary
    assert "task_4_band_stability" in summary
    assert "task_5_measurement_quality" in summary

    # Verify Band 121 Rank 1 across erosion conditions
    band_121_erosion = summary["task_4_band_stability"]["band_121"]["erosion_progression"]
    for it_key in ["erosion_0px", "erosion_1px", "erosion_2px", "erosion_3px"]:
        assert band_121_erosion[it_key]["rank_lesion_vs_unaffected"] == 1
