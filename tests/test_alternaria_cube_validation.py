import csv
import json

import numpy as np

from src.data.inspect_alternaria_cubes import (
    compare_cubes,
    inspect_npz,
    write_array_inventory,
    write_manifest,
)


def test_inspection_reports_array_statistics_without_assigning_axis_order(tmp_path):
    cube = np.array(
        [[[1.0, np.nan, 3.0], [np.inf, 5.0, 7.0]]],
        dtype=np.float32,
    )
    wavelengths = np.array([400.0, 500.0, 600.0], dtype=np.float32)
    path = tmp_path / "fixture.npz"
    np.savez(
        path,
        cube=cube,
        wavelengths_nm=wavelengths,
        plant_id=np.array(["065/I"]),
    )

    result = inspect_npz(path)

    assert result["keys"] == ["cube", "wavelengths_nm", "plant_id"]
    assert result["cube_candidate_status"] == "unambiguous"
    assert result["cube_shape"] == [1, 2, 3]
    assert result["cube_dtype"] == np.dtype(np.float32).name
    assert result["metadata_fields"] == {"plant_id": ["065/I"]}
    wavelength = next(
        array for array in result["arrays"]
        if array["key"] == "wavelengths_nm"
    )
    assert wavelength["wavelength_vector_candidate"] is True
    assert wavelength["matching_3d_candidate_axes"] == [
        {"cube_key": "cube", "axes": [2]}
    ]
    stats = result["arrays"][0]["statistics"]
    assert stats["nan_count"] == 1
    assert stats["positive_infinity_count"] == 1
    assert stats["finite_element_count"] == 4
    assert stats["min_finite"] == 1.0
    assert stats["max_finite"] == 7.0


def test_comparison_detects_exact_duplicate_cube_arrays(tmp_path):
    cube = np.arange(24, dtype=np.uint16).reshape(2, 3, 4)
    first = tmp_path / "first.npz"
    second = tmp_path / "second.npz"
    third = tmp_path / "third.npz"
    np.savez(first, cube=cube)
    np.savez(second, cube=cube.copy())
    np.savez(third, cube=cube + 1)

    records = [inspect_npz(path) for path in (first, second, third)]
    comparison = compare_cubes(records)

    assert comparison["cube_count"] == 3
    assert comparison["all_cube_shapes_match"] is True
    assert comparison["all_cube_dtypes_match"] is True
    assert len(comparison["duplicate_groups"]) == 1
    assert comparison["duplicate_groups"][0]["filenames"] == [
        "first.npz",
        "second.npz",
    ]


def test_pickle_arrays_are_not_loaded_and_inventory_is_serializable(tmp_path):
    path = tmp_path / "object.npz"
    np.savez(
        path,
        cube=np.ones((2, 2, 2), dtype=np.float32),
        metadata=np.array([{"unsafe": True}], dtype=object),
    )

    record = inspect_npz(path)
    object_array = next(item for item in record["arrays"] if item["key"] == "metadata")
    assert "allow_pickle" in object_array["load_error"]

    csv_path = tmp_path / "inventory.csv"
    record.update({
        "actual_file_size_bytes": path.stat().st_size,
        "published_file_size_bytes": 1,
        "official_md5": "expected",
        "actual_md5": "actual",
        "actual_sha256": "sha256",
    })
    write_array_inventory([record], csv_path)

    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert {row["array_key"] for row in rows} == {"cube", "metadata"}
    manifest_path = tmp_path / "manifest.json"
    write_manifest({"files": [record]}, manifest_path)
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["files"][0]["filename"] == "object.npz"
