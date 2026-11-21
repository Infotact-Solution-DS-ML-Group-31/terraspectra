"""
Service for exposing saved real-cube PCA artifacts.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from backend.app.config import PCA_DIR, LOCAL_CUBE_IDS
from backend.app.schemas.pca import (
    PcaCubeSummary,
    PcaExplainedVariancePoint,
    PcaExplainedVarianceResponse,
    PcaLoadingPoint,
    PcaLoadingResponse,
    PcaSpatialPoint,
    PcaSpatialScoresResponse,
    PcaSpectralAxis,
)


ANALYZED_IDS = ("2436", "3079")
DISCLAIMERS = (
    "PCA was fit independently per cube; component scores and loadings are not comparable across cubes as a common basis.",
    "PCA components are exploratory mathematical components, not disease classes or healthy/diseased indicators.",
    "No disease classification, forecasting, prediction, or clinical interpretation is claimed.",
)


class PcaService:
    def _summary_path(self, image_id: str) -> Path:
        return PCA_DIR / f"{image_id}_summary.json"

    def _npz_path(self, image_id: str) -> Path:
        return PCA_DIR / f"{image_id}_pca.npz"

    def _load_summary(self, image_id: str) -> Optional[dict]:
        path = self._summary_path(image_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _axis(self, summary: dict) -> PcaSpectralAxis:
        axis = summary["spectral_axis"]
        return PcaSpectralAxis(
            axis_type=axis["axis_type"],
            axis_label=axis["axis_label"],
            values=list(axis["values"]),
            calibration_status=axis["calibration_status"],
        )

    def list_cubes(self) -> List[PcaCubeSummary]:
        results: List[PcaCubeSummary] = []
        for image_id in ("2436", "2973", "3079"):
            if image_id in ANALYZED_IDS:
                summary = self._load_summary(image_id)
                if summary is None:
                    results.append(PcaCubeSummary(
                        image_id=image_id,
                        status="skipped",
                        available=False,
                        region_distributions_available=False,
                        region_distributions_reason="PCA summary artifact is missing.",
                        scientific_disclaimer=" ".join(DISCLAIMERS),
                    ))
                    continue
                axis = self._axis(summary)
                region_reason = None
                region_available = False
                if image_id == "3079":
                    region_reason = (
                        "Only the region score-distribution figure is saved; no structured distribution artifact is available."
                    )
                results.append(PcaCubeSummary(
                    image_id=image_id,
                    status="analyzed",
                    available=True,
                    spectral_axis=axis,
                    spectral_features_per_pixel=summary.get("spectral_features_per_pixel"),
                    valid_pixel_count=summary.get("valid_pixel_count"),
                    fit_sample_count=summary.get("fit_sample_count"),
                    cumulative_explained_variance_ratio=summary.get("cumulative_explained_variance_ratio"),
                    region_distributions_available=region_available,
                    region_distributions_reason=region_reason,
                    scientific_disclaimer=" ".join(DISCLAIMERS),
                ))
            else:
                results.append(PcaCubeSummary(
                    image_id=image_id,
                    status="skipped",
                    available=False,
                    region_distributions_available=False,
                    region_distributions_reason="No PCA analysis is available for image 2973.",
                    scientific_disclaimer=" ".join(DISCLAIMERS),
                ))
        return results

    def get_summary(self, image_id: str) -> Optional[PcaCubeSummary]:
        if image_id not in LOCAL_CUBE_IDS:
            return None
        for cube in self.list_cubes():
            if cube.image_id == image_id:
                return cube
        return None

    def get_explained_variance(self, image_id: str) -> Optional[PcaExplainedVarianceResponse]:
        if image_id not in ANALYZED_IDS:
            return None
        summary = self._load_summary(image_id)
        npz_path = self._npz_path(image_id)
        if summary is None or not npz_path.exists():
            return None
        with np.load(npz_path, allow_pickle=False) as data:
            ratios = [float(value) for value in data["explained_variance_ratio"][:3]]
        if len(ratios) != 3:
            return None
        cumulative = 0.0
        points = []
        for index, ratio in enumerate(ratios, start=1):
            cumulative += ratio
            points.append(PcaExplainedVariancePoint(
                component=f"PC{index}",
                explained_variance_ratio=ratio,
                cumulative_explained_variance_ratio=cumulative,
            ))
        return PcaExplainedVarianceResponse(
            image_id=image_id,
            independent_fit=True,
            cumulative_explained_variance_ratio=cumulative,
            data=points,
            spectral_axis=self._axis(summary),
        )

    def get_loadings(self, image_id: str) -> Optional[PcaLoadingResponse]:
        if image_id not in ANALYZED_IDS:
            return None
        summary = self._load_summary(image_id)
        csv_path = PCA_DIR / f"{image_id}_component_loadings.csv"
        if summary is None or not csv_path.exists():
            return None
        positions: List[object] = []
        pc1: List[float] = []
        pc2: List[float] = []
        pc3: List[float] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            first_column = reader.fieldnames[0] if reader.fieldnames else None
            if not first_column:
                return None
            for row in reader:
                raw_position = row[first_column]
                position = float(raw_position) if image_id == "2436" else int(raw_position)
                positions.append(position)
                pc1.append(float(row["PC1"]))
                pc2.append(float(row["PC2"]))
                pc3.append(float(row["PC3"]))
        if not positions:
            return None
        axis = self._axis(summary)
        return PcaLoadingResponse(
            image_id=image_id,
            independent_fit=True,
            spectral_axis=axis,
            data=[
                PcaLoadingPoint(
                    spectral_position=float(position),
                    pc1=pc1[index],
                    pc2=pc2[index],
                    pc3=pc3[index],
                )
                for index, position in enumerate(positions)
            ],
        )

    def get_spatial_scores(self, image_id: str, max_size: int = 64) -> Optional[PcaSpatialScoresResponse]:
        if image_id not in ANALYZED_IDS:
            return None
        summary = self._load_summary(image_id)
        npz_path = self._npz_path(image_id)
        if summary is None or not npz_path.exists():
            return None
        with np.load(npz_path, allow_pickle=False) as data:
            score_map = np.asarray(data["score_map"])
            required_width = int(max_size)
        height, width, _ = score_map.shape
        down_width = min(width, required_width)
        down_height = min(height, required_width)
        row_edges = np.linspace(0, height, down_height + 1, dtype=int)
        col_edges = np.linspace(0, width, down_width + 1, dtype=int)
        points: List[PcaSpatialPoint] = []
        for row_index in range(down_height):
            row_slice = slice(row_edges[row_index], row_edges[row_index + 1])
            for col_index in range(down_width):
                col_slice = slice(col_edges[col_index], col_edges[col_index + 1])
                block = score_map[row_slice, col_slice, :]
                valid = np.isfinite(block).all(axis=2)
                count = int(valid.sum())
                if count == 0:
                    points.append(PcaSpatialPoint(
                        row=row_index,
                        column=col_index,
                        pc1=None,
                        pc2=None,
                        pc3=None,
                        valid_pixel_count=0,
                    ))
                else:
                    mean = block[valid].mean(axis=0)
                    points.append(PcaSpatialPoint(
                        row=row_index,
                        column=col_index,
                        pc1=float(mean[0]),
                        pc2=float(mean[1]),
                        pc3=float(mean[2]),
                        valid_pixel_count=count,
                    ))
        return PcaSpatialScoresResponse(
            image_id=image_id,
            independent_fit=True,
            width=width,
            height=height,
            downsampled_width=down_width,
            downsampled_height=down_height,
            data=points,
            spectral_axis=self._axis(summary),
        )


pca_service = PcaService()
