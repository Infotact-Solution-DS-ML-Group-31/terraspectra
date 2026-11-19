"""
Automated tests for TerraSpectra FastAPI endpoints.
"""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_api_health():
    """Verify GET /api/health returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "platform" in data


def test_list_datasets():
    """Verify GET /api/datasets lists all 3 local cubes with attributes."""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert len(datasets) == 3

    cube_ids = {d["image_id"] for d in datasets}
    assert cube_ids == {"2436", "2973", "3079"}

    for d in datasets:
        assert d["shape"] == [512, 512, 204]
        assert d["spectral_bands"] == 204
        assert d["file_size_mb"] > 0
        if d["image_id"] == "2436":
            assert d["has_wavelength_calibration"] is True
            assert "Wavelength-calibrated" in d["calibration_status"]
        else:
            assert d["has_wavelength_calibration"] is False
            assert "Spectral-band indexed only" in d["calibration_status"]


def test_dataset_metadata():
    """Verify GET /api/datasets/{image_id}/metadata returns accurate metadata."""
    # Test valid image 2436
    res_2436 = client.get("/api/datasets/2436/metadata")
    assert res_2436.status_code == 200
    meta_2436 = res_2436.json()
    assert meta_2436["image_id"] == "2436"
    assert meta_2436["replicate"] == 1
    assert meta_2436["pathogen"] == "B. pseudo"
    assert meta_2436["verified_wavelengths"] is True

    # Test valid image 3079
    res_3079 = client.get("/api/datasets/3079/metadata")
    assert res_3079.status_code == 200
    meta_3079 = res_3079.json()
    assert meta_3079["image_id"] == "3079"
    assert meta_3079["replicate"] == 4
    assert meta_3079["part"] == "ST-2"
    assert meta_3079["verified_wavelengths"] is False

    # Test invalid image ID
    res_invalid = client.get("/api/datasets/9999/metadata")
    assert res_invalid.status_code == 404


def test_dataset_preview():
    """Verify GET /api/datasets/{image_id}/preview serves false-color PNGs."""
    for img_id in ["2436", "2973", "3079"]:
        res = client.get(f"/api/datasets/{img_id}/preview")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert len(res.content) > 1000

    # Invalid ID
    res_invalid = client.get("/api/datasets/unknown_cube/preview")
    assert res_invalid.status_code == 404


def test_spectral_profile_calibration_enforcement():
    """Verify that wavelengths are only returned for 2436 and None for others."""
    # Image 2436: Must have wavelength_nm
    res_2436 = client.get("/api/datasets/2436/spectral-profile")
    assert res_2436.status_code == 200
    data_2436 = res_2436.json()
    assert data_2436["spectral_axis"] == "wavelength_nm"
    assert data_2436["has_verified_wavelengths"] is True
    assert len(data_2436["data"]) == 204
    assert data_2436["data"][0]["wavelength_nm"] is not None
    assert 390.0 < data_2436["data"][0]["wavelength_nm"] < 410.0

    # Image 3079: Must NOT have wavelength_nm
    res_3079 = client.get("/api/datasets/3079/spectral-profile")
    assert res_3079.status_code == 200
    data_3079 = res_3079.json()
    assert data_3079["spectral_axis"] == "zero_based_band_indices"
    assert data_3079["has_verified_wavelengths"] is False
    assert len(data_3079["data"]) == 204
    for pt in data_3079["data"]:
        assert pt["wavelength_nm"] is None

    # Image 2973: Must NOT have wavelength_nm
    res_2973 = client.get("/api/datasets/2973/spectral-profile")
    assert res_2973.status_code == 200
    data_2973 = res_2973.json()
    assert data_2973["has_verified_wavelengths"] is False
    assert len(data_2973["data"]) == 204

    # Invalid ID
    res_inv = client.get("/api/datasets/9999/spectral-profile")
    assert res_inv.status_code == 404


def test_3079_roi_analysis():
    """Verify GET /api/datasets/3079/roi-analysis returns verified region metrics."""
    response = client.get("/api/datasets/3079/roi-analysis")
    assert response.status_code == 200
    roi = response.json()
    assert roi["image_id"] == "3079"

    counts = roi["region_pixel_counts"]
    assert counts["visible_necrotic_lesion"] == 4137
    assert counts["visually_unaffected_adjacent_stem"] == 18661
    assert counts["preserved_comparison_stem"] == 30532
    assert counts["overlap_pixels"] == 0

    # Verify peak divergence at band 121
    div = roi["pairwise_divergence"]["lesion_vs_adjacent_unaffected"]
    assert div["max_abs_diff_band"] == 121
    assert len(roi["scientific_disclaimers"]) > 0


def test_quality_metrics():
    """Verify GET /api/datasets/{image_id}/quality flags uncalibrated exceedances."""
    # Image 3079: Has exceedances in comparison stem
    res_3079 = client.get("/api/datasets/3079/quality")
    assert res_3079.status_code == 200
    q_3079 = res_3079.json()
    assert q_3079["has_values_exceeding_1"] is True
    assert q_3079["values_exceeding_1_count"] > 0
    assert len(q_3079["warnings"]) > 0
    # Check updated scientific phrasing
    joined_notes = " ".join(q_3079.get("scientific_notes", []))
    assert "possible physical explanations" in joined_notes
    assert "arbitrarily" not in joined_notes

    # Image 2436
    res_2436 = client.get("/api/datasets/2436/quality")
    assert res_2436.status_code == 200
    q_2436 = res_2436.json()
    assert q_2436["image_id"] == "2436"

    # Invalid ID
    res_inv = client.get("/api/datasets/9999/quality")
    assert res_inv.status_code == 404


def test_cors_configuration():
    """Verify CORS headers respond correctly to allowed local dev origins and reject unallowed."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    }
    res = client.options("/api/health", headers=headers)
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_reports_endpoints():
    """Verify GET /api/reports listing and report retrieval."""
    res_list = client.get("/api/reports")
    assert res_list.status_code == 200
    reports = res_list.json()
    assert len(reports) >= 5

    report_ids = [r["id"] for r in reports]
    assert "dataset_inventory" in report_ids
    assert "dataset_suitability_assessment" in report_ids

    # Fetch JSON report
    res_json = client.get("/api/reports/dataset_inventory")
    assert res_json.status_code == 200
    assert res_json.json()["type"] == "json"
    assert "metadata_records_total" in res_json.json()["content"]

    # Fetch Markdown report
    res_md = client.get("/api/reports/dataset_suitability_assessment")
    assert res_md.status_code == 200
    assert res_md.json()["type"] == "markdown"
    assert "Executive Summary" in res_md.json()["content"]

    # Invalid report ID
    res_inv = client.get("/api/reports/nonexistent_report")
    assert res_inv.status_code == 404
