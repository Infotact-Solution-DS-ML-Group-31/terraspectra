"""Memory-conscious, per-cube unsupervised K-Means spectral clustering."""

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
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import StandardScaler

try:
    import psutil
except ImportError:
    psutil = None


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "tomato_botrytis"
PROCESSED_DIR = ROOT / "data" / "processed"
CLUSTERING_DIR = PROCESSED_DIR / "clustering"
REPORTS_DIR = PROCESSED_DIR / "reports"
FIGURE_DIR = ROOT / "outputs" / "figures"
REPORT_MD_PATH = ROOT / "docs" / "phase_f3_unsupervised_clustering.md"
REPORT_JSON_PATH = REPORTS_DIR / "phase_f3_unsupervised_clustering.json"

N_BANDS = 204
IMAGE_IDS = ("2436", "2973", "3079")
DEFAULT_K_VALUES = (2, 3, 4, 5)
DEFAULT_RANDOM_SEED = 42
STABILITY_SEEDS = (42, 101, 202)
DEFAULT_MAX_FIT_SAMPLES = 20_000
DEFAULT_SILHOUETTE_SAMPLES = 5_000
DEFAULT_BATCH_SIZE = 4_096
SPATIAL_GRID_SIZE = 32
SPATIAL_BLOCK_SIZE = 64

REGION_DESCRIPTIONS = {
    "visible_lesion": "Visually annotated lesion; not laboratory-confirmed.",
    "adjacent_unaffected": "Adjacent visually unaffected stem; not confirmed healthy.",
    "comparison_stem": "Comparison stem; not confirmed healthy.",
}


class InvalidClusteringInputError(ValueError):
    """Raised when cube, masks, or spectral axis fail validation."""


class InsufficientClusteringSamplesError(ValueError):
    """Raised when valid pixels are insufficient for clustering."""


