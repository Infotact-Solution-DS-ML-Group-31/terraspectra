"""
Service for hyperspectral cube discovery, metadata queries, and quality metrics.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from backend.app.config import (
    RAW_DATA_DIR,
    METADATA_PATH,
    FIGURES_DIR,
    LOCAL_CUBE_IDS
)
from backend.app.schemas.dataset import DatasetSummary, DatasetMetadata
from backend.app.schemas.quality import QualityMetricsResponse


class DatasetService:
    def __init__(self):
        self._metadata_df = None
        self._load_metadata()

    def _load_metadata(self):
        if METADATA_PATH.exists():
            df = pd.read_csv(METADATA_PATH, sep="\t")
            df["plant_id"] = (
                df["replicate"].astype(str) + "_" +
                df["pathogen"] + "_S" +
                df["sample"].astype(str)
            )
            df["organ_id"] = df["plant_id"] + "_" + df["part"]
            self._metadata_df = df
        else:
            self._metadata_df = pd.DataFrame()

    def list_datasets(self) -> List[DatasetSummary]:
        results = []
        for img_id in LOCAL_CUBE_IDS:
            cube_file = RAW_DATA_DIR / f"{img_id}.npz"
            if not cube_file.exists():
                continue

            # Load cube array header info
            with np.load(cube_file) as data:
                arr = data[list(data.keys())[0]]
                shape = list(arr.shape)
                dtype = str(arr.dtype)

            size_mb = round(cube_file.stat().st_size / (1024 * 1024), 2)
            has_wl = (img_id == "2436")
            cal_status = (
                "Wavelength-calibrated (397.32 - 1003.58 nm)"
                if has_wl else
                "Spectral-band indexed only (no wavelength metadata)"
            )

            # Metadata lookup
            row = self._metadata_df[self._metadata_df["image_id"] == int(img_id)]
            if not row.empty:
                r = row.iloc[0]
                pathogen = str(r["pathogen"])
                replicate = int(r["replicate"])
                sample = int(r["sample"])
                part = str(r["part"])
                date = str(r["date"])
            else:
                pathogen, replicate, sample, part, date = "B. pseudo", 0, 0, "Unknown", "Unknown"

            results.append(DatasetSummary(
                image_id=img_id,
                shape=shape,
                spectral_bands=shape[2] if len(shape) == 3 else 204,
                data_type=dtype,
                file_size_mb=size_mb,
                calibration_status=cal_status,
                has_wavelength_calibration=has_wl,
                pathogen=pathogen,
                replicate=replicate,
                sample=sample,
                part=part,
                date=date
            ))
        return results

    def get_metadata(self, image_id: str) -> Optional[DatasetMetadata]:
        if image_id not in LOCAL_CUBE_IDS:
            return None

        row = self._metadata_df[self._metadata_df["image_id"] == int(image_id)]
        if row.empty:
            return None

        r = row.iloc[0]
        has_wl = (image_id == "2436")
        cal_status = (
            "Wavelength-calibrated (397.32 - 1003.58 nm)"
            if has_wl else
            "Spectral-band indexed only (no verified wavelength calibration)"
        )

        dist = r.get("imaging_distance")
        dist_val = float(dist) if pd.notna(dist) else None

        disclaimer = (
            "Verified Specim IQ ENVI wavelength headers available."
            if has_wl else
            "Wavelength calibration is unavailable for this cube; strictly uses zero-based band indices (0 to 203)."
        )

        return DatasetMetadata(
            image_id=image_id,
            replicate=int(r["replicate"]),
            pathogen=str(r["pathogen"]),
            sample=int(r["sample"]),
            part=str(r["part"]),
            date=str(r["date"]),
            imaging_distance_cm=dist_val,
            integration_time_ms=int(r["integration_time"]),
            weather=str(r["weather"]),
            plant_id=str(r["plant_id"]),
            organ_id=str(r["organ_id"]),
            calibration_status=cal_status,
            verified_wavelengths=has_wl,
            scientific_disclaimer=disclaimer
        )

    def get_preview_path(self, image_id: str) -> Optional[Path]:
        if image_id not in LOCAL_CUBE_IDS:
            return None

        # Look for exact 512x512 preview in outputs/figures
        preview = FIGURES_DIR / f"{image_id}_pseudo_rgb_preview.png"
        if preview.exists():
            return preview

        # Fallback to raw folder preview for 2436 if available
        raw_preview = RAW_DATA_DIR / f"raw_{image_id}" / image_id / f"{image_id}.png"
        if raw_preview.exists():
            return raw_preview

        return None

    def get_quality_metrics(self, image_id: str) -> Optional[QualityMetricsResponse]:
        if image_id not in LOCAL_CUBE_IDS:
            return None

        cube_file = RAW_DATA_DIR / f"{image_id}.npz"
        if not cube_file.exists():
            return None

        with np.load(cube_file) as data:
            arr = data[list(data.keys())[0]].astype(np.float32)

        nan_cnt = int(np.isnan(arr).sum())
        inf_cnt = int(np.isinf(arr).sum())
        min_v = float(np.nanmin(arr))
        max_v = float(np.nanmax(arr))

        gt1_mask = arr > 1.0
        gt1_cnt = int(gt1_mask.sum())
        gt1_pct = float((gt1_cnt / arr.size) * 100.0)

        # Bands where exceedance occurs
        band_sums = gt1_mask.sum(axis=(0, 1))
        active_bands = [int(b) for b in np.where(band_sums > 0)[0]]

        warnings = []
        if gt1_cnt > 0:
            warnings.append(
                f"{gt1_cnt:,} values ({gt1_pct:.3f}%) exceed 1.0, occurring in {len(active_bands)} spectral bands."
            )
        if nan_cnt > 0:
            warnings.append(f"Cube contains {nan_cnt} NaN measurements.")
        if inf_cnt > 0:
            warnings.append(f"Cube contains {inf_cnt} infinite measurements.")

        scientific_notes = [
            "Measurements reflect author-normalized NPZ values and must not be assumed to be calibrated laboratory reflectance.",
            "Values exceeding 1.0 typically result from specular reflections or lighting tilt on plant curvature relative to white reference plates.",
            "Zero values were clipped or removed arbitrarily."
        ]

        return QualityMetricsResponse(
            image_id=image_id,
            nan_count=nan_cnt,
            inf_count=inf_cnt,
            min_value=min_v,
            max_value=max_v,
            values_exceeding_1_count=gt1_cnt,
            values_exceeding_1_percentage=gt1_pct,
            has_values_exceeding_1=(gt1_cnt > 0),
            affected_bands_exceeding_1=active_bands,
            warnings=warnings,
            scientific_notes=scientific_notes
        )


dataset_service = DatasetService()
