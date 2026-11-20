"""Memory-conscious, per-cube PCA for masked tomato hyperspectral data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import threading
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import IncrementalPCA

try:
    import psutil
except ImportError:
    psutil = None


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "tomato_botrytis"
PROCESSED_DIR = ROOT / "data" / "processed"
PCA_DIR = PROCESSED_DIR / "pca"
FIGURE_DIR = ROOT / "outputs" / "figures"
REPORT_PATH = ROOT / "docs" / "real_data_pca_report.md"
N_BANDS = 204
N_COMPONENTS = 3
DEFAULT_RANDOM_SEED = 42
DEFAULT_MAX_SAMPLES = 20_000
DEFAULT_BATCH_SIZE = 2_048
SPATIAL_GRID_SIZE = 32

IMAGE_IDS = ("2436", "2973", "3079")
REGION_DESCRIPTIONS = {
    "visible_lesion": "Visually annotated lesion; not laboratory-confirmed.",
    "adjacent_unaffected": (
        "Adjacent visually unaffected stem; not confirmed healthy."
    ),
    "comparison_stem": "Comparison stem; not confirmed healthy.",
}


class InsufficientValidPixelsError(ValueError):
    """Raised when a cube or region cannot support a three-component PCA."""


class InvalidCubeInputError(ValueError):
    """Raised when an existing cube, mask, or axis fails validation."""


def spectral_axis(image_id: str, wavelengths_nm: np.ndarray | None) -> dict[str, Any]:
    """Return the permitted spectral axis without borrowing calibration."""
    if image_id == "2436":
        if wavelengths_nm is None:
            raise InvalidCubeInputError(
                "Image 2436 requires its verified wavelength vector."
            )
        values = np.asarray(wavelengths_nm, dtype=np.float64)
        if (
            values.shape != (N_BANDS,)
            or not np.isfinite(values).all()
            or not np.all(np.diff(values) > 0)
        ):
            raise InvalidCubeInputError("Image 2436 wavelength vector is invalid.")
        if not (math.isclose(values[0], 397.32, abs_tol=0.01)
                and math.isclose(values[-1], 1003.58, abs_tol=0.01)):
            raise InvalidCubeInputError(
                "Image 2436 wavelength range is not verified."
            )
        return {
            "axis_type": "wavelength_nm",
            "axis_label": "Wavelength (nm)",
            "values": values.tolist(),
            "calibration_status": "Verified for image 2436 only.",
        }

    if wavelengths_nm is not None:
        raise InvalidCubeInputError(
            f"Do not assign a wavelength vector to image {image_id}."
        )
    return {
        "axis_type": "zero_based_band_index",
        "axis_label": "Zero-based band index",
        "values": list(range(N_BANDS)),
        "calibration_status": (
            f"No verified wavelength calibration for image {image_id}."
        ),
    }


def _validate_masks(
    cube: np.ndarray,
    region_masks: dict[str, np.ndarray],
    quality_mask: np.ndarray | None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    if cube.ndim != 3 or cube.shape[2] != N_BANDS:
        raise InvalidCubeInputError(
            f"Expected an H x W x {N_BANDS} cube; received {cube.shape}."
        )
    spatial_shape = cube.shape[:2]
    if not region_masks:
        raise InvalidCubeInputError("At least one existing ROI mask is required.")

    checked_regions: dict[str, np.ndarray] = {}
    occupied = np.zeros(spatial_shape, dtype=bool)
    for name, mask in region_masks.items():
        region = np.asarray(mask, dtype=bool)
        if region.shape != spatial_shape:
            raise InvalidCubeInputError(
                f"ROI mask {name!r} shape {region.shape} does not match "
                f"cube spatial shape {spatial_shape}."
            )
        if np.any(occupied & region):
            raise InvalidCubeInputError(
                "ROI masks overlap; region-balanced fitting is ambiguous."
            )
        checked_regions[name] = region
        occupied |= region

    if quality_mask is None:
        invalid_measurements = np.zeros(cube.shape, dtype=bool)
    else:
        invalid_measurements = np.asarray(quality_mask, dtype=bool)
        if invalid_measurements.shape == spatial_shape:
            invalid_measurements = np.broadcast_to(
                invalid_measurements[:, :, None], cube.shape
            )
        elif invalid_measurements.shape != cube.shape:
            raise InvalidCubeInputError(
                f"Quality mask shape {invalid_measurements.shape} does not "
                f"match cube shape {cube.shape}."
            )

    finite_spectra = np.isfinite(cube).all(axis=2)
    quality_valid = ~invalid_measurements.any(axis=2)
    valid_regions = {
        name: mask & finite_spectra & quality_valid
        for name, mask in checked_regions.items()
    }
    return valid_regions, np.logical_or.reduce(list(valid_regions.values()))


def _sample_spatially(
    valid_mask: np.ndarray,
    sample_count: int,
    rng: np.random.Generator,
    grid_size: int = SPATIAL_GRID_SIZE,
) -> np.ndarray:
    """Choose valid flat pixel indices evenly across occupied spatial tiles."""
    candidates = np.flatnonzero(valid_mask)
    if sample_count < 0 or sample_count > candidates.size:
        raise ValueError("Requested sample count is outside the valid pixel count.")
    if sample_count == 0:
        return np.empty(0, dtype=np.int64)
    if sample_count == candidates.size:
        selected = candidates.copy()
        rng.shuffle(selected)
        return selected

    width = valid_mask.shape[1]
    rows, cols = np.divmod(candidates, width)
    n_tile_cols = math.ceil(width / grid_size)
    tile_ids = (rows // grid_size) * n_tile_cols + cols // grid_size
    order = np.argsort(tile_ids, kind="stable")
    sorted_candidates = candidates[order]
    sorted_tiles = tile_ids[order]
    boundaries = np.flatnonzero(np.diff(sorted_tiles)) + 1
    tile_candidates = np.split(sorted_candidates, boundaries)
    n_tiles = len(tile_candidates)
    base, extra = divmod(sample_count, n_tiles)
    selected_parts: list[np.ndarray] = []
    remaining_parts: list[np.ndarray] = []

    for tile_index, tile_values in enumerate(tile_candidates):
        quota = base + (1 if tile_index < extra else 0)
        take = min(quota, tile_values.size)
        if take:
            tile_order = rng.permutation(tile_values.size)
            selected_parts.append(tile_values[tile_order[:take]])
            if take < tile_values.size:
                remaining_parts.append(tile_values[tile_order[take:]])
        else:
            remaining_parts.append(tile_values)

    selected = (
        np.concatenate(selected_parts)
        if selected_parts else np.empty(0, dtype=np.int64)
    )
    shortfall = sample_count - selected.size
    if shortfall:
        remaining = np.concatenate(remaining_parts)
        fill = rng.choice(remaining, size=shortfall, replace=False)
        selected = np.concatenate((selected, fill))
    rng.shuffle(selected)
    return selected


def _batch_slices(length: int, batch_size: int) -> list[slice]:
    if batch_size < N_COMPONENTS:
        raise ValueError(
            f"batch_size must be at least {N_COMPONENTS} for IncrementalPCA."
        )
    batches: list[slice] = []
    start = 0
    while start < length:
        stop = min(start + batch_size, length)
        if length - stop in (1, 2):
            stop = length
        batches.append(slice(start, stop))
        start = stop
    return batches


def _fit_sample_indices(
    valid_regions: dict[str, np.ndarray],
    max_samples: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, int]]:
    if max_samples < N_COMPONENTS:
        raise InsufficientValidPixelsError(
            f"At least {N_COMPONENTS} fitting samples are required."
        )
    nonempty = {
        name: mask for name, mask in valid_regions.items() if mask.any()
    }
    if not nonempty:
        raise InsufficientValidPixelsError("No valid pixels remain inside the ROI.")

    per_region_limit = max_samples // len(nonempty)
    region_counts = {name: int(mask.sum()) for name, mask in nonempty.items()}
    if len(nonempty) == 1:
        sample_count = min(max_samples, next(iter(region_counts.values())))
        target_per_region = sample_count
    else:
        target_per_region = min(
            per_region_limit,
            min(region_counts.values()),
        )
        sample_count = target_per_region * len(nonempty)
    if target_per_region < N_COMPONENTS:
        raise InsufficientValidPixelsError(
            "Each annotated region needs at least three valid pixels for "
            "balanced PCA fitting."
        )

    sampled: list[np.ndarray] = []
    fit_counts: dict[str, int] = {}
    for name, mask in nonempty.items():
        indices = _sample_spatially(mask, target_per_region, rng)
        sampled.append(indices)
        fit_counts[name] = int(indices.size)
    combined = np.concatenate(sampled)
    rng.shuffle(combined)
    return combined, fit_counts


def analyze_cube_array(
    cube: np.ndarray,
    image_id: str,
    region_masks: dict[str, np.ndarray],
    quality_mask: np.ndarray | None = None,
    wavelengths_nm: np.ndarray | None = None,
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_samples: int = DEFAULT_MAX_SAMPLES,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Fit one independent cube PCA and transform valid ROI pixels in batches."""
    valid_regions, valid_mask = _validate_masks(
        cube, region_masks, quality_mask
    )
    axis = spectral_axis(image_id, wavelengths_nm)
    rng = np.random.default_rng(random_seed)
    sample_indices, fit_counts = _fit_sample_indices(
        valid_regions, max_samples, rng
    )
    if sample_indices.size < N_COMPONENTS:
        raise InsufficientValidPixelsError(
            f"Only {sample_indices.size} fitting samples are available."
        )

    flat_cube = cube.reshape(-1, N_BANDS)
    pca = IncrementalPCA(n_components=N_COMPONENTS, batch_size=batch_size)
    fit_batches = _batch_slices(sample_indices.size, batch_size)
    for batch in fit_batches:
        values = flat_cube[sample_indices[batch]].astype(np.float32)
        pca.partial_fit(values)

    valid_indices = np.flatnonzero(valid_mask)
    scores = np.full(
        (cube.shape[0] * cube.shape[1], N_COMPONENTS),
        np.nan,
        dtype=np.float32,
    )
    transform_batches = _batch_slices(valid_indices.size, batch_size)
    for batch in transform_batches:
        indices = valid_indices[batch]
        values = flat_cube[indices].astype(np.float32)
        scores[indices] = pca.transform(values).astype(np.float32)

    score_map = scores.reshape(*cube.shape[:2], N_COMPONENTS)
    ratio = pca.explained_variance_ratio_.astype(np.float64)
    sample_values = flat_cube[sample_indices]
    above_one_fit_measurements = int(np.count_nonzero(sample_values > 1.0))
    metadata = {
        "image_id": image_id,
        "spectral_axis": axis,
        "spectral_features_per_pixel": int(cube.shape[2]),
        "valid_pixel_count": int(valid_indices.size),
        "region_valid_pixel_counts": {
            name: int(mask.sum()) for name, mask in valid_regions.items()
        },
        "fit_sample_count": int(sample_indices.size),
        "fit_sample_counts_by_region": fit_counts,
        "sampling_strategy": (
            "Deterministic, without-replacement spatial grid-cell sampling; "
            "equal quotas across non-empty annotated regions."
        ),
        "random_seed": int(random_seed),
        "max_fit_samples_per_cube": int(max_samples),
        "batch_size": int(batch_size),
        "fit_batch_count": len(fit_batches),
        "transform_batch_count": len(transform_batches),
        "incremental_pca": True,
        "explained_variance_ratio": ratio.tolist(),
        "cumulative_explained_variance_ratio": float(ratio.sum()),
        "fit_sample_measurements_above_1_count": above_one_fit_measurements,
        "threshold_at_1_applied": False,
        "preexisting_quality_mask_applied": quality_mask is not None,
        "measurement_interpretation": (
            "NPZ measurements are analyzed as provided; they are not described "
            "as independently calibrated laboratory reflectance."
        ),
    }
    return {
        "score_map": score_map,
        "valid_mask": valid_mask,
        "sample_flat_indices": sample_indices,
        "components": pca.components_.astype(np.float32),
        "explained_variance": pca.explained_variance_.astype(np.float64),
        "explained_variance_ratio": ratio,
        "mean": pca.mean_.astype(np.float64),
        "metadata": metadata,
        "valid_regions": valid_regions,
    }