class _PeakRssMonitor:
    """Poll process RSS in a background thread to record peak memory."""

    def __init__(self, interval_seconds: float = 0.05) -> None:
        self.interval_seconds = interval_seconds
        self.peak_bytes: int | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "_PeakRssMonitor":
        if psutil is None:
            return self
        proc = psutil.Process()
        self.peak_bytes = proc.memory_info().rss

        def _poll() -> None:
            while not self._stop_event.wait(self.interval_seconds):
                rss = proc.memory_info().rss
                if self.peak_bytes is None or rss > self.peak_bytes:
                    self.peak_bytes = rss

        self._thread = threading.Thread(target=_poll, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def build_spectral_axis(image_id: str, wavelengths_nm: np.ndarray | None) -> dict[str, Any]:
    """Return permitted spectral axis metadata without borrowing calibration."""
    if image_id == "2436":
        if wavelengths_nm is None:
            raise InvalidClusteringInputError("Image 2436 requires its verified wavelength vector.")
        values = np.asarray(wavelengths_nm, dtype=np.float64)
        if values.shape != (N_BANDS,) or not np.isfinite(values).all() or not np.all(np.diff(values) > 0):
            raise InvalidClusteringInputError("Image 2436 wavelength vector is invalid.")
        if not (math.isclose(values[0], 397.32, abs_tol=0.01) and math.isclose(values[-1], 1003.58, abs_tol=0.01)):
            raise InvalidClusteringInputError("Image 2436 wavelength range is not verified.")
        return {
            "axis_type": "wavelength_nm",
            "axis_label": "Wavelength (nm)",
            "values": values.tolist(),
            "calibration_status": "Verified for image 2436 only (Specim IQ ENVI headers).",
        }

    if wavelengths_nm is not None:
        raise InvalidClusteringInputError(f"Do not assign a wavelength vector to image {image_id}.")
    return {
        "axis_type": "zero_based_band_index",
        "axis_label": "Zero-based band index",
        "values": list(range(N_BANDS)),
        "calibration_status": f"No verified wavelength calibration for image {image_id}.",
    }


def validate_and_combine_masks(
    cube: np.ndarray,
    region_masks: dict[str, np.ndarray],
    quality_mask: np.ndarray | None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Validate shapes, exclude non-finite and quality-flagged pixels, and return valid masks."""
    if cube.ndim != 3 or cube.shape[2] != N_BANDS:
        raise InvalidClusteringInputError(f"Expected H x W x {N_BANDS} cube; received {cube.shape}.")
    spatial_shape = cube.shape[:2]
    if not region_masks:
        raise InvalidClusteringInputError("At least one ROI mask is required.")

    checked_regions: dict[str, np.ndarray] = {}
    occupied = np.zeros(spatial_shape, dtype=bool)
    for name, mask in region_masks.items():
        region = np.asarray(mask, dtype=bool)
        if region.shape != spatial_shape:
            raise InvalidClusteringInputError(
                f"ROI mask {name!r} shape {region.shape} does not match cube spatial shape {spatial_shape}."
            )
        if np.any(occupied & region):
            raise InvalidClusteringInputError("ROI masks overlap.")
        checked_regions[name] = region
        occupied |= region

    if quality_mask is None:
        invalid_measurements = np.zeros(cube.shape, dtype=bool)
    else:
        invalid_measurements = np.asarray(quality_mask, dtype=bool)
        if invalid_measurements.shape == spatial_shape:
            invalid_measurements = np.broadcast_to(invalid_measurements[:, :, None], cube.shape)
        elif invalid_measurements.shape != cube.shape:
            raise InvalidClusteringInputError(
                f"Quality mask shape {invalid_measurements.shape} does not match cube shape {cube.shape}."
            )

    finite_spectra = np.isfinite(cube).all(axis=2)
    quality_valid = ~invalid_measurements.any(axis=2)
    valid_regions = {name: mask & finite_spectra & quality_valid for name, mask in checked_regions.items()}
    valid_mask = np.logical_or.reduce(list(valid_regions.values()))
    return valid_regions, valid_mask


def sample_spatial_grid_indices(
    valid_mask: np.ndarray,
    sample_count: int,
    rng: np.random.Generator,
    grid_size: int = SPATIAL_GRID_SIZE,
) -> np.ndarray:
    """Deterministically sample flat pixel indices across occupied spatial grid tiles without using ROI labels."""
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
    tile_ids = (rows // grid_size) * n_tile_cols + (cols // grid_size)
    order = np.argsort(tile_ids, kind="stable")
    sorted_candidates = candidates[order]
    sorted_tiles = tile_ids[order]
    boundaries = np.flatnonzero(np.diff(sorted_tiles)) + 1
    tile_candidates = np.split(sorted_candidates, boundaries)

    n_tiles = len(tile_candidates)
    base, extra = divmod(sample_count, n_tiles)
    selected_parts: list[np.ndarray] = []
    remaining_parts: list[np.ndarray] = []

    for tile_idx, tile_vals in enumerate(tile_candidates):
        quota = base + (1 if tile_idx < extra else 0)
        take = min(quota, tile_vals.size)
        if take > 0:
            perm = rng.permutation(tile_vals.size)
            selected_parts.append(tile_vals[perm[:take]])
            if take < tile_vals.size:
                remaining_parts.append(tile_vals[perm[take:]])
        else:
            remaining_parts.append(tile_vals)

    selected = np.concatenate(selected_parts) if selected_parts else np.empty(0, dtype=np.int64)
    shortfall = sample_count - selected.size
    if shortfall > 0:
        remaining = np.concatenate(remaining_parts)
        fill = rng.choice(remaining, size=shortfall, replace=False)
        selected = np.concatenate((selected, fill))
    rng.shuffle(selected)
    return selected


def _extract_flat_spectra(cube: np.ndarray, flat_indices: np.ndarray) -> np.ndarray:
    """Extract (N, bands) float32 matrix for given flat spatial indices."""
    height, width, bands = cube.shape
    return cube.reshape(height * width, bands)[flat_indices].astype(np.float32, copy=False)


def _predict_in_batches(
    cube: np.ndarray,
    valid_indices: np.ndarray,
    scaler: StandardScaler,
    kmeans: KMeans,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    """Predict cluster labels for all valid pixels in memory-bounded batches."""
    labels = np.empty(valid_indices.size, dtype=np.int16)
    height, width, bands = cube.shape
    flat_cube = cube.reshape(height * width, bands)
    for start in range(0, valid_indices.size, batch_size):
        stop = min(start + batch_size, valid_indices.size)
        batch = flat_cube[valid_indices[start:stop]].astype(np.float32, copy=False)
        batch_scaled = scaler.transform(batch)
        labels[start:stop] = kmeans.predict(batch_scaled).astype(np.int16)
    return labels


def _compute_cluster_profiles(
    cube: np.ndarray,
    valid_indices: np.ndarray,
    labels: np.ndarray,
    k: int,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Compute exact per-cluster mean and std spectral profiles in original stored-value units."""
    height, width, bands = cube.shape
    flat_cube = cube.reshape(height * width, bands)
    counts = np.zeros(k, dtype=np.int64)
    sums = np.zeros((k, bands), dtype=np.float64)
    sum_sq = np.zeros((k, bands), dtype=np.float64)

    for start in range(0, valid_indices.size, batch_size):
        stop = min(start + batch_size, valid_indices.size)
        batch = flat_cube[valid_indices[start:stop]].astype(np.float64)
        batch_labels = labels[start:stop]
        for c in range(k):
            mask = batch_labels == c
            if np.any(mask):
                sub = batch[mask]
                counts[c] += sub.shape[0]
                sums[c] += sub.sum(axis=0)
                sum_sq[c] += np.square(sub).sum(axis=0)

    total_valid = int(valid_indices.size)
    means = np.zeros((k, bands), dtype=np.float64)
    stds = np.zeros((k, bands), dtype=np.float64)
    cluster_sizes: list[dict[str, Any]] = []

    for c in range(k):
        cnt = int(counts[c])
        if cnt > 0:
            means[c] = sums[c] / cnt
            var = np.maximum(0.0, (sum_sq[c] / cnt) - np.square(means[c]))
            stds[c] = np.sqrt(var)
        cluster_sizes.append({
            "cluster_id": c,
            "pixel_count": cnt,
            "percentage": round((cnt / total_valid) * 100.0, 4) if total_valid > 0 else 0.0,
            "mean_within_cluster_std": round(float(stds[c].mean()), 6) if cnt > 0 else 0.0,
        })

    return {
        "means": means,
        "stds": stds,
        "cluster_sizes": cluster_sizes,
    }


def _compute_posthoc_roi_comparison(
    valid_regions: dict[str, np.ndarray],
    cluster_map: np.ndarray,
    k: int,
) -> dict[str, Any]:
    """Post-hoc exploratory cross-tabulation against visual ROI masks (not ground truth)."""
    region_names = list(valid_regions.keys())
    contingency: dict[str, dict[str, int]] = {}
    roi_labels_list: list[np.ndarray] = []
    cluster_labels_list: list[np.ndarray] = []

    for r_idx, r_name in enumerate(region_names):
        mask = valid_regions[r_name]
        c_vals = cluster_map[mask]
        contingency[r_name] = {f"cluster_{c}": int(np.sum(c_vals == c)) for c in range(k)}
        roi_labels_list.append(np.full(c_vals.size, r_idx, dtype=np.int32))
        cluster_labels_list.append(c_vals.astype(np.int32))

    all_roi = np.concatenate(roi_labels_list)
    all_cluster = np.concatenate(cluster_labels_list)
    ari = float(adjusted_rand_score(all_roi, all_cluster)) if len(region_names) > 1 else None
    nmi = float(normalized_mutual_info_score(all_roi, all_cluster)) if len(region_names) > 1 else None

    return {
        "note": (
            "Post-hoc exploratory comparison only. Visual ROI annotations are not "
            "laboratory-confirmed disease labels and were NOT used during clustering."
        ),
        "contingency_counts": contingency,
        "adjusted_rand_index_vs_visual_roi": round(ari, 6) if ari is not None else None,
        "normalized_mutual_info_vs_visual_roi": round(nmi, 6) if nmi is not None else None,
    }


def analyze_cube_clustering(
    cube: np.ndarray,
    image_id: str,
    region_masks: dict[str, np.ndarray],
    quality_mask: np.ndarray | None = None,
    wavelengths_nm: np.ndarray | None = None,
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_fit_samples: int = DEFAULT_MAX_FIT_SAMPLES,
    silhouette_samples: int = DEFAULT_SILHOUETTE_SAMPLES,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Run independent, standardized K-Means clustering on one validated hyperspectral cube."""
    axis_info = build_spectral_axis(image_id, wavelengths_nm)
    valid_regions, valid_mask = validate_and_combine_masks(cube, region_masks, quality_mask)

    valid_indices = np.flatnonzero(valid_mask)
    valid_pixel_count = int(valid_indices.size)
    max_k = max(k_values)
    if valid_pixel_count < max(max_k + 1, 10):
        raise InsufficientClusteringSamplesError(
            f"Image {image_id} has only {valid_pixel_count} valid pixels; need at least {max(max_k + 1, 10)}."
        )

    rng = np.random.default_rng(random_seed)
    fit_count = min(max_fit_samples, valid_pixel_count)
    fit_indices = sample_spatial_grid_indices(valid_mask, fit_count, rng)
    fit_X = _extract_flat_spectra(cube, fit_indices)

    scaler = StandardScaler()
    fit_X_scaled = scaler.fit_transform(fit_X)

    # Subsample for silhouette score to avoid O(N^2) memory blowup
    sil_count = min(silhouette_samples, fit_count)
    sil_rng = np.random.default_rng(random_seed + 1)
    sil_sub_idx = sil_rng.choice(fit_count, size=sil_count, replace=False) if sil_count < fit_count else np.arange(fit_count)
    sil_X_scaled = fit_X_scaled[sil_sub_idx]

    # Spatial block checkerboard split for spatial stability evaluation
    height, width = valid_mask.shape
    rows, cols = np.divmod(fit_indices, width)
    block_parity = ((rows // SPATIAL_BLOCK_SIZE) + (cols // SPATIAL_BLOCK_SIZE)) % 2
    even_mask = block_parity == 0
    odd_mask = block_parity == 1
    can_check_spatial = int(even_mask.sum()) >= max_k + 2 and int(odd_mask.sum()) >= max_k + 2

    k_results: dict[int, dict[str, Any]] = {}
    cluster_maps: dict[int, np.ndarray] = {}
    mean_profiles: dict[int, np.ndarray] = {}
    std_profiles: dict[int, np.ndarray] = {}

    for k in k_values:
        km = KMeans(n_clusters=k, random_state=random_seed, n_init=10)
        km.fit(fit_X_scaled)

        # Silhouette on subsample
        sil_labels = km.predict(sil_X_scaled)
        n_unique_sil = len(np.unique(sil_labels))
        if 2 <= n_unique_sil < sil_count:
            sil_score = round(float(silhouette_score(sil_X_scaled, sil_labels)), 6)
        else:
            sil_score = None

        # Predict all valid pixels in batches
        all_labels = _predict_in_batches(cube, valid_indices, scaler, km, batch_size=batch_size)
        cmap = np.full((height, width), -1, dtype=np.int16)
        cmap.reshape(-1)[valid_indices] = all_labels
        cluster_maps[k] = cmap

        prof = _compute_cluster_profiles(cube, valid_indices, all_labels, k, batch_size=batch_size)
        mean_profiles[k] = prof["means"]
        std_profiles[k] = prof["stds"]

        # Seed stability on fit sample
        seed_aris: list[float] = []
        base_fit_labels = km.labels_
        for alt_seed in STABILITY_SEEDS:
            if alt_seed == random_seed:
                continue
            km_alt = KMeans(n_clusters=k, random_state=alt_seed, n_init=10).fit(fit_X_scaled)
            seed_aris.append(float(adjusted_rand_score(base_fit_labels, km_alt.labels_)))

        # Spatial block stability: fit on even blocks, compare predictions on odd blocks vs full fit
        spatial_block_ari: float | None = None
        if can_check_spatial:
            km_even = KMeans(n_clusters=k, random_state=random_seed, n_init=10).fit(fit_X_scaled[even_mask])
            odd_pred_from_even = km_even.predict(fit_X_scaled[odd_mask])
            spatial_block_ari = round(float(adjusted_rand_score(base_fit_labels[odd_mask], odd_pred_from_even)), 6)

        k_entry: dict[str, Any] = {
            "k": k,
            "inertia_standardized": round(float(km.inertia_), 4),
            "silhouette_score": sil_score,
            "silhouette_sample_size": int(sil_count),
            "cluster_sizes": prof["cluster_sizes"],
            "seed_stability_ari_mean": round(float(np.mean(seed_aris)), 6) if seed_aris else None,
            "seed_stability_ari_min": round(float(np.min(seed_aris)), 6) if seed_aris else None,
            "spatial_block_stability_ari": spatial_block_ari,
        }
        if len(valid_regions) > 1:
            k_entry["posthoc_roi_comparison"] = _compute_posthoc_roi_comparison(valid_regions, cmap, k)

        k_results[k] = k_entry

    return {
        "image_id": image_id,
        "status": "analyzed",
        "spectral_axis": axis_info,
        "valid_pixel_count": valid_pixel_count,
        "fit_sample_count": fit_count,
        "silhouette_sample_size": int(sil_count),
        "k_values": list(k_values),
        "k_results": k_results,
        "cluster_maps": cluster_maps,
        "mean_profiles": mean_profiles,
        "std_profiles": std_profiles,
        "valid_mask": valid_mask,
        "valid_regions": valid_regions,
    }


def _load_metadata_records() -> dict[str, dict[str, str]]:
    path = RAW_DIR / "metadata.tsv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset metadata file is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {row["image_id"].strip(): row for row in csv.DictReader(stream, delimiter="\t")}


def _load_cube_inputs(image_id: str) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray | None, np.ndarray | None]:
    cube_path = RAW_DIR / f"{image_id}.npz"
    if not cube_path.is_file():
        raise FileNotFoundError(f"Raw cube is missing: {cube_path}")

    if image_id == "2436":
        roi_path = PROCESSED_DIR / "cubes" / "2436_leaf_roi.npz"
        quality_path = PROCESSED_DIR / "quality_masks" / "2436_quality_mask.npz"
        with np.load(roi_path, allow_pickle=False) as rf:
            roi = rf["leaf_mask"].astype(bool)
            wavelengths = rf["wavelengths_nm"].astype(np.float64)
        with np.load(quality_path, allow_pickle=False) as qf:
            quality = qf["quality_mask"].astype(bool)
        with np.load(cube_path, allow_pickle=False) as cf:
            cube = cf["arr_0"]
        return cube, {"leaf_roi": roi}, quality, wavelengths

    if image_id == "3079":
        ann_path = PROCESSED_DIR / "segmentation" / "3079_lesion_level_annotations.npz"
        with np.load(ann_path, allow_pickle=False) as af:
            masks = {
                "visible_lesion": af["visible_lesion_mask"].astype(bool),
                "adjacent_unaffected": af["adjacent_non_lesioned_stem_mask"].astype(bool),
                "comparison_stem": af["comparison_stem_mask"].astype(bool),
            }
        with np.load(cube_path, allow_pickle=False) as cf:
            cube = cf["arr_0"]
        return cube, masks, None, None

    raise ValueError(f"No supported existing ROI is configured for image {image_id}.")


def _save_figures(image_id: str, res: dict[str, Any]) -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    k_values: list[int] = res["k_values"]
    axis_values = np.asarray(res["spectral_axis"]["values"], dtype=np.float64)
    axis_label = res["spectral_axis"]["axis_label"]

    # 1. Spatial cluster maps for K = 2, 3, 4, 5
    fig, axes = plt.subplots(1, len(k_values), figsize=(4.2 * len(k_values), 4.5))
    if len(k_values) == 1:
        axes = [axes]
    cmap_discrete = plt.get_cmap("tab10")
    for ax, k in zip(axes, k_values):
        c_map = res["cluster_maps"][k].astype(float)
        c_map[c_map < 0] = np.nan
        ax.imshow(np.ma.masked_invalid(c_map), cmap=cmap_discrete, vmin=0, vmax=9, interpolation="nearest")
        sil = res["k_results"][k]["silhouette_score"]
        sil_txt = f"Sil={sil:.3f}" if sil is not None else "Sil=N/A"
        ax.set_title(f"K={k} ({sil_txt})", fontsize=10)
        ax.set_axis_off()
    fig.suptitle(f"Image {image_id}: Spatial K-Means Cluster Maps (Masked ROI)", fontsize=12)
    fig.tight_layout()
    spatial_fig_path = FIGURE_DIR / f"{image_id}_clustering_spatial_maps.png"
    fig.savefig(spatial_fig_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    # 2. Cluster-wise spectral profiles for K=3 (and best silhouette K if different, or 2x2 grid for K=2..5)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    for ax, k in zip(axes.flat, k_values):
        means = res["mean_profiles"][k]
        stds = res["std_profiles"][k]
        for c in range(k):
            color = cmap_discrete(c)
            ax.plot(axis_values, means[c], color=color, linewidth=1.3, label=f"C{c}")
            ax.fill_between(axis_values, means[c] - stds[c], means[c] + stds[c], color=color, alpha=0.12)
        ax.set_title(f"K={k} Mean ± 1 SD", fontsize=10)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="upper left")
    for ax in axes[1, :]:
        ax.set_xlabel(axis_label)
    for ax in axes[:, 0]:
        ax.set_ylabel("Stored NPZ Value")
    fig.suptitle(f"Image {image_id}: Cluster-wise Spectral Profiles ({axis_label})", fontsize=12)
    fig.tight_layout()
    prof_fig_path = FIGURE_DIR / f"{image_id}_clustering_spectral_profiles.png"
    fig.savefig(prof_fig_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    # 3. Silhouette, inertia & cluster-size distribution
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    sils = [res["k_results"][k]["silhouette_score"] or 0.0 for k in k_values]
    axes[0].plot(k_values, sils, marker="o", color="#22d3ee", linewidth=2)
    axes[0].set_xticks(k_values)
    axes[0].set_xlabel("Number of clusters (K)")
    axes[0].set_ylabel("Silhouette score (subsampled)")
    axes[0].set_title(f"Image {image_id}: Silhouette Score vs K")
    axes[0].grid(alpha=0.25)

    # Stacked bar of cluster proportions per K
    bottom = np.zeros(len(k_values))
    max_k = max(k_values)
    for c in range(max_k):
        heights = []
        for k in k_values:
            sizes = res["k_results"][k]["cluster_sizes"]
            pct = sizes[c]["percentage"] if c < len(sizes) else 0.0
            heights.append(pct)
        axes[1].bar(k_values, heights, bottom=bottom, color=cmap_discrete(c), label=f"C{c}")
        bottom += np.array(heights)
    axes[1].set_xticks(k_values)
    axes[1].set_xlabel("Number of clusters (K)")
    axes[1].set_ylabel("Cluster share (% of valid ROI)")
    axes[1].set_title(f"Image {image_id}: Cluster Size Distribution")
    axes[1].legend(fontsize=8, ncol=3, loc="upper right")
    axes[1].grid(alpha=0.2, axis="y")
    fig.tight_layout()
    metrics_fig_path = FIGURE_DIR / f"{image_id}_clustering_metrics_and_sizes.png"
    fig.savefig(metrics_fig_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    paths = {
        "spatial_maps": str(spatial_fig_path.relative_to(ROOT)).replace("\\", "/"),
        "spectral_profiles": str(prof_fig_path.relative_to(ROOT)).replace("\\", "/"),
        "metrics_and_sizes": str(metrics_fig_path.relative_to(ROOT)).replace("\\", "/"),
    }

    # 4. Post-hoc ROI comparison for 3079 (K=3)
    if image_id == "3079" and "posthoc_roi_comparison" in res["k_results"][3]:
        comp = res["k_results"][3]["posthoc_roi_comparison"]["contingency_counts"]
        regions = list(comp.keys())
        clusters = [f"cluster_{c}" for c in range(3)]
        mat = np.array([[comp[r][cl] for cl in clusters] for r in regions], dtype=np.float64)
        row_sums = mat.sum(axis=1, keepdims=True)
        pct_mat = np.divide(mat, row_sums, out=np.zeros_like(mat), where=row_sums > 0) * 100.0

        fig, ax = plt.subplots(figsize=(7, 4.5))
        im = ax.imshow(pct_mat, cmap="Blues", vmin=0, vmax=100)
        ax.set_xticks(range(3), [f"Cluster {c}" for c in range(3)])
        ax.set_yticks(range(len(regions)), [r.replace("_", " ").title() for r in regions])
        for i in range(len(regions)):
            for j in range(3):
                ax.text(
                    j, i,
                    f"{pct_mat[i, j]:.1f}%\n({int(mat[i, j]):,})",
                    ha="center", va="center",
                    color="white" if pct_mat[i, j] > 50 else "black",
                    fontsize=9,
                )
        ax.set_title("Image 3079: Post-hoc Exploratory Comparison vs Visual ROIs (K=3)\n(Visual annotations only; not ground-truth labels)")
        fig.colorbar(im, ax=ax, label="% of visual ROI pixels")
        fig.tight_layout()
        roi_fig_path = FIGURE_DIR / "3079_clustering_roi_posthoc_comparison.png"
        fig.savefig(roi_fig_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        paths["roi_posthoc_comparison"] = str(roi_fig_path.relative_to(ROOT)).replace("\\", "/")

    return paths


def _write_cube_artifacts(image_id: str, res: dict[str, Any], cube_meta: dict[str, str]) -> dict[str, Any]:
    CLUSTERING_DIR.mkdir(parents=True, exist_ok=True)
    npz_path = CLUSTERING_DIR / f"{image_id}_clustering.npz"

    npz_payload: dict[str, Any] = {
        "valid_mask": res["valid_mask"],
        "spectral_axis_values": np.asarray(res["spectral_axis"]["values"], dtype=np.float64),
    }
    for k in res["k_values"]:
        npz_payload[f"cluster_map_k{k}"] = res["cluster_maps"][k]
        npz_payload[f"mean_profile_k{k}"] = res["mean_profiles"][k].astype(np.float32)
        npz_payload[f"std_profile_k{k}"] = res["std_profiles"][k].astype(np.float32)

    np.savez_compressed(npz_path, **npz_payload)
    figures = _save_figures(image_id, res)

    summary_entry = {
        "image_id": image_id,
        "status": "analyzed",
        "metadata": {
            "pathogen": cube_meta.get("pathogen", "Unknown"),
            "replicate": int(cube_meta["replicate"]) if "replicate" in cube_meta else None,
            "sample": int(cube_meta["sample"]) if "sample" in cube_meta else None,
            "part": cube_meta.get("part", "Unknown"),
            "date": cube_meta.get("date", "Unknown"),
        },
        "spectral_axis": res["spectral_axis"],
        "valid_pixel_count": res["valid_pixel_count"],
        "fit_sample_count": res["fit_sample_count"],
        "silhouette_sample_size": res["silhouette_sample_size"],
        "k_values": res["k_values"],
        "k_results": {str(k): v for k, v in res["k_results"].items()},
        "artifacts": {
            "npz": str(npz_path.relative_to(ROOT)).replace("\\", "/"),
            "figures": figures,
        },
    }
    summary_path = CLUSTERING_DIR / f"{image_id}_summary.json"
    summary_path.write_text(json.dumps(summary_entry, indent=2, allow_nan=False), encoding="utf-8")
    return summary_entry


def _build_markdown_report(experiment: dict[str, Any]) -> str:
    lines = [
        "# TerraSpectra Phase F3 — Exploratory Unsupervised Spectral Learning",
        "",
        f"**Experiment date:** 2026-11-27  ",
        f"**Algorithm:** Standardized K-Means (`StandardScaler` + `KMeans`, `n_init=10`, `random_state={experiment['config']['random_seed']}`)  ",
        f"**K range evaluated:** {experiment['config']['k_values']}  ",
        f"**Runtime:** {experiment['runtime_seconds']} s | **Peak RSS:** {experiment['peak_rss_mib']} MiB  ",
        "",
        "## 1. Scientific Boundaries & Scope",
        "",
        "- Each hyperspectral cube was processed **independently**; spectral axes were never pooled or aligned.",
        "- **Image 2436** uses its verified ENVI wavelength vector (`397.32–1003.58 nm`).",
        "- **Image 3079** has 204 bands with **no verified wavelength calibration** and strictly uses zero-based band indices (`0–203`).",
        "- **Image 2973** was skipped because no validated ROI mask exists; no ad-hoc segmentation was invented.",
        "- Visual ROI labels for image 3079 are treated strictly as **post-hoc exploratory visual annotations**, not laboratory-confirmed disease ground truth, and were **never** used during clustering.",
        "- **Pixels are not independent biological samples.** This experiment demonstrates an exploratory unsupervised workflow and is **not** a validated disease classifier, pathogen detector, or forecasting model.",
        "",
        "## 2. Configuration & Memory-Conscious Design",
        "",
        f"- **Max fitting sample per cube:** {experiment['config']['max_fit_samples']:,} pixels via deterministic spatial grid-cell sampling (`{SPATIAL_GRID_SIZE}x{SPATIAL_GRID_SIZE}` tiles).",
        f"- **Batch prediction:** All valid ROI pixels assigned in batches of {experiment['config']['batch_size']:,} pixels; only 1 cube loaded in memory at a time.",
        f"- **Silhouette evaluation:** Computed on a deterministic subsample of {experiment['config']['silhouette_samples']:,} pixels to avoid $O(N^2)$ pairwise distance memory pressure.",
        f"- **Stability evaluation:** Seed stability across seeds `{STABILITY_SEEDS}` (Adjusted Rand Index) and spatial block stability (`{SPATIAL_BLOCK_SIZE}x{SPATIAL_BLOCK_SIZE}` checkerboard split).",
        "",
        "## 3. Per-Cube Results",
        "",
    ]

    for entry in experiment["cubes"]:
        if entry["status"] == "skipped":
            lines.append(f"### Image {entry['image_id']} (Skipped)")
            lines.append(f"- **Reason:** {entry['reason']}")
            lines.append("")
            continue

        lines.append(f"### Image {entry['image_id']} ({entry['spectral_axis']['axis_label']})")
        lines.append(f"- **Valid ROI pixels:** {entry['valid_pixel_count']:,} | **Fit sample:** {entry['fit_sample_count']:,}")
        lines.append(f"- **Calibration status:** {entry['spectral_axis']['calibration_status']}")
        lines.append("")
        lines.append("| K | Silhouette (subsampled) | Inertia (std) | Seed ARI (mean) | Spatial Block ARI | Cluster Shares (%) |")
        lines.append("|---:|---:|---:|---:|---:|---|")
        for k_str in [str(k) for k in entry["k_values"]]:
            kr = entry["k_results"][k_str]
            shares = ", ".join(f"C{c['cluster_id']}: {c['percentage']:.1f}%" for c in kr["cluster_sizes"])
            sil = f"{kr['silhouette_score']:.4f}" if kr["silhouette_score"] is not None else "N/A"
            s_ari = f"{kr['seed_stability_ari_mean']:.4f}" if kr["seed_stability_ari_mean"] is not None else "N/A"
            sp_ari = f"{kr['spatial_block_stability_ari']:.4f}" if kr["spatial_block_stability_ari"] is not None else "N/A"
            lines.append(f"| {k_str} | {sil} | {kr['inertia_standardized']:.1f} | {s_ari} | {sp_ari} | {shares} |")
        lines.append("")

        if entry["image_id"] == "3079" and "posthoc_roi_comparison" in entry["k_results"]["3"]:
            comp = entry["k_results"]["3"]["posthoc_roi_comparison"]
            lines.append("#### Image 3079 Post-hoc Exploratory Comparison (K=3 vs Visual ROIs)")
            lines.append(f"> {comp['note']}")
            lines.append(f"- **ARI vs visual ROIs:** {comp['adjusted_rand_index_vs_visual_roi']} | **NMI:** {comp['normalized_mutual_info_vs_visual_roi']}")
            lines.append("")
            lines.append("| Visual ROI | Cluster 0 | Cluster 1 | Cluster 2 |")
            lines.append("|---|---:|---:|---:|")
            for r_name, counts in comp["contingency_counts"].items():
                lines.append(f"| {r_name} | {counts['cluster_0']:,} | {counts['cluster_1']:,} | {counts['cluster_2']:,} |")
            lines.append("")

    lines.extend([
        "## 4. Limitations & Why This Is Not a Classifier",
        "",
        "1. **Spatial autocorrelation:** Neighboring pixels on the same leaf or stem are strongly correlated; high seed/spatial ARI reflects within-specimen spectral structure, not population-level generalization.",
        "2. **Specimen count:** Each cube represents a single biological specimen (*B. pseudocinerea* only, zero control cubes locally).",
        "3. **Calibration asymmetry:** Image 3079 lacks verified wavelength calibration; clusters cannot be transferred between 2436 and 3079.",
        "4. **Unsupervised clusters ≠ biological classes:** Clusters capture illumination geometry, curvature, specular highlights, and pigmentation variation alongside visual lesion contrast.",
    ])
    return "\n".join(lines) + "\n"


def run_clustering_experiment(
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_fit_samples: int = DEFAULT_MAX_FIT_SAMPLES,
    silhouette_samples: int = DEFAULT_SILHOUETTE_SAMPLES,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Execute Phase F3 clustering across eligible local cubes and save all artifacts."""
    metadata_records = _load_metadata_records()
    cube_entries: list[dict[str, Any]] = []
    start_time = time.perf_counter()

    with _PeakRssMonitor() as mem:
        for image_id in IMAGE_IDS:
            if image_id == "2973":
                cube_entries.append({
                    "image_id": "2973",
                    "status": "skipped",
                    "reason": "No validated ROI mask exists for image 2973; no segmentation was invented.",
                })
                continue

            cube, region_masks, quality_mask, wavelengths = _load_cube_inputs(image_id)
            res = analyze_cube_clustering(
                cube=cube,
                image_id=image_id,
                region_masks=region_masks,
                quality_mask=quality_mask,
                wavelengths_nm=wavelengths,
                k_values=k_values,
                random_seed=random_seed,
                max_fit_samples=max_fit_samples,
                silhouette_samples=silhouette_samples,
                batch_size=batch_size,
            )
            entry = _write_cube_artifacts(image_id, res, metadata_records.get(image_id, {}))
            cube_entries.append(entry)
            del cube, res, region_masks, quality_mask, wavelengths

    runtime = round(time.perf_counter() - start_time, 3)
    peak_mib = round(mem.peak_bytes / (1024 * 1024), 2) if mem.peak_bytes is not None else None

    experiment = {
        "phase": "F3",
        "analysis": "exploratory_unsupervised_spectral_clustering",
        "config": {
            "algorithm": "KMeans",
            "standardization": "StandardScaler (per-cube, fit on sampled pixels)",
            "k_values": list(k_values),
            "random_seed": random_seed,
            "stability_seeds": list(STABILITY_SEEDS),
            "max_fit_samples": max_fit_samples,
            "silhouette_samples": silhouette_samples,
            "batch_size": batch_size,
            "spatial_grid_size": SPATIAL_GRID_SIZE,
            "spatial_block_size": SPATIAL_BLOCK_SIZE,
        },
        "runtime_seconds": runtime,
        "peak_rss_mib": peak_mib,
        "complete_cubes_loaded_simultaneously": 1,
        "cubes": cube_entries,
        "scientific_limitations": [
            "Exploratory unsupervised clustering only; not a disease classifier, pathogen identifier, or forecasting model.",
            "Pixels are spatially autocorrelated and do not represent independent biological samples.",
            "Image 2436 has verified ENVI wavelengths (397.32-1003.58 nm); image 3079 strictly uses zero-based band indices (0-203).",
            "Image 3079 visual ROI annotations are not laboratory-confirmed labels and were excluded from model fitting.",
            "NPZ measurements are analyzed as stored without arbitrary clipping.",
        ],
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(experiment, indent=2, allow_nan=False), encoding="utf-8")
    REPORT_MD_PATH.write_text(_build_markdown_report(experiment), encoding="utf-8")
    return experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase F3 unsupervised K-Means spectral clustering.")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED)
    parser.add_argument("--max-samples", type=int, default=DEFAULT_MAX_FIT_SAMPLES)
    parser.add_argument("--silhouette-samples", type=int, default=DEFAULT_SILHOUETTE_SAMPLES)
    args = parser.parse_args()

    exp = run_clustering_experiment(
        random_seed=args.seed,
        max_fit_samples=args.max_samples,
        silhouette_samples=args.silhouette_samples,
    )
    print(f"Phase F3 clustering completed in {exp['runtime_seconds']}s | Peak RSS: {exp['peak_rss_mib']} MiB")
    for c in exp["cubes"]:
        if c["status"] == "skipped":
            print(f"  {c['image_id']}: skipped ({c['reason']})")
        else:
            print(f"  {c['image_id']}: analyzed ({c['valid_pixel_count']:,} valid px)")
            for k_str, kr in c["k_results"].items():
                print(f"    K={k_str}: sil={kr['silhouette_score']}, seed_ARI={kr['seed_stability_ari_mean']}, spatial_ARI={kr['spatial_block_stability_ari']}")


if __name__ == "__main__":
    main()
