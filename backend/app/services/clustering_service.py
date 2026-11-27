"""
Service for exposing Phase F3 unsupervised spectral clustering artifacts.
"""

import json
import math
from pathlib import Path
from typing import List, Optional

import numpy as np

from backend.app.config import CLUSTERING_DIR, LOCAL_CUBE_IDS
from backend.app.schemas.clustering import (
    ClusterProfileSeries,
    ClusterSizeInfo,
    ClusteringCubeSummary,
    ClusteringKResult,
    ClusteringProfilesResponse,
    ClusteringSpatialMapResponse,
    ClusteringSpatialPoint,
    ClusteringSpectralAxis,
)


ANALYZED_IDS = ("2436", "3079")
DISCLAIMERS = (
    "Exploratory unsupervised K-Means clustering only; clusters are not disease classes or biological ground truth.",
    "Each cube was standardized and clustered independently; cluster IDs are not comparable across cubes.",
    "Pixels are spatially autocorrelated and do not represent independent biological samples.",
)


class ClusteringService:
    def _summary_path(self, image_id: str) -> Path:
        return CLUSTERING_DIR / f"{image_id}_summary.json"

    def _npz_path(self, image_id: str) -> Path:
        return CLUSTERING_DIR / f"{image_id}_clustering.npz"

    def _load_summary(self, image_id: str) -> Optional[dict]:
        path = self._summary_path(image_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _axis(self, summary: dict) -> ClusteringSpectralAxis:
        axis = summary["spectral_axis"]
        return ClusteringSpectralAxis(
            axis_type=axis["axis_type"],
            axis_label=axis["axis_label"],
            values=[float(v) for v in axis["values"]],
            calibration_status=axis["calibration_status"],
        )

    def list_cubes(self) -> List[ClusteringCubeSummary]:
        results: List[ClusteringCubeSummary] = []
        for image_id in ("2436", "2973", "3079"):
            if image_id in ANALYZED_IDS:
                raw = self._load_summary(image_id)
                if raw is None:
                    results.append(ClusteringCubeSummary(
                        image_id=image_id,
                        status="skipped",
                        available=False,
                        reason="Clustering summary artifact is missing.",
                        scientific_disclaimer=" ".join(DISCLAIMERS),
                    ))
                    continue

                k_results = {}
                for k_str, kr in raw["k_results"].items():
                    k_results[k_str] = ClusteringKResult(
                        k=int(kr["k"]),
                        inertia_standardized=float(kr["inertia_standardized"]),
                        silhouette_score=kr.get("silhouette_score"),
                        silhouette_sample_size=int(kr["silhouette_sample_size"]),
                        cluster_sizes=[ClusterSizeInfo(**cs) for cs in kr["cluster_sizes"]],
                        seed_stability_ari_mean=kr.get("seed_stability_ari_mean"),
                        seed_stability_ari_min=kr.get("seed_stability_ari_min"),
                        spatial_block_stability_ari=kr.get("spatial_block_stability_ari"),
                        posthoc_roi_comparison=kr.get("posthoc_roi_comparison"),
                    )

                results.append(ClusteringCubeSummary(
                    image_id=image_id,
                    status="analyzed",
                    available=True,
                    spectral_axis=self._axis(raw),
                    valid_pixel_count=raw.get("valid_pixel_count"),
                    fit_sample_count=raw.get("fit_sample_count"),
                    silhouette_sample_size=raw.get("silhouette_sample_size"),
                    k_values=[int(k) for k in raw.get("k_values", [])],
                    k_results=k_results,
                    scientific_disclaimer=" ".join(DISCLAIMERS),
                ))
            else:
                results.append(ClusteringCubeSummary(
                    image_id=image_id,
                    status="skipped",
                    available=False,
                    reason="No validated ROI mask exists for image 2973; no segmentation was invented.",
                    scientific_disclaimer=" ".join(DISCLAIMERS),
                ))
        return results

    def get_summary(self, image_id: str) -> Optional[ClusteringCubeSummary]:
        if image_id not in LOCAL_CUBE_IDS:
            return None
        for cube in self.list_cubes():
            if cube.image_id == image_id:
                return cube
        return None

    def get_profiles(self, image_id: str, k: int = 3) -> Optional[ClusteringProfilesResponse]:
        if image_id not in ANALYZED_IDS:
            return None
        raw = self._load_summary(image_id)
        npz_path = self._npz_path(image_id)
        if raw is None or not npz_path.exists():
            return None
        if str(k) not in raw.get("k_results", {}):
            return None

        with np.load(npz_path, allow_pickle=False) as data:
            means = data[f"mean_profile_k{k}"]
            stds = data[f"std_profile_k{k}"]

        sizes = raw["k_results"][str(k)]["cluster_sizes"]
        clusters: List[ClusterProfileSeries] = []
        for idx, cs in enumerate(sizes):
            clusters.append(ClusterProfileSeries(
                cluster_id=int(cs["cluster_id"]),
                pixel_count=int(cs["pixel_count"]),
                percentage=float(cs["percentage"]),
                mean_profile=[round(float(v), 6) for v in means[idx]],
                std_profile=[round(float(v), 6) for v in stds[idx]],
            ))

        return ClusteringProfilesResponse(
            image_id=image_id,
            k=k,
            independent_fit=True,
            spectral_axis=self._axis(raw),
            clusters=clusters,
            scientific_disclaimer=" ".join(DISCLAIMERS),
        )

    def get_spatial_map(
        self,
        image_id: str,
        k: int = 3,
        max_size: int = 64,
    ) -> Optional[ClusteringSpatialMapResponse]:
        if image_id not in ANALYZED_IDS:
            return None
        raw = self._load_summary(image_id)
        npz_path = self._npz_path(image_id)
        if raw is None or not npz_path.exists():
            return None
        key = f"cluster_map_k{k}"

        with np.load(npz_path, allow_pickle=False) as data:
            if key not in data:
                return None
            cmap = data[key]

        height, width = cmap.shape
        step_r = max(1, math.ceil(height / max_size))
        step_c = max(1, math.ceil(width / max_size))
        points: List[ClusteringSpatialPoint] = []
        out_rows = 0
        out_cols = 0

        for r_idx, r0 in enumerate(range(0, height, step_r)):
            out_rows = r_idx + 1
            r1 = min(height, r0 + step_r)
            col_count = 0
            for c_idx, c0 in enumerate(range(0, width, step_c)):
                col_count = c_idx + 1
                c1 = min(width, c0 + step_c)
                block = cmap[r0:r1, c0:c1]
                valid_vals = block[block >= 0]
                if valid_vals.size == 0:
                    points.append(ClusteringSpatialPoint(
                        row=r_idx,
                        column=c_idx,
                        cluster_id=None,
                        valid_pixel_count=0,
                    ))
                else:
                    vals, counts = np.unique(valid_vals, return_counts=True)
                    majority_cluster = int(vals[int(np.argmax(counts))])
                    points.append(ClusteringSpatialPoint(
                        row=r_idx,
                        column=c_idx,
                        cluster_id=majority_cluster,
                        valid_pixel_count=int(valid_vals.size),
                    ))
            out_cols = col_count

        return ClusteringSpatialMapResponse(
            image_id=image_id,
            k=k,
            independent_fit=True,
            width=width,
            height=height,
            downsampled_width=out_cols,
            downsampled_height=out_rows,
            data=points,
            spectral_axis=self._axis(raw),
            scientific_disclaimer=" ".join(DISCLAIMERS),
        )


clustering_service = ClusteringService()