def _load_metadata_records() -> dict[str, dict[str, str]]:
    path = RAW_DIR / "metadata.tsv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset metadata file is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        records = {
            row["image_id"].strip(): row
            for row in csv.DictReader(stream, delimiter="\t")
        }
    return records


def _load_cube_inputs(image_id: str) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray | None, np.ndarray | None]:
    cube_path = RAW_DIR / f"{image_id}.npz"
    if not cube_path.is_file():
        raise FileNotFoundError(f"Raw cube is missing: {cube_path}")

    if image_id == "2436":
        roi_path = PROCESSED_DIR / "cubes" / "2436_leaf_roi.npz"
        quality_path = PROCESSED_DIR / "quality_masks" / "2436_quality_mask.npz"
        if not roi_path.is_file():
            raise FileNotFoundError(f"Existing leaf ROI mask is missing: {roi_path}")
        if not quality_path.is_file():
            raise FileNotFoundError(f"Existing quality mask is missing: {quality_path}")
        with np.load(roi_path, allow_pickle=False) as roi_file:
            roi = roi_file["leaf_mask"].astype(bool)
            wavelengths = roi_file["wavelengths_nm"].astype(np.float64)
        with np.load(quality_path, allow_pickle=False) as quality_file:
            quality = quality_file["quality_mask"].astype(bool)
        with np.load(cube_path, allow_pickle=False) as cube_file:
            cube = cube_file["arr_0"]
        return cube, {"leaf_roi": roi}, quality, wavelengths

    if image_id == "3079":
        annotation_path = (
            PROCESSED_DIR / "segmentation" / "3079_lesion_level_annotations.npz"
        )
        if not annotation_path.is_file():
            raise FileNotFoundError(
                f"Existing 3079 region annotations are missing: {annotation_path}"
            )
        with np.load(annotation_path, allow_pickle=False) as annotation:
            masks = {
                "visible_lesion": annotation["visible_lesion_mask"].astype(bool),
                "adjacent_unaffected": annotation[
                    "adjacent_non_lesioned_stem_mask"
                ].astype(bool),
                "comparison_stem": annotation["comparison_stem_mask"].astype(bool),
            }
        with np.load(cube_path, allow_pickle=False) as cube_file:
            cube = cube_file["arr_0"]
        return cube, masks, None, None

    raise ValueError(f"No supported existing ROI is configured for image {image_id}.")


