"""
Tests for Phase F3 exploratory unsupervised spectral clustering and API endpoints.
"""

from fastapi.testclient import TestClient
import numpy as np
import pytest

from backend.app.main import app
from src.data.analyze_real_cube_clustering import (
    InsufficientClusteringSamplesError,
    InvalidClusteringInputError,
    N_BANDS,
    analyze_cube_clustering,
    build_spectral_axis,
    sample_spatial_grid_indices,
    validate_and_combine_masks,
)


client = TestClient(app)


def _synthetic_cube_and_mask(height: int = 32, width: int = 32, seed: int = 7):
    rng = np.random.default_rng(seed)
    cube = rng.normal(0.4, 0.03, size=(height, width, N_BANDS)).astype(np.float32)
    # Create two spectrally distinct regions inside the ROI
    roi = np.zeros((height, width), dtype=bool)
    roi[4:28, 4:28] = True
    cube[4:16, 4:28, :] += 0.35
    return cube, roi


def test_deterministic_clustering():
    cube, roi = _synthetic_cube_and_mask()
    res1 = analyze_cube_clustering(
        cube=cube,
        image_id="3079",
        region_masks={"stem": roi},
        k_values=(2, 3),
        random_seed=42,
        max_fit_samples=300,
        silhouette_samples=200,
    )
    res2 = analyze_cube_clustering(
        cube=cube,
        image_id="3079",
        region_masks={"stem": roi},
        k_values=(2, 3),
        random_seed=42,
        max_fit_samples=300,
        silhouette_samples=200,
    )
    assert np.array_equal(res1["cluster_maps"][2], res2["cluster_maps"][2])
    assert np.array_equal(res1["cluster_maps"][3], res2["cluster_maps"][3])
    assert res1["k_results"][2]["silhouette_score"] == res2["k_results"][2]["silhouette_score"]


def test_invalid_pixel_handling():
    cube, roi = _synthetic_cube_and_mask()
    # Inject NaN, Inf, and quality-masked pixel inside ROI
    cube[6, 6, 10] = np.nan
    cube[7, 7, 20] = np.inf
    quality_mask = np.zeros(cube.shape[:2], dtype=bool)
    quality_mask[8, 8] = True

    res = analyze_cube_clustering(
        cube=cube,
        image_id="3079",
        region_masks={"stem": roi},
        quality_mask=quality_mask,
        k_values=(2,),
        random_seed=42,
        max_fit_samples=300,
        silhouette_samples=200,
    )
    expected_valid = int(roi.sum()) - 3
    assert res["valid_pixel_count"] == expected_valid
    cmap = res["cluster_maps"][2]
    assert cmap[6, 6] == -1
    assert cmap[7, 7] == -1
    assert cmap[8, 8] == -1
    assert cmap[0, 0] == -1  # outside ROI


def test_cluster_label_shape_and_spatial_mapping():
    cube, roi = _synthetic_cube_and_mask(height=24, width=28)
    res = analyze_cube_clustering(
        cube=cube,
        image_id="3079",
        region_masks={"stem": roi},
        k_values=(2, 3),
        random_seed=42,
        max_fit_samples=200,
        silhouette_samples=150,
    )
    cmap = res["cluster_maps"][3]
    assert cmap.shape == (24, 28)
    assert cmap.dtype == np.int16
    assert np.all(cmap[~roi] == -1)
    assert set(np.unique(cmap[roi])).issubset({0, 1, 2})


def test_reproducible_sampling():
    mask = np.zeros((64, 64), dtype=bool)
    mask[8:56, 8:56] = True
    idx1 = sample_spatial_grid_indices(mask, 250, np.random.default_rng(42), grid_size=16)
    idx2 = sample_spatial_grid_indices(mask, 250, np.random.default_rng(42), grid_size=16)
    assert idx1.shape == (250,)
    assert np.array_equal(idx1, idx2)
    assert len(np.unique(idx1)) == 250
    assert np.all(mask.reshape(-1)[idx1])


def test_per_cube_isolation_and_calibration_guard():
    # 2436 requires verified wavelengths
    with pytest.raises(InvalidClusteringInputError):
        build_spectral_axis("2436", None)

    wl = np.linspace(397.32, 1003.58, N_BANDS)
    axis_2436 = build_spectral_axis("2436", wl)
    assert axis_2436["axis_type"] == "wavelength_nm"

    # 3079 must reject wavelengths
    with pytest.raises(InvalidClusteringInputError):
        build_spectral_axis("3079", wl)

    axis_3079 = build_spectral_axis("3079", None)
    assert axis_3079["axis_type"] == "zero_based_band_index"
    assert axis_3079["values"] == list(range(N_BANDS))


