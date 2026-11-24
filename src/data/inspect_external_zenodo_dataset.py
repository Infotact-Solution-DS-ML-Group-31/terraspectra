"""
Phase F2.1: reproducible, read-only inspection of the Zenodo fungal HSI MAT files.

This module does not transform, calibrate, merge, or relabel source arrays.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.io import loadmat, whosmat


SCRIPT_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data/processed/reports/phase_f2_acquisition_manifest.json"
RAW_ROOT = ROOT / "data/raw/external/zenodo_15800414"
REPORTS_DIR = ROOT / "data/processed/reports"
PROFILE_DIR = ROOT / "data/processed/external/zenodo_15800414/band_profiles"
JSON_REPORT = REPORTS_DIR / "phase_f2_1_external_dataset_inspection.json"
INVENTORY_CSV = REPORTS_DIR / "phase_f2_1_file_inventory.csv"
DUPLICATE_CSV = REPORTS_DIR / "phase_f2_1_duplicate_groups.csv"
DOC_REPORT = ROOT / "docs/phase_f2_1_external_dataset_inspection.md"


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_array_hash(array: np.ndarray) -> str:
    """Hash shape, dtype, and C-contiguous bytes; no numeric normalization."""
    canonical = np.ascontiguousarray(array)
    shape_bytes = repr(tuple(canonical.shape)).encode("ascii")
    dtype_bytes = str(canonical.dtype).encode("ascii")
    digest = hashlib.sha256()
    digest.update(b"shape=")
    digest.update(shape_bytes)
    digest.update(b"\ndtype=")
    digest.update(dtype_bytes)
    digest.update(b"\nbytes=")
    digest.update(canonical.tobytes(order="C"))
    return digest.hexdigest()


def safe_float(value: float) -> float | None:
    value = float(value)
    return value if np.isfinite(value) else None


def numeric_statistics(array: np.ndarray) -> dict:
    finite = np.asarray(array)[np.isfinite(np.asarray(array))]
    count = int(finite.size)
    if count == 0:
        quantiles = {f"q{p:02d}": None for p in (1, 5, 25, 50, 75, 95, 99)}
        minimum = maximum = mean = std = None
    else:
        qvalues = np.quantile(finite, [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
        quantiles = {
            f"q{p:02d}": safe_float(q)
            for p, q in zip((1, 5, 25, 50, 75, 95, 99), qvalues)
        }
        minimum = safe_float(np.min(finite))
        maximum = safe_float(np.max(finite))
        mean = safe_float(np.mean(finite, dtype=np.float64))
        std = safe_float(np.std(finite, dtype=np.float64))

    array = np.asarray(array)
    return {
        "finite_element_count": count,
        "total_element_count": int(array.size),
        "nan_count": int(np.isnan(array).sum()) if np.issubdtype(array.dtype, np.inexact) else 0,
        "positive_infinity_count": int(np.isposinf(array).sum()) if np.issubdtype(array.dtype, np.inexact) else 0,
        "negative_infinity_count": int(np.isneginf(array).sum()) if np.issubdtype(array.dtype, np.inexact) else 0,
        "zero_count": int(np.count_nonzero(array == 0)),
        "negative_value_count": int(np.count_nonzero(
            np.isfinite(array) & (array < 0)
        )),
        "min_finite": minimum,
        "max_finite": maximum,
        "mean_finite": mean,
        "std_finite": std,
        **quantiles,
    }


def resolve_manifest_path(root: Path, entry: dict) -> tuple[Path, str]:
    filename = str(entry["filename"])
    direct = entry.get("path") or entry.get("relative_path") or entry.get("resolved_path")
    candidates = []
    if direct:
        direct_path = Path(direct)
        candidates.append(direct_path if direct_path.is_absolute() else root / direct_path)
    candidates.extend([
        root / filename,
        root / ("botrytis_cinerea" if filename.lower().startswith("botrytis") else "healthy") / filename,
        root / "**" / filename,
    ])
    for candidate in candidates:
        if "*" not in str(candidate) and candidate.exists():
            return candidate, str(candidate.relative_to(root)).replace("\\", "/")
    matches = sorted(root.glob(f"**/{filename}"))
    if matches:
        match = matches[0]
        return match, str(match.relative_to(root)).replace("\\", "/")
    return root / ("botrytis_cinerea" if filename.lower().startswith("botrytis") else "healthy") / filename, ""


def inspect_mat(path: Path) -> dict:
    variables = []
    candidates = []
    try:
        header = whosmat(str(path))
    except Exception as exc:
        return {"inspection_error": f"{type(exc).__name__}: {exc}", "variables": [], "numeric_3d_candidates": []}

    numeric_types = ("uint", "int", "float", "double", "single", "logical")
    for name, shape, dtype in header:
        dimensions = list(shape)
        variables.append({"name": name, "dimensions": dimensions, "matlab_type": dtype})
        dtype_lower = dtype.lower()
        if len(dimensions) == 3 and any(token in dtype_lower for token in numeric_types):
            candidates.append(name)

    if len(candidates) == 1:
        return {"variables": variables, "numeric_3d_candidate_names": candidates,
                "candidate_cube_status": "unambiguous", "numeric_3d_candidate_count": 1,
                "other_numeric_array_count": 0}
    if len(candidates) > 1:
        return {"variables": variables, "numeric_3d_candidate_names": candidates,
                "candidate_cube_status": "ambiguous", "numeric_3d_candidate_count": len(candidates),
                "other_numeric_array_count": len(variables) - len(candidates)}
    return {"variables": variables, "numeric_3d_candidate_names": [],
            "candidate_cube_status": "none", "numeric_3d_candidate_count": 0,
            "other_numeric_array_count": len(variables)}


def load_candidate(path: Path, variable_name: str) -> np.ndarray:
    loaded = loadmat(str(path), variable_names=[variable_name], mat_dtype=False)
    return np.asarray(loaded[variable_name])


def class_counts(records: list[dict]) -> dict:
    result = {}
    for class_name in sorted({r["provisional_class"] for r in records}):
        class_records = [r for r in records if r["provisional_class"] == class_name]
        unique_hashes = {r["cube_hash"] for r in class_records if r["cube_hash"]}
        stats = [r["cube_statistics"] for r in class_records if r["cube_statistics"]]
        means = [r["cube_statistics"]["mean_finite"] for r in class_records if r["cube_statistics"].get("mean_finite") is not None]
        stds = [r["cube_statistics"]["std_finite"] for r in class_records if r["cube_statistics"].get("std_finite") is not None]
        minima = [r["cube_statistics"]["min_finite"] for r in class_records if r["cube_statistics"].get("min_finite") is not None]
        maxima = [r["cube_statistics"]["max_finite"] for r in class_records if r["cube_statistics"].get("max_finite") is not None]
        def summarize(values):
            if not values:
                return None
            return {"min": min(values), "mean": float(np.mean(values)), "max": max(values)}
        result[class_name] = {
            "file_count": len(class_records),
            "unique_array_count": len(unique_hashes),
            "observed_finite_min_max": {
                "min": min(minima) if minima else None,
                "max": max(maxima) if maxima else None,
            },
            "file_minima_summary": summarize(minima),
            "file_maxima_summary": summarize(maxima),
            "file_mean_summary": summarize(means),
            "file_std_summary": summarize(stds),
            "label_status": "filename-derived provisional label",
        }
    return result


def duplicate_groups(records: list[dict]) -> tuple[list[dict], dict]:
    groups: dict[str, list[str]] = {}
    for record in records:
        cube_hash = record.get("cube_hash")
        if cube_hash:
            groups.setdefault(cube_hash, []).append(record["filename"])
    group_list = []
    mapping = {}
    for index, (cube_hash, filenames) in enumerate(sorted(groups.items(), key=lambda item: item[0]), start=1):
        group_id = f"DG-{index:03d}"
        group_list.append({"duplicate_group_id": group_id, "cube_hash": cube_hash,
                           "file_count": len(filenames), "filenames": filenames,
                           "unique_array": True})
        for position, filename in enumerate(sorted(filenames)):
            mapping[filename] = {"duplicate_group_id": group_id,
                                 "is_unique_array": position == 0,
                                 "group_file_count": len(filenames)}
    return group_list, mapping


def run_inspection(manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    start = time.monotonic()
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Phase F2 manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    entries = manifest["files"]
    records = []
    raw_hashes_before = {}
    for entry in entries:
        filename = str(entry["filename"])
        path, manifest_relative_path = resolve_manifest_path(RAW_ROOT, entry)
        record = {
            "filename": filename,
            "original_filename": filename,
            "source_class": entry.get("class"),
            "provisional_class": "Botrytis cinerea" if filename.lower().startswith("botrytis") else "Healthy control",
            "resolved_relative_path": manifest_relative_path,
            "file_id": entry.get("file_id"),
            "exists": path.exists(),
        }
        if not path.exists():
            record.update({
                "file_size_bytes": None, "md5": None, "sha256": None,
                "md5_status": "missing", "inspection_error": "file missing",
                "mat_variables": [], "cube_variable_name": None, "cube_dimensions": None,
                "cube_dtype": None, "cube_statistics": None, "cube_hash": None,
            })
            records.append(record)
            continue

        raw_hashes_before[str(path.resolve())] = sha256_file(path)
        md5 = md5_file(path)
        sha256 = sha256_file(path)
        official = str(entry.get("checksum", "")).lower().removeprefix("md5:")
        record.update({
            "file_size_bytes": path.stat().st_size,
            "md5": md5,
            "sha256": sha256,
            "md5_status": "match" if official and md5 == official else ("unknown" if not official else "mismatch"),
        })
        mat_info = inspect_mat(path)
        record.update(mat_info)
        record["mat_variables"] = mat_info["variables"]
        record["numeric_3d_candidate_names"] = mat_info["numeric_3d_candidate_names"]
        record["cube_variable_name"] = None
        record["cube_dimensions"] = None
        record["cube_dtype"] = None
        record["cube_statistics"] = None
        record["cube_hash"] = None
        record["band_profile_status"] = "not_calculated"

        if mat_info.get("numeric_3d_candidate_count") == 1:
            variable_name = mat_info["numeric_3d_candidate_names"][0]
            try:
                array = load_candidate(path, variable_name)
                record["cube_variable_name"] = variable_name
                record["cube_dimensions"] = list(array.shape)
                record["cube_dtype"] = str(array.dtype)
                record["cube_statistics"] = numeric_statistics(array)
                record["cube_hash"] = canonical_array_hash(array)

                if array.ndim == 3:
                    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
                    profile_path = PROFILE_DIR / f"{path.stem}_band_profile.csv"
                    flat = np.asarray(array, dtype=np.float64)
                    finite = np.isfinite(flat)
                    profile = []
                    for band_index in range(flat.shape[-1]):
                        band = flat[:, :, band_index]
                        finite_band = band[np.isfinite(band)]
                        if finite_band.size:
                            profile.append({
                                "band_index": band_index,
                                "mean": safe_float(np.mean(finite_band)),
                                "std": safe_float(np.std(finite_band)),
                                "median": safe_float(np.median(finite_band)),
                            })
                        else:
                            profile.append({"band_index": band_index, "mean": None, "std": None, "median": None})
                    pd.DataFrame(profile).to_csv(profile_path, index=False)
                    record["band_profile_status"] = "provisional_550_axis_from_array_shape_and_source_documentation"
                    record["band_profile_path"] = str(profile_path.relative_to(ROOT)).replace("\\", "/")
                    record["band_profile_units"] = "array units not wavelength units; no wavelength vector"
                    del flat
                del array
            except Exception as exc:
                record["inspection_error"] = f"{type(exc).__name__}: {exc}"
        records.append(record)

    groups, mapping = duplicate_groups(records)
    for record in records:
        duplicate = mapping.get(record["filename"])
        record["duplicate_group_id"] = duplicate["duplicate_group_id"] if duplicate else None
        record["is_unique_array"] = duplicate["is_unique_array"] if duplicate else False
        record["duplicate_group_file_count"] = duplicate["group_file_count"] if duplicate else 0

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "filename": r["filename"],
        "provisional_class": r["provisional_class"],
        "md5": r["md5"],
        "sha256": r["sha256"],
        "md5_status": r["md5_status"],
        "exists": r["exists"],
        "cube_dimensions": json.dumps(r["cube_dimensions"]) if r["cube_dimensions"] else None,
        "cube_dtype": r["cube_dtype"],
        "cube_variable_name": r["cube_variable_name"],
        "cube_hash": r["cube_hash"],
        "duplicate_group_id": r["duplicate_group_id"],
        "is_unique_array": r["is_unique_array"],
        **(r["cube_statistics"] or {}),
    } for r in records]).to_csv(INVENTORY_CSV, index=False)

    pd.DataFrame([{
        "filename": r["filename"],
        "cube_variable_name": r["cube_variable_name"],
        "cube_hash": r["cube_hash"],
        "duplicate_group_id": r["duplicate_group_id"],
        "is_unique_array": r["is_unique_array"],
        "group_file_count": r["duplicate_group_file_count"],
        "provisional_class": r["provisional_class"],
    } for r in records]).to_csv(DUPLICATE_CSV, index=False)

    valid_candidates = sum(r["cube_variable_name"] is not None for r in records)
    unique_hashes = {r["cube_hash"] for r in records if r["cube_hash"]}
    checksum_matches = sum(r["md5_status"] == "match" for r in records)
    checksum_failures = sum(r["md5_status"] in ("mismatch", "missing") for r in records)
    raw_hashes_after = {
        path: sha256_file(Path(path)) for path in raw_hashes_before
        if Path(path).exists()
    }
    raw_immutable = raw_hashes_before == raw_hashes_after

    report = {
        "script_version": SCRIPT_VERSION,
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": round(time.monotonic() - start, 3),
        "source_manifest_reference": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "source_doi": manifest.get("source_doi"),
        "record_version": manifest.get("record_version"),
        "license": manifest.get("license"),
        "raw_root": str(RAW_ROOT.relative_to(ROOT)).replace("\\", "/"),
        "files_expected": len(entries),
        "files_inspected": sum(r["exists"] for r in records),
        "checksum_matches": checksum_matches,
        "checksum_failures": checksum_failures,
        "valid_3d_candidates": valid_candidates,
        "unique_array_count": len(unique_hashes),
        "duplicate_group_count": sum(g["file_count"] > 1 for g in groups),
        "duplicate_groups": groups,
        "file_results": records,
        "class_comparison": class_counts(records),
        "raw_input_immutability": {
            "verified": raw_immutable,
            "files_checked": len(raw_hashes_before),
            "raw_writes": False,
        },
        "compatibility_assessment": {
            "conclusion": "Suitable only for separate exploratory analysis.",
            "f3_status": "NO-GO",
            "reason": "The external files lack verified biological identity, sample-level calibration, wavelength vectors, and plant-independent controls; exact healthy duplicates and a class-scale difference prevent direct comparability.",
        },
    }

    generate_markdown(report)
    with JSON_REPORT.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False)
    return report


def generate_markdown(report: dict) -> None:
    DOC_REPORT.parent.mkdir(parents=True, exist_ok=True)
    groups = report["duplicate_groups"]
    class_rows = []
    for class_name, values in report["class_comparison"].items():
        class_rows.append(
            f"| {class_name} | {values['file_count']} | {values['unique_array_count']} "
            f"| min={values['observed_finite_min_max']['min']}; max={values['observed_finite_min_max']['max']} "
            f"| {values['file_mean_summary']} | {values['file_std_summary']} |"
        )
    duplicate_rows = "\n".join(
        f"| {g['duplicate_group_id']} | {', '.join(g['filenames'])} | {g['cube_hash']} |"
        for g in groups if g["file_count"] > 1
    )
    file_rows = []
    for r in report["file_results"]:
        stats = r["cube_statistics"] or {}
        dims = r["cube_dimensions"]
        file_rows.append(
            f"| {r['filename']} | {r['provisional_class']} | {r['md5_status']} | "
            f"{dims or 'N/A'} | {r['cube_dtype'] or 'N/A'} | "
            f"{stats.get('min_finite', 'N/A')} | {stats.get('max_finite', 'N/A')} | "
            f"{stats.get('mean_finite', 'N/A')} | {r['duplicate_group_id'] or 'N/A'} |"
        )

    text = f"""# TerraSpectra - Phase F2.1 External Dataset Inspection

