import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


METADATA_KEY_ALIASES = {
    "plant": "plant_id",
    "plant_id": "plant_id",
    "sample": "sample_id",
    "sample_id": "sample_id",
    "leaf": "leaf_id",
    "leaf_id": "leaf_id",
    "rep": "replicate",
    "replicate": "replicate",
    "replicate_id": "replicate",
    "trial": "trial",
    "date": "date",
    "acquisition_date": "date",
    "timestamp": "timestamp",
    "disease": "disease_label",
    "pathogen": "disease_label",
    "label": "disease_label",
    "class": "disease_label",
    "condition": "disease_label",
    "treatment": "disease_label",
}

CALIBRATION_KEY_TERMS = (
    "calibrat",
    "reflectance",
    "dark",
    "white",
    "reference",
    "panel",
)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_scalar(value):
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        return value
    return str(value)


def _metadata_value(array):
    if array.size > 64:
        return {"shape": list(array.shape), "value_omitted": True}
    return [
        _json_scalar(value)
        for value in np.asarray(array).reshape(-1).tolist()
    ]


def _array_statistics(array):
    result = {
        "total_element_count": int(array.size),
        "finite_element_count": None,
        "nan_count": None,
        "positive_infinity_count": None,
        "negative_infinity_count": None,
        "zero_count": None,
        "negative_value_count": None,
        "above_one_count": None,
        "min_finite": None,
        "max_finite": None,
        "mean_finite": None,
        "std_finite": None,
    }

    if array.dtype.kind not in "biuf":
        return result

    finite = np.isfinite(array)
    finite_values = array[finite]
    result["finite_element_count"] = int(finite.sum())
    result["zero_count"] = int(np.count_nonzero(array == 0))
    result["negative_value_count"] = int(np.count_nonzero(array < 0))
    result["above_one_count"] = int(np.count_nonzero(array > 1))
    if array.dtype.kind == "f":
        result["nan_count"] = int(np.isnan(array).sum())
        result["positive_infinity_count"] = int(np.isposinf(array).sum())
        result["negative_infinity_count"] = int(np.isneginf(array).sum())
    else:
        result["nan_count"] = 0
        result["positive_infinity_count"] = 0
        result["negative_infinity_count"] = 0

    if finite_values.size:
        with np.errstate(over="ignore", invalid="ignore"):
            result["min_finite"] = float(np.min(finite_values))
            result["max_finite"] = float(np.max(finite_values))
            mean = float(np.mean(finite_values, dtype=np.float64))
            std = float(np.std(finite_values, dtype=np.float64))
        result["mean_finite"] = mean if math.isfinite(mean) else None
        result["std_finite"] = std if math.isfinite(std) else None
    return result


