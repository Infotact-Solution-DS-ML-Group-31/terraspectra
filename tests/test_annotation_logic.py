"""
Unit tests for lesion-level annotation geometric logic and validation checks.
"""

from pathlib import Path
import json
import numpy as np
import pytest

from src.data.annotate_3079_lesion_level import (
    polygon_to_mask,
    validate_saved_annotations
)


def test_polygon_to_mask_empty_and_small():
    """Verify polygon_to_mask returns all False for fewer than 3 points."""
    shape = (100, 100)
    assert not polygon_to_mask([], shape).any()
    assert not polygon_to_mask([[10, 10]], shape).any()
    assert not polygon_to_mask([[10, 10], [20, 20]], shape).any()


def test_polygon_to_mask_triangle():
    """Verify polygon_to_mask rasterizes a known triangle correctly."""
    shape = (50, 50)
    pts = np.array([[10, 10], [30, 10], [20, 30]])
    mask = polygon_to_mask(pts, shape)
    assert mask.shape == shape
    assert mask.dtype == bool
    assert mask.sum() > 0
    # Centroid (20, 16) should be inside
    assert mask[16, 20]
    # Point outside triangle (0, 0) should be False
    assert not mask[0, 0]


def test_validation_logic_mocked(tmp_path):
    """Test full 10-check validation suite against synthetic/mocked outputs."""
    shape = (512, 512)

    # 1. Create a mock source mask
    src_stem = np.zeros(shape, dtype=bool)
    src_stem[100:300, 100:300] = True

    src_comp = np.zeros(shape, dtype=bool)
    src_comp[350:450, 350:450] = True

    source_path = tmp_path / "mock_roi_annotations.npz"
    np.savez_compressed(
        source_path,
        image_id=np.array("3079"),
        class_map=np.zeros(shape, dtype=np.uint8),
        overlap_mask=np.zeros(shape, dtype=bool),
        band_indices_zero_based=np.array([18, 52, 69]),
        lesion_bearing_stem_mask=src_stem,
        comparison_stem_mask=src_comp
    )

    # 2. Create mock lesion and unaffected subregions strictly inside src_stem
    lesion_mask = np.zeros(shape, dtype=bool)
    lesion_mask[120:180, 120:180] = True

    unaffected_mask = np.zeros(shape, dtype=bool)
    unaffected_mask[200:260, 200:260] = True

    output_mask_path = tmp_path / "mock_lesion_level.npz"
    np.savez_compressed(
        output_mask_path,
        image_id=np.array("3079"),
        visible_lesion_mask=lesion_mask,
        adjacent_non_lesioned_stem_mask=unaffected_mask,
        lesion_bearing_stem_mask=src_stem,
        comparison_stem_mask=src_comp,
        band_indices_zero_based=np.array([18, 52, 69]),
        lesion_polygon_vertices=np.array([[120, 120], [180, 120], [180, 180], [120, 180]]),
        adjacent_unaffected_polygon_vertices=np.array([[200, 200], [260, 200], [260, 260], [200, 260]])
    )

    # 3. Create mock summary JSON
    summary_path = tmp_path / "mock_summary.json"
    summary_data = {
        "image_id": "3079",
        "roi_pixel_counts": {
            "visible_lesion": int(lesion_mask.sum()),
            "visually_unaffected_adjacent_stem": int(unaffected_mask.sum()),
            "lesion_bearing_stem_total": int(src_stem.sum()),
            "comparison_stem_total": int(src_comp.sum())
        },
        "overlap_pixels": 0
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f)

    # 4. Create dummy figure
    figure_path = tmp_path / "mock_figure.png"
    figure_path.write_bytes(b"dummy_png_bytes")

    # Run validation
    passed, results = validate_saved_annotations(
        output_mask_path=output_mask_path,
        output_summary_path=summary_path,
        output_figure_path=figure_path,
        source_mask_path=source_path,
        verbose=False
    )

    assert passed
    assert results["overall_pass"]
    assert results["zero_overlap_valid"]
    assert results["source_preservation_valid"]


def test_validation_fails_on_overlap(tmp_path):
    """Test validation failure when lesion and unaffected masks overlap."""
    shape = (512, 512)
    src_stem = np.ones(shape, dtype=bool)
    src_comp = np.zeros(shape, dtype=bool)

    source_path = tmp_path / "mock_src.npz"
    np.savez_compressed(
        source_path,
        image_id=np.array("3079"),
        band_indices_zero_based=np.array([18, 52, 69]),
        lesion_bearing_stem_mask=src_stem,
        comparison_stem_mask=src_comp
    )

    # Overlapping regions
    lesion_mask = np.zeros(shape, dtype=bool)
    lesion_mask[50:150, 50:150] = True
    unaffected_mask = np.zeros(shape, dtype=bool)
    unaffected_mask[100:200, 100:200] = True  # Overlaps at [100:150, 100:150]

    output_mask_path = tmp_path / "mock_out.npz"
    np.savez_compressed(
        output_mask_path,
        image_id=np.array("3079"),
        visible_lesion_mask=lesion_mask,
        adjacent_non_lesioned_stem_mask=unaffected_mask,
        lesion_bearing_stem_mask=src_stem,
        comparison_stem_mask=src_comp,
        band_indices_zero_based=np.array([18, 52, 69]),
        lesion_polygon_vertices=np.array([[50, 50], [150, 50], [150, 150]]),
        adjacent_unaffected_polygon_vertices=np.array([[100, 100], [200, 100], [200, 200]])
    )

    summary_path = tmp_path / "mock_sum.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "roi_pixel_counts": {
                "visible_lesion": int(lesion_mask.sum()),
                "visually_unaffected_adjacent_stem": int(unaffected_mask.sum())
            },
            "overlap_pixels": int((lesion_mask & unaffected_mask).sum())
        }, f)

    figure_path = tmp_path / "mock_fig.png"
    figure_path.write_bytes(b"dummy")

    passed, results = validate_saved_annotations(
        output_mask_path=output_mask_path,
        output_summary_path=summary_path,
        output_figure_path=figure_path,
        source_mask_path=source_path,
        verbose=False
    )

    assert not passed
    assert not results["zero_overlap_valid"]