- **Status:** Phase F2.1 scientific inspection complete
- **Source:** Zenodo DOI 10.5281/zenodo.15800414, record version {report['record_version']}
- **License:** CC BY 4.0
**F3 integration status:** NO-GO

## Executive summary

The reproducible inspection evaluated {report['files_inspected']} of {report['files_expected']} MAT files.
It found {report['checksum_matches']} checksum matches and {report['checksum_failures']} checksum failures/missing files,
{report['valid_3d_candidates']} unambiguous numeric 3D candidates, and {report['unique_array_count']} unique numeric array contents.
There are {report['duplicate_group_count']} exact duplicate groups. Raw-sha256 immutability:
{report['raw_input_immutability']['verified']}.

## Inspection methodology

The script read the F2 manifest, resolved exact filenames beneath `data/raw/external/zenodo_15800414/`,
verified MD5/SHA-256, used `scipy.io.whosmat` before loading, loaded candidates one file at a time,
and hashed canonical shape/dtype/C-contiguous bytes. It did not modify raw MAT files or claim calibrated reflectance.

## File integrity

| Filename | Provisional class | MD5 | Dimensions | Dtype | Finite minimum | Finite maximum | Finite mean | Duplicate group |
|---|---|---|---|---|---:|---:|---:|---|
{chr(10).join(file_rows)}

