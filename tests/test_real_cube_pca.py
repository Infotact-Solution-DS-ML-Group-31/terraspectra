import numpy as np
import pytest

from src.data.analyze_real_cube_pca import (
    InsufficientValidPixelsError,
    _batch_slices,
    _sample_spatially,
    analyze_cube_array,
    spectral_axis,
)


def make_cube(seed=3, shape=(12, 14, 204)):
    rng = np.random.default_rng(seed)
    return rng.normal(size=shape).astype(np.float32)


def test_pca_output_dimensions_and_masked_score_map():
    cube = make_cube()
    roi = np.zeros(cube.shape[:2], dtype=bool)
    roi[2:10, 3:12] = True
    quality = np.zeros(cube.shape, dtype=bool)
    quality[4, 5, 17] = True

    result = analyze_cube_array(
        cube,
        "3079",
        {"annotated": roi},
        quality_mask=quality,
        random_seed=5,
        max_samples=30,
        batch_size=9,
    )

    assert result["score_map"].shape == (12, 14, 3)
    assert result["components"].shape == (3, 204)
    assert result["explained_variance_ratio"].shape == (3,)
    assert np.isnan(result["score_map"][~roi]).all()
    assert np.isnan(result["score_map"][4, 5]).all()
    assert np.isfinite(result["score_map"][roi & ~quality.any(axis=2)]).all()


def test_deterministic_spatial_sampling():
    mask = np.ones((70, 90), dtype=bool)
    first = _sample_spatially(mask, 111, np.random.default_rng(42))
    second = _sample_spatially(mask, 111, np.random.default_rng(42))

    np.testing.assert_array_equal(first, second)
    assert np.unique(first).size == 111
    assert np.all(mask.ravel()[first])


def test_nonfinite_spectra_are_left_missing():
    cube = make_cube()
    cube[3, 4, 10] = np.nan
    roi = np.ones(cube.shape[:2], dtype=bool)

    result = analyze_cube_array(
        cube, "3079", {"roi": roi}, max_samples=30, batch_size=10
    )

    assert np.isnan(result["score_map"][3, 4]).all()
    assert result["metadata"]["valid_pixel_count"] == roi.size - 1


def test_insufficient_valid_pixels_are_reported():
    cube = make_cube(shape=(2, 1, 204))
    roi = np.ones(cube.shape[:2], dtype=bool)

    with pytest.raises(InsufficientValidPixelsError):
        analyze_cube_array(cube, "3079", {"roi": roi}, max_samples=2)


def test_incremental_fit_and_transform_respect_batch_size():
    cube = make_cube(shape=(20, 20, 204))
    roi = np.ones(cube.shape[:2], dtype=bool)
    result = analyze_cube_array(
        cube, "3079", {"roi": roi}, max_samples=47, batch_size=10
    )

    assert result["metadata"]["fit_batch_count"] > 1
    assert result["metadata"]["transform_batch_count"] > 1
    assert all(
        batch.stop - batch.start <= 10
        for batch in _batch_slices(47, 10)
    )
    assert all(
        batch.stop - batch.start >= 3
        for batch in _batch_slices(47, 10)
    )


def test_band_index_metadata_never_borrows_2436_wavelengths():
    wavelength = np.linspace(397.32, 1003.58, 204)
    calibrated = spectral_axis("2436", wavelength)
    indexed = spectral_axis("3079", None)
    indexed_2973 = spectral_axis("2973", None)

    assert calibrated["axis_type"] == "wavelength_nm"
    assert calibrated["values"][0] == pytest.approx(397.32)
    assert calibrated["values"][-1] == pytest.approx(1003.58)
    assert indexed["axis_type"] == "zero_based_band_index"
    assert indexed["values"] == list(range(204))
    assert indexed_2973["axis_type"] == "zero_based_band_index"
    with pytest.raises(ValueError, match="Do not assign"):
        spectral_axis("3079", wavelength)


def test_region_balancing_and_independent_cube_fits():
    cube_a = make_cube(seed=10, shape=(18, 18, 204))
    cube_b = make_cube(seed=11, shape=(18, 18, 204)) + 4
    regions = {
        "small": np.zeros((18, 18), dtype=bool),
        "medium": np.zeros((18, 18), dtype=bool),
        "large": np.ones((18, 18), dtype=bool),
    }
    regions["small"][0:3, 0:3] = True
    regions["medium"][4:10, 4:10] = True
    # Make the masks disjoint, as required for region-wise quotas.
    regions["large"][0:10, 0:10] = False

    fit_a = analyze_cube_array(
        cube_a, "3079", regions, max_samples=60, random_seed=19, batch_size=12
    )
    fit_b = analyze_cube_array(
        cube_b, "2436", regions, wavelengths_nm=np.linspace(397.32, 1003.58, 204),
        max_samples=60, random_seed=19, batch_size=12
    )

    counts = fit_a["metadata"]["fit_sample_counts_by_region"]
    assert len(set(counts.values())) == 1
    assert fit_a["metadata"]["image_id"] != fit_b["metadata"]["image_id"]
    assert not np.allclose(fit_a["components"], fit_b["components"])


def test_values_above_one_are_not_clipped_or_filtered():
    cube = make_cube()
    cube[2, 3, 4] = 1.25
    roi = np.ones(cube.shape[:2], dtype=bool)
    result = analyze_cube_array(
        cube, "3079", {"roi": roi}, max_samples=20, batch_size=8
    )

    assert cube[2, 3, 4] == pytest.approx(1.25)
    assert result["metadata"]["threshold_at_1_applied"] is False
    assert result["metadata"]["valid_pixel_count"] == roi.size


def test_raw_array_is_not_mutated():
    cube = make_cube()
    original = cube.copy()
    roi = np.ones(cube.shape[:2], dtype=bool)

    analyze_cube_array(cube, "3079", {"roi": roi}, max_samples=30, batch_size=10)

    np.testing.assert_array_equal(cube, original)