def test_metric_edge_cases_and_posthoc_roi():
    cube, _ = _synthetic_cube_and_mask(height=16, width=16)
    tiny_roi = np.zeros((16, 16), dtype=bool)
    tiny_roi[0, :3] = True
    with pytest.raises(InsufficientClusteringSamplesError):
        analyze_cube_clustering(
            cube=cube,
            image_id="3079",
            region_masks={"tiny": tiny_roi},
            k_values=(2, 3),
        )

    # Overlapping masks should fail validation
    m1 = np.zeros((16, 16), dtype=bool)
    m2 = np.zeros((16, 16), dtype=bool)
    m1[2:8, 2:8] = True
    m2[6:12, 6:12] = True
    with pytest.raises(InvalidClusteringInputError):
        validate_and_combine_masks(cube, {"m1": m1, "m2": m2}, None)

    # Disjoint multi-region ROI produces post-hoc comparison
    m2_disjoint = np.zeros((16, 16), dtype=bool)
    m2_disjoint[9:14, 9:14] = True
    res = analyze_cube_clustering(
        cube=cube,
        image_id="3079",
        region_masks={"r1": m1, "r2": m2_disjoint},
        k_values=(2,),
        max_fit_samples=50,
        silhouette_samples=40,
    )
    assert "posthoc_roi_comparison" in res["k_results"][2]
    assert "contingency_counts" in res["k_results"][2]["posthoc_roi_comparison"]


def test_clustering_api_integration():
    res_cubes = client.get("/api/clustering/cubes")
    assert res_cubes.status_code == 200
    cubes = res_cubes.json()
    assert len(cubes) == 3
    by_id = {c["image_id"]: c for c in cubes}
    assert by_id["2436"]["available"] is True
    assert by_id["3079"]["available"] is True
    assert by_id["2973"]["available"] is False

    # 2973 summary returns 404
    assert client.get("/api/clustering/2973/summary").status_code == 404
    assert client.get("/api/clustering/9999/summary").status_code == 404

    # 2436 profiles & spatial map
    prof_2436 = client.get("/api/clustering/2436/profiles?k=3")
    assert prof_2436.status_code == 200
    p_data = prof_2436.json()
    assert p_data["spectral_axis"]["axis_type"] == "wavelength_nm"
    assert len(p_data["clusters"]) == 3
    assert len(p_data["clusters"][0]["mean_profile"]) == N_BANDS

    # 3079 spatial map & axis check
    map_3079 = client.get("/api/clustering/3079/spatial-map?k=3&max_size=32")
    assert map_3079.status_code == 200
    m_data = map_3079.json()
    assert m_data["spectral_axis"]["axis_type"] == "zero_based_band_index"
    assert m_data["downsampled_width"] == 32
    assert m_data["downsampled_height"] == 32

    # Phase F3 reports exposed in /api/reports
    reports = client.get("/api/reports").json()
    report_ids = {r["id"] for r in reports}
    assert "phase_f3_unsupervised_clustering" in report_ids
    assert "phase_f3_unsupervised_clustering_report" in report_ids


def test_api_matches_saved_artifacts():
    import json
    from pathlib import Path

    for img in ("2436", "3079"):
        saved = json.loads(Path(f"data/processed/clustering/{img}_summary.json").read_text(encoding="utf-8"))
        api_res = client.get(f"/api/clustering/{img}/summary").json()
        assert api_res["valid_pixel_count"] == saved["valid_pixel_count"]
        assert api_res["fit_sample_count"] == saved["fit_sample_count"]
        for k_str, kr in saved["k_results"].items():
            assert api_res["k_results"][k_str]["silhouette_score"] == kr["silhouette_score"]
            assert api_res["k_results"][k_str]["spatial_block_stability_ari"] == kr["spatial_block_stability_ari"]


def test_f3_1_audit_report_integrity():
    import json
    from pathlib import Path

    audit_path = Path("data/processed/reports/phase_f3_1_methodology_audit.json")
    assert audit_path.is_file()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["phase"] == "F3.1"
    for img in ("2436", "3079"):
        assert audit["cubes"][img]["reproducibility"]["all_exact_match"] is True
        assert audit["cubes"][img]["contiguous_spatial_validation"]["north_to_south_buffered"]["buffer_pixels"] == 32