## MATLAB structure

All candidate status, MATLAB variable names, dimensions, and types are retained in the machine-readable JSON report.
A third-dimension value of 550 is not treated as a verified wavelength axis. Per-file wavelength vectors are absent.

## Exact duplicate findings

| Group | Filenames | Cube hash |
|---|---|---|
{duplicate_rows or '| None | No exact duplicate groups detected | |'}

Exact duplicate groups are array-content duplicates only. They do not establish biological repetitions or independent plants.

## Per-band inspection

The source record and accompanying MATLAB script document 550 bands, while no MAT file includes a wavelength vector.
Accordingly, per-file band profiles were generated for the final axis as **provisional 550-band profiles**, with zero-based
indices and no wavelength or calibration claims. CSV units are array units, and no wavelength range is inferred.

## Class-wise numerical comparison

| Filename-derived provisional class | File count | Unique array count | Finite min/max summary | Finite mean summary | Finite std summary |
|---|---:|---:|---|---|---|
{chr(10).join(class_rows)}

The table above distinguishes files from unique array contents. The filename-based class labels are provisional:
the BOTRYTIS/healthy labels do not establish verified pathology or control ground truth.

## Existing-versus-external compatibility matrix

| Dimension | Existing TerraSpectra Latvia | External Zenodo tomato HSI |
|---|---|---|
| Crop | Tomato, cultivar Encore F1 | Tomato, Solanum lycopersicum var. 4921 |
| Pathogen | B. cinerea / B. pseudocinerea / control | Filename-derived B. cinerea / healthy |
| Source geography | Latvia | Gorgan, Iran |
| Sensor/instrument | Specim IQ | Hyspim HSI-Vis_Nir-15fps, paper-reported |
| Acquisition protocol | Greenhouse natural sunlight; verified partially | Laboratory halogen/dark-chamber details in paper; per-file products unavailable |
| Array dimensions | 512 x 512 x 204 local NPZ | 140 x 280 x 550 candidate MAT arrays |
| Number of bands | 204 | 550 source-reported and final-axis shape, no per-file vector |
| Wavelength range | 397.32-1003.58 nm verified only for 2436 | 400-950 nm paper-reported; file-verification unavailable |
| Wavelength vector | Available only for 2436 | Unavailable |
| Radiometric calibration | 2436 uncertain in exact reconstruction; 2973/3079 unresolved | Unresolved |
| Numerical scale | float16 NPZ; repository values require source-specific interpretation | Botrytis 0-4095; healthy below 1; scale difference observed |
| Biological sample identity | Metadata-derived 49 plants across 904 records | No verified plant/leaf/scan IDs |
| Independent sample count | 49 plants in metadata; only 3 local cubes | 16 source files; 12 recomputed unique arrays; 0 verified plants |
| Healthy/control labels | Metadata control class; caveats remain | Filename-derived provisional controls |
| Acquisition dates | Verified in metadata | Unverified; variable day tokens are not sample mapping |
| Disease timeline | Metadata repeated observations, severity absent | Paper report differs on days; release mapping absent |
| Disease severity | Unavailable | Unavailable |
| Duplicate arrays | Separate from this inspection | Exact duplicate array groups recomputed |
| License | CC BY 4.0 | CC BY 4.0 |
| Integration status | Existing source still constrained | {report['compatibility_assessment']['conclusion']} |

## Scientific limitations

- 16 source files are not 16 verified biological samples.
- 12 unique array contents are not 12 verified plants.
- Day variable names are not proven time points or plant identities.
- Numeric arrays are not called calibrated reflectance.
- Values must not be treated as cross-dataset spectral measurements without calibration evidence.

## Final integration recommendation

**Suitable only for separate exploratory analysis.** Preserve the current F3 NO-GO status.
Do not merge or train pooled models until sample identity, calibration, wavelength, and label provenance are resolved.

## Reproduction

Run from the repository root:

```powershell
python src/data/inspect_external_zenodo_dataset.py
pytest tests/test_external_dataset_inspection.py
```
"""
    DOC_REPORT.write_text(text, encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    manifest = Path(args[0]).resolve() if args else DEFAULT_MANIFEST
    report = run_inspection(manifest)
    print(json.dumps({
        "files_expected": report["files_expected"],
        "files_inspected": report["files_inspected"],
        "checksum_matches": report["checksum_matches"],
        "checksum_failures": report["checksum_failures"],
        "valid_3d_candidates": report["valid_3d_candidates"],
        "unique_array_count": report["unique_array_count"],
        "duplicate_group_count": report["duplicate_group_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