def _metadata_for_cube(
    image_id: str, records: dict[str, dict[str, str]]
) -> dict[str, Any]:
    if image_id not in records:
        raise ValueError(f"No metadata row exists for image {image_id}.")
    row = records[image_id]
    plant_key = "_".join(
        (row["replicate"], row["pathogen"], f"S{row['sample']}")
    )
    organ_key = f"{plant_key}_{row['part']}"
    return {
        "pathogen": row["pathogen"],
        "replicate": row["replicate"],
        "sample": row["sample"],
        "part": row["part"],
        "biological_plant_id": plant_key,
        "plant_organ_id": organ_key,
    }


def _figure_paths(image_id: str) -> dict[str, Path]:
    prefix = f"real_pca_{image_id}"
    paths = {
        "explained_variance": FIGURE_DIR / f"{prefix}_explained_variance.png",
        "spatial_scores": FIGURE_DIR / f"{prefix}_spatial_scores.png",
        "component_loadings": FIGURE_DIR / f"{prefix}_component_loadings.png",
    }
    if image_id == "3079":
        paths["region_score_distributions"] = (
            FIGURE_DIR / f"{prefix}_region_score_distributions.png"
        )
    return paths


def _save_figures(
    image_id: str, result: dict[str, Any]
) -> dict[str, str]:
    paths = _figure_paths(image_id)
    metadata = result["metadata"]
    axis_values = metadata["spectral_axis"]["values"]
    axis_label = metadata["spectral_axis"]["axis_label"]
    ratios = result["explained_variance_ratio"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    components = np.arange(1, N_COMPONENTS + 1)
    ax.bar(components, ratios * 100, color="#4472C4", label="Individual")
    ax.plot(
        components,
        np.cumsum(ratios) * 100,
        color="#C0504D",
        marker="o",
        label="Cumulative",
    )
    ax.set_xticks(components, [f"PC{i}" for i in components])
    ax.set_ylabel("Explained variance (%)")
    ax.set_title(f"Image {image_id}: PCA explained variance")
    ax.grid(alpha=0.25, axis="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(paths["explained_variance"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    score_map = result["score_map"]
    fig, axes = plt.subplots(1, N_COMPONENTS, figsize=(15, 5))
    for index, ax in enumerate(axes):
        image = ax.imshow(
            np.ma.masked_invalid(score_map[:, :, index]),
            cmap="RdBu_r",
            interpolation="nearest",
        )
        ax.set_title(f"PC{index + 1} score")
        ax.set_axis_off()
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(
        f"Image {image_id}: independent PCA scores in annotated valid ROI"
    )
    fig.tight_layout()
    fig.savefig(paths["spatial_scores"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(N_COMPONENTS, 1, figsize=(11, 8), sharex=True)
    for index, ax in enumerate(axes):
        ax.plot(axis_values, result["components"][index], linewidth=1.1)
        ax.set_ylabel(f"PC{index + 1}\nloading")
        ax.grid(alpha=0.25)
    axes[-1].set_xlabel(axis_label)
    fig.suptitle(f"Image {image_id}: PCA component loadings")
    fig.tight_layout()
    fig.savefig(paths["component_loadings"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    if image_id == "3079":
        region_names = list(result["valid_regions"])
        fig, axes = plt.subplots(1, N_COMPONENTS, figsize=(15, 5))
        for index, ax in enumerate(axes):
            distributions = [
                result["score_map"][:, :, index][mask]
                for mask in result["valid_regions"].values()
            ]
            ax.boxplot(distributions, showfliers=False)
            ax.set_xticks(
                np.arange(1, len(region_names) + 1),
                [name.replace("_", "\n") for name in region_names],
                rotation=0,
            )
            ax.set_title(f"PC{index + 1}")
            ax.set_ylabel("PCA score")
            ax.grid(alpha=0.2, axis="y")
        fig.suptitle(
            "Image 3079: exploratory ROI score distributions "
            "(not disease discrimination)"
        )
        fig.tight_layout()
        fig.savefig(
            paths["region_score_distributions"],
            dpi=180,
            bbox_inches="tight",
        )
        plt.close(fig)

    return {name: str(path.relative_to(ROOT)) for name, path in paths.items()}


def _write_loadings_csv(path: Path, result: dict[str, Any]) -> None:
    axis = result["metadata"]["spectral_axis"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [axis["axis_label"]]
            + [f"PC{index}" for index in range(1, N_COMPONENTS + 1)]
        )
        for value, loadings in zip(axis["values"], result["components"].T):
            writer.writerow([value, *[float(item) for item in loadings]])


def _write_cube_outputs(
    image_id: str,
    result: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    PCA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    data_path = PCA_DIR / f"{image_id}_pca.npz"
    summary_path = PCA_DIR / f"{image_id}_summary.json"
    loadings_path = PCA_DIR / f"{image_id}_component_loadings.csv"
    np.savez_compressed(
        data_path,
        score_map=result["score_map"],
        valid_mask=result["valid_mask"],
        sample_flat_indices=result["sample_flat_indices"],
        components=result["components"],
        explained_variance=result["explained_variance"],
        explained_variance_ratio=result["explained_variance_ratio"],
        mean=result["mean"],
        spectral_axis_values=np.asarray(
            result["metadata"]["spectral_axis"]["values"]
        ),
    )
    _write_loadings_csv(loadings_path, result)
    result["metadata"].update(metadata)
    result["metadata"]["status"] = "analyzed"
    result["metadata"]["figures"] = _save_figures(
        image_id, result
    )
    result["metadata"]["output_files"] = {
        "pca_arrays": str(data_path.relative_to(ROOT)),
        "component_loadings_csv": str(loadings_path.relative_to(ROOT)),
        **result["metadata"]["figures"],
    }
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(result["metadata"], stream, indent=2, allow_nan=False)
    return result["metadata"]


def _markdown_report(summary: dict[str, Any]) -> str:
    analyses = summary["analyses"]
    successful = [item for item in analyses if item["status"] == "analyzed"]
    skipped = [item for item in analyses if item["status"] == "skipped"]
    rows = []
    for item in analyses:
        if item["status"] == "analyzed":
            ratios = item["explained_variance_ratio"]
            rows.append(
                f"| {item['image_id']} | analyzed | "
                f"{item['valid_pixel_count']:,} | {item['fit_sample_count']:,} | "
                f"{ratios[0] * 100:.2f}% / {ratios[1] * 100:.2f}% / "
                f"{ratios[2] * 100:.2f}% | "
                f"{item['spectral_axis']['axis_label']} |"
            )
        else:
            rows.append(
                f"| {item['image_id']} | skipped: {item['reason']} | — | — | — | — |"
            )
    figure_links = []
    for item in successful:
        for name, path in item["figures"].items():
            figure_links.append(f"- Image {item['image_id']} {name}: `{path}`")
    skip_text = (
        "\n".join(f"- Image {item['image_id']}: {item['reason']}" for item in skipped)
        or "- None."
    )
    return f"""# Real-Cube PCA and ML Readiness

**Status:** Reproducible exploratory PCA completed; no classifier trained.

## Real-data PCA

PCA was fit independently for each eligible cube using 204 spectral measurements
per pixel and `IncrementalPCA`. Only existing annotated/segmented ROIs were used;
pixels outside each ROI, pixels with any non-finite spectral measurement, and
pixels flagged by an existing quality mask remain missing in spatial score maps.
No 1.0 threshold or clipping rule was added; an existing quality mask, where
available, was applied as stored. The NPZ measurements are not described as
independently calibrated laboratory reflectance. Cubes were not pooled, aligned, or compared as if their spectral
axes were interchangeable.

| Image | Status | Valid ROI pixels | PCA fit samples | PC1 / PC2 / PC3 variance | Spectral axis |
|---|---|---:|---:|---|---|
{chr(10).join(rows)}

### Sampling and reproducibility

- Method: deterministic sampling without replacement, stratified across a
  spatial grid; for image 3079, equal fit quotas were used for the visible
  lesion, adjacent visually unaffected stem, and comparison stem.
- Random seed: `{summary['random_seed']}`.
- Maximum fit sample budget per cube: `{summary['max_fit_samples_per_cube']:,}`;
  incremental fit and score transformation batch size:
  `{summary['batch_size']:,}`.
- PCA was fit separately per cube. The wavelength axis is used only for image
  2436 (397.32–1003.58 nm); images 2973 and 3079 use zero-based band indices.
- Runtime for this run: {summary['runtime_seconds']:.2f} seconds.
- Peak process working set observed during this run:
  {summary['peak_rss_mib'] if summary['peak_rss_mib'] is not None else 'unavailable'}
  MiB.

### Skipped cubes

{skip_text}

### Figures

{chr(10).join(figure_links)}

## Interpretation limits

PCA is unsupervised dimensionality reduction, not classification. Components
are not disease indicators. Any separation in the image 3079 ROI score
distributions is exploratory only; the lesion is not laboratory-confirmed, and
the adjacent and comparison regions are not confirmed healthy. The PCA cannot
establish pathogen discrimination, disease classification, forecasting, or
predictive accuracy.

## Dataset and ML readiness

The local metadata contains **49 biological plant identities** and **193
plant-organ objects**. The project’s biological plant key is
`replicate + pathogen + sample`; the organ key adds `part`. The longitudinal
metadata script groups by all four fields, which identifies organ-level
objects, not independent biological plants. The existing identifiers were not
changed. For leakage prevention, future supervised evaluation must group by
biological plant identity (and report replicate-held-out results separately).

The three local cubes (2436, 2973, 3079) are each associated with
*B. pseudocinerea* and map to three distinct plant identities. They do not
provide validated healthy-versus-diseased or pathogen-discrimination labels.
Reliable supervised labels are not available locally: metadata pathogen
assignments are not pixel-level lesion ground truth, and the three cubes
contain only one pathogen class. A valid baseline classification experiment
cannot be trained or evaluated from these cubes.

GroupKFold is structurally possible on the 49 metadata plant groups, and
Leave-One-Replicate-Out can be specified across five replicates, but neither
creates a defensible experiment from the three local, single-class cubes.
Replicate-held-out folds also require checks for class coverage and
acquisition/season confounding. Before supervised baselines, obtain the
remaining class-diverse cubes (including controls and *B. cinerea*), traceable
and consistent spectral calibration/band mapping, and independent,
laboratory-confirmed plant/lesion labels. Evaluation must be grouped by
biological plant and must not treat pixels or multiple organs from one plant
as independent biological replicates.

## Geospatial scope

The local greenhouse cubes are not georeferenced field imagery. Rasterio/
GeoTIFF geospatial processing and geographic-coordinate claims are not part of
this completed work; no coordinates are fabricated.
"""


class _PeakRssMonitor:
    def __init__(self) -> None:
        self.peak_bytes: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "_PeakRssMonitor":
        if psutil is not None:
            process = psutil.Process()
            self.peak_bytes = process.memory_info().rss

            def sample() -> None:
                while not self._stop.wait(0.05):
                    rss = process.memory_info().rss
                    self.peak_bytes = max(self.peak_bytes or 0, rss)

            self._thread = threading.Thread(target=sample, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()


def _expected_output_paths() -> list[Path]:
    paths = [REPORT_PATH, PCA_DIR / "analysis_summary.json"]
    for image_id in ("2436", "3079"):
        paths.extend(
            (
                PCA_DIR / f"{image_id}_pca.npz",
                PCA_DIR / f"{image_id}_summary.json",
                PCA_DIR / f"{image_id}_component_loadings.csv",
                *_figure_paths(image_id).values(),
            )
        )
    return paths


def _skip_entry(image_id: str, reason: str) -> dict[str, Any]:
    return {"image_id": image_id, "status": "skipped", "reason": reason}


def run_analysis(
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_samples: int = DEFAULT_MAX_SAMPLES,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    existing = [path for path in _expected_output_paths() if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing PCA outputs: "
            + ", ".join(str(path) for path in existing)
        )
    if batch_size < N_COMPONENTS:
        raise ValueError(f"batch_size must be at least {N_COMPONENTS}.")

    metadata_records = _load_metadata_records()
    analyses: list[dict[str, Any]] = []
    start_time = time.perf_counter()
    with _PeakRssMonitor() as memory_monitor:
        for image_id in IMAGE_IDS:
            if image_id == "2973":
                roi_path = PROCESSED_DIR / "segmentation" / "2973_roi_annotations.npz"
                if not roi_path.is_file():
                    analyses.append(
                        _skip_entry(
                            image_id,
                            "no appropriate existing ROI mask; no segmentation "
                            "was invented, so this cube was not analyzed.",
                        )
                    )
                    continue
            try:
                cube, region_masks, quality_mask, wavelengths = _load_cube_inputs(
                    image_id
                )
            except FileNotFoundError as error:
                analyses.append(_skip_entry(image_id, str(error)))
                continue
            except (KeyError, OSError, ValueError) as error:
                analyses.append(
                    _skip_entry(image_id, f"invalid input or mask: {error}")
                )
                continue

            try:
                result = analyze_cube_array(
                    cube=cube,
                    image_id=image_id,
                    region_masks=region_masks,
                    quality_mask=quality_mask,
                    wavelengths_nm=wavelengths,
                    random_seed=random_seed,
                    max_samples=max_samples,
                    batch_size=batch_size,
                )
            except InvalidCubeInputError as error:
                analyses.append(
                    _skip_entry(image_id, f"invalid cube/mask/axis: {error}")
                )
                del cube, region_masks, quality_mask, wavelengths
                continue
            except InsufficientValidPixelsError as error:
                analyses.append(
                    _skip_entry(image_id, f"insufficient valid samples: {error}")
                )
                del cube, region_masks, quality_mask, wavelengths
                continue

            cube_metadata = _metadata_for_cube(image_id, metadata_records)
            if image_id == "3079":
                result["metadata"]["region_interpretations"] = REGION_DESCRIPTIONS
            entry = _write_cube_outputs(image_id, result, cube_metadata)
            entry["status"] = "analyzed"
            analyses.append(entry)
            del cube, result, region_masks, quality_mask, wavelengths

    runtime = time.perf_counter() - start_time
    peak_mib = (
        round(memory_monitor.peak_bytes / (1024 * 1024), 2)
        if memory_monitor.peak_bytes is not None else None
    )
    summary = {
        "analysis": "independent_real_hyperspectral_cube_pca",
        "random_seed": int(random_seed),
        "max_fit_samples_per_cube": int(max_samples),
        "batch_size": int(batch_size),
        "sampling_strategy": (
            "Deterministic spatial grid-cell sampling without replacement; "
            "equal per-region quotas for image 3079."
        ),
        "runtime_seconds": round(runtime, 3),
        "peak_rss_mib": peak_mib,
        "complete_cubes_loaded_simultaneously": 1,
        "analyses": analyses,
        "scientific_scope": (
            "Unsupervised exploratory PCA only; no disease classification, "
            "forecasting, prediction, reflectance calibration, or cross-cube "
            "spectral alignment is claimed."
        ),
    }
    PCA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    (PCA_DIR / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run independent, masked PCA on eligible local tomato cubes."
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED)
    parser.add_argument(
        "--max-samples", type=int, default=DEFAULT_MAX_SAMPLES
    )
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()
    summary = run_analysis(args.seed, args.max_samples, args.batch_size)
    for item in summary["analyses"]:
        print(f"{item['image_id']}: {item['status']}")
        if item["status"] == "skipped":
            print(f"  reason: {item['reason']}")
        else:
            ratios = item["explained_variance_ratio"]
            print(
                "  explained variance: "
                + ", ".join(f"PC{i + 1}={value:.6f}" for i, value in enumerate(ratios))
            )
            print(
                f"  valid pixels={item['valid_pixel_count']}, "
                f"fit samples={item['fit_sample_count']}"
            )
    print(f"Runtime: {summary['runtime_seconds']:.2f} seconds")
    print(f"Peak RSS: {summary['peak_rss_mib']} MiB")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
