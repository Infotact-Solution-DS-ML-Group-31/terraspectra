from pathlib import Path
import json

import numpy as np
import pytest
from scipy.io import savemat

from src.data.inspect_external_zenodo_dataset import (
    canonical_array_hash,
    duplicate_groups,
    inspect_mat,
    md5_file,
    numeric_statistics,
)


def write_mat(tmp_path: Path, name: str, variables: dict) -> Path:
    path = tmp_path / name
    savemat(path, variables)
    return path


def test_valid_mat_inspection(tmp_path):
    path = write_mat(tmp_path, "valid.mat", {"cube": np.ones((3, 4, 5), dtype=np.float32)})
    result = inspect_mat(path)
    assert result["candidate_cube_status"] == "unambiguous"
    assert result["numeric_3d_candidate_count"] == 1
    assert result["variables"][0]["dimensions"] == [3, 4, 5]


def test_missing_file_handling(tmp_path):
    result = inspect_mat(tmp_path / "missing.mat")
    assert "missing" in result["inspection_error"].lower()
    assert result["variables"] == []


def test_checksum_mismatch_and_match(tmp_path):
    path = write_mat(tmp_path, "sum.mat", {"cube": np.ones((2, 2, 2))})
    assert md5_file(path) == md5_file(path)
    path.write_bytes(path.read_bytes() + b"x")
    assert md5_file(path) != md5_file(write_mat(tmp_path, "other.mat", {"cube": np.ones((2, 2, 2))}))


def test_ambiguous_multiple_3d_cube_handling(tmp_path):
    path = write_mat(tmp_path, "ambiguous.mat", {
        "a": np.ones((2, 3, 4)),
        "b": np.zeros((2, 3, 4)),
    })
    result = inspect_mat(path)
    assert result["candidate_cube_status"] == "ambiguous"
    assert result["numeric_3d_candidate_count"] == 2


def test_nan_infinity_negative_zero_statistics():
    cube = np.array([[[np.nan, np.inf, -np.inf, -2.0, 0.0, 3.0]]])
    stats = numeric_statistics(cube)
    assert stats["nan_count"] == 1
    assert stats["positive_infinity_count"] == 1
    assert stats["negative_infinity_count"] == 1
    assert stats["negative_value_count"] == 1
    assert stats["zero_count"] == 1
    assert stats["total_element_count"] == 6


def test_all_invalid_statistics():
    stats = numeric_statistics(np.array([[[np.nan, np.inf, -np.inf]]]))
    assert stats["finite_element_count"] == 0
    assert stats["min_finite"] is None
    assert stats["mean_finite"] is None


def test_deterministic_array_hashing():
    a = np.arange(24, dtype=np.float64).reshape(2, 3, 4)
    b = a.copy()
    c = a + 1
    assert canonical_array_hash(a) == canonical_array_hash(b)
    assert canonical_array_hash(a) != canonical_array_hash(c)


def test_exact_duplicate_detection_and_different_arrays():
    records = [
        {"filename": "a.mat", "cube_hash": canonical_array_hash(np.ones((2, 2, 2)))},
        {"filename": "b.mat", "cube_hash": canonical_array_hash(np.ones((2, 2, 2)))},
        {"filename": "c.mat", "cube_hash": canonical_array_hash(np.zeros((2, 2, 2)))},
    ]
    groups, mapping = duplicate_groups(records)
    assert len(groups) == 2
    assert mapping["a.mat"]["duplicate_group_id"] == mapping["b.mat"]["duplicate_group_id"]
    assert mapping["c.mat"]["duplicate_group_id"] != mapping["a.mat"]["duplicate_group_id"]
    assert mapping["a.mat"]["is_unique_array"] is True
    assert mapping["b.mat"]["is_unique_array"] is False


def test_duplicate_aware_class_counts():
    records = [
        {"filename": "a.mat", "provisional_class": "A", "cube_hash": "x",
         "cube_statistics": {"mean_finite": 1.0, "std_finite": 0.1, "min_finite": 0.0, "max_finite": 2.0}},
        {"filename": "b.mat", "provisional_class": "A", "cube_hash": "x",
         "cube_statistics": {"mean_finite": 1.0, "std_finite": 0.1, "min_finite": 0.0, "max_finite": 2.0}},
        {"filename": "c.mat", "provisional_class": "A", "cube_hash": "y",
         "cube_statistics": {"mean_finite": 3.0, "std_finite": 0.2, "min_finite": 2.0, "max_finite": 4.0}},
    ]
    from src.data.inspect_external_zenodo_dataset import class_counts
    counts = class_counts(records)
    assert counts["A"]["file_count"] == 3
    assert counts["A"]["unique_array_count"] == 2


def test_json_serialization_without_nan_or_infinity(tmp_path):
    report = {"stats": numeric_statistics(np.array([[[np.nan, np.inf, -1.0, 0.0]]]))}
    text = json.dumps(report, allow_nan=False)
    assert "NaN" not in text
    assert "Infinity" not in text


def test_run_never_writes_raw_directory(tmp_path, monkeypatch):
    import src.data.inspect_external_zenodo_dataset as inspector

    raw_root = tmp_path / "raw"
    botrytis_dir = raw_root / "botrytis_cinerea"
    botrytis_dir.mkdir(parents=True)
    mat_path = write_mat(
        botrytis_dir,
        "Botrytis_cinerea_test.mat",
        {"cube": np.ones((2, 3, 4), dtype=np.float32)},
    )
    before = mat_path.read_bytes()

    manifest_dir = tmp_path / "reports"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "manifest.json"
    manifest_path.write_text(json.dumps({
        "source_doi": "10.5281/test",
        "record_version": "test",
        "license": "cc-by-4.0",
        "files": [{
            "filename": mat_path.name,
            "class": "Botrytis cinerea",
            "checksum": "md5:" + md5_file(mat_path),
            "file_id": "test-id",
        }],
    }), encoding="utf-8")

    monkeypatch.setattr(inspector, "RAW_ROOT", raw_root)
    monkeypatch.setattr(inspector, "ROOT", tmp_path)
    monkeypatch.setattr(inspector, "REPORTS_DIR", manifest_dir)
    monkeypatch.setattr(inspector, "PROFILE_DIR", tmp_path / "profiles")
    monkeypatch.setattr(inspector, "JSON_REPORT", manifest_dir / "report.json")
    monkeypatch.setattr(inspector, "INVENTORY_CSV", manifest_dir / "inventory.csv")
    monkeypatch.setattr(inspector, "DUPLICATE_CSV", manifest_dir / "duplicates.csv")
    monkeypatch.setattr(inspector, "DOC_REPORT", tmp_path / "report.md")

    report = inspector.run_inspection(manifest_path)

    assert mat_path.read_bytes() == before
    assert report["raw_input_immutability"]["verified"] is True
    assert not any(p.is_relative_to(raw_root) for p in (
        inspector.JSON_REPORT,
        inspector.INVENTORY_CSV,
        inspector.DUPLICATE_CSV,
        inspector.PROFILE_DIR,
    ))