def _array_hash(array):
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    header = json.dumps(
        {"dtype": contiguous.dtype.str, "shape": list(contiguous.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest.update(header)
    digest.update(memoryview(contiguous).cast("B"))
    return digest.hexdigest()


def inspect_npz(path: Path):
    path = Path(path)
    arrays = []
    with np.load(path, allow_pickle=False) as archive:
        keys = list(archive.files)
        for key in keys:
            try:
                array = np.asarray(archive[key])
            except ValueError as exc:
                arrays.append({
                    "key": key,
                    "load_error": str(exc),
                    "shape": None,
                    "ndim": None,
                    "dtype": None,
                    "is_numeric": False,
                    "is_3d_cube_candidate": False,
                })
                continue

            is_numeric = (
                np.issubdtype(array.dtype, np.number)
                or np.issubdtype(array.dtype, np.bool_)
            )
            dtype = array.dtype.name
            entry = {
                "key": key,
                "shape": list(array.shape),
                "ndim": int(array.ndim),
                "dtype": dtype,
                "is_numeric": bool(is_numeric),
                "is_3d_cube_candidate": bool(is_numeric and array.ndim == 3),
                "statistics": _array_statistics(array) if is_numeric else None,
                "array_sha256": _array_hash(array) if is_numeric and array.ndim == 3 else None,
                "wavelength_vector_candidate": bool(
                    is_numeric
                    and array.ndim == 1
                    and "wavelength" in key.lower()
                ),
                "possible_calibration_or_reference_key": any(
                    term in key.lower() for term in CALIBRATION_KEY_TERMS
                ),
                "metadata_field": METADATA_KEY_ALIASES.get(key.lower()),
                "metadata_value": (
                    _metadata_value(array)
                    if METADATA_KEY_ALIASES.get(key.lower())
                    else None
                ),
            }
            if entry["wavelength_vector_candidate"]:
                entry["matching_3d_candidate_axes"] = []
            arrays.append(entry)

    cube_candidates = [
        item for item in arrays if item.get("is_3d_cube_candidate")
    ]
    for wavelength in (
        item for item in arrays if item.get("wavelength_vector_candidate")
    ):
        wavelength["matching_3d_candidate_axes"] = [
            {
                "cube_key": cube["key"],
                "axes": [
                    axis
                    for axis, length in enumerate(cube["shape"])
                    if length == wavelength["shape"][0]
                ],
            }
            for cube in cube_candidates
            if wavelength["shape"]
            and any(length == wavelength["shape"][0] for length in cube["shape"])
        ]

    return {
        "filename": path.name,
        "keys": keys,
        "arrays": arrays,
        "numeric_3d_candidate_keys": [item["key"] for item in cube_candidates],
        "cube_candidate_status": (
            "unambiguous" if len(cube_candidates) == 1
            else "ambiguous" if cube_candidates
            else "none"
        ),
        "cube_key": cube_candidates[0]["key"] if len(cube_candidates) == 1 else None,
        "cube_shape": cube_candidates[0]["shape"] if len(cube_candidates) == 1 else None,
        "cube_dtype": cube_candidates[0]["dtype"] if len(cube_candidates) == 1 else None,
        "cube_sha256": (
            cube_candidates[0]["array_sha256"] if len(cube_candidates) == 1 else None
        ),
        "metadata_fields": {
            item["metadata_field"]: item["metadata_value"]
            for item in arrays
            if item.get("metadata_field") and item.get("metadata_value") is not None
        },
        "wavelength_candidate_keys": [
            item["key"]
            for item in arrays
            if item.get("wavelength_vector_candidate")
        ],
        "possible_calibration_or_reference_keys": [
            item["key"]
            for item in arrays
            if item.get("possible_calibration_or_reference_key")
        ],
    }


def compare_cubes(records):
    candidates = [
        record for record in records
        if record.get("cube_candidate_status") == "unambiguous"
    ]
    shapes = [tuple(record["cube_shape"]) for record in candidates]
    dtypes = [record["cube_dtype"] for record in candidates]
    hashes = {}
    for record in candidates:
        hashes.setdefault(record["cube_sha256"], []).append(record["filename"])
    duplicate_groups = [
        {"array_sha256": digest, "filenames": names}
        for digest, names in hashes.items()
        if len(names) > 1
    ]
    return {
        "cube_count": len(candidates),
        "all_cube_shapes_match": bool(shapes) and len(set(shapes)) == 1,
        "all_cube_dtypes_match": bool(dtypes) and len(set(dtypes)) == 1,
        "common_shape": list(shapes[0]) if shapes and len(set(shapes)) == 1 else None,
        "common_dtype": dtypes[0] if dtypes and len(set(dtypes)) == 1 else None,
        "duplicate_groups": duplicate_groups,
    }


def write_array_inventory(records, output_path: Path):
    fields = [
        "filename",
        "official_file_id",
        "source_url",
        "acquisition_timestamp_utc",
        "array_key",
        "shape",
        "dimensions",
        "dtype",
        "is_numeric",
        "is_3d_cube_candidate",
        "cube_candidate_status",
        "actual_file_size_bytes",
        "published_file_size_bytes",
        "official_md5",
        "actual_md5",
        "actual_sha256",
        "array_sha256",
        "min_finite",
        "max_finite",
        "mean_finite",
        "std_finite",
        "finite_element_count",
        "nan_count",
        "positive_infinity_count",
        "negative_infinity_count",
        "zero_count",
        "negative_value_count",
        "above_one_count",
        "wavelength_vector_candidate",
        "matching_3d_candidate_axes",
        "possible_calibration_or_reference_key",
        "metadata_field",
        "metadata_value",
        "source_metadata_mapping",
        "load_error",
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            for array in record["arrays"]:
                stats = array.get("statistics") or {}
                writer.writerow({
                    "filename": record["filename"],
                    "official_file_id": record.get("official_file_id"),
                    "source_url": record.get("source_url"),
                    "acquisition_timestamp_utc": record.get("acquisition_timestamp_utc"),
                    "array_key": array["key"],
                    "shape": json.dumps(array.get("shape")),
                    "dimensions": array.get("ndim"),
                    "dtype": array.get("dtype"),
                    "is_numeric": array.get("is_numeric"),
                    "is_3d_cube_candidate": array.get("is_3d_cube_candidate"),
                    "cube_candidate_status": record.get("cube_candidate_status"),
                    "actual_file_size_bytes": record.get("actual_file_size_bytes"),
                    "published_file_size_bytes": record.get("published_file_size_bytes"),
                    "official_md5": record.get("official_md5"),
                    "actual_md5": record.get("actual_md5"),
                    "actual_sha256": record.get("actual_sha256"),
                    "array_sha256": array.get("array_sha256"),
                    "min_finite": stats.get("min_finite"),
                    "max_finite": stats.get("max_finite"),
                    "mean_finite": stats.get("mean_finite"),
                    "std_finite": stats.get("std_finite"),
                    "finite_element_count": stats.get("finite_element_count"),
                    "nan_count": stats.get("nan_count"),
                    "positive_infinity_count": stats.get("positive_infinity_count"),
                    "negative_infinity_count": stats.get("negative_infinity_count"),
                    "zero_count": stats.get("zero_count"),
                    "negative_value_count": stats.get("negative_value_count"),
                    "above_one_count": stats.get("above_one_count"),
                    "wavelength_vector_candidate": array.get("wavelength_vector_candidate"),
                    "matching_3d_candidate_axes": json.dumps(
                        array.get("matching_3d_candidate_axes")
                    ),
                    "possible_calibration_or_reference_key": array.get(
                        "possible_calibration_or_reference_key"
                    ),
                    "metadata_field": array.get("metadata_field"),
                    "metadata_value": json.dumps(array.get("metadata_value")),
                    "source_metadata_mapping": json.dumps(
                        record.get("source_metadata_mapping")
                    ),
                    "load_error": array.get("load_error"),
                })


def write_manifest(report, output_path: Path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
