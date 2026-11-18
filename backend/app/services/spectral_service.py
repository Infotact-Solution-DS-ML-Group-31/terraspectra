"""
Service for spectral profile retrieval and calculations.
"""

from typing import Optional, List
import numpy as np
import pandas as pd

from backend.app.config import (
    RAW_DATA_DIR,
    FEATURES_DIR,
    LOCAL_CUBE_IDS
)
from backend.app.schemas.spectral import SpectralProfileResponse, SpectralBandPoint


class SpectralService:
    def get_spectral_profile(self, image_id: str) -> Optional[SpectralProfileResponse]:
        if image_id not in LOCAL_CUBE_IDS:
            return None

        points: List[SpectralBandPoint] = []

        if image_id == "2436":
            # Load verified leaf ROI features for 2436
            csv_path = FEATURES_DIR / "2436_spectral_features.csv"
            if not csv_path.exists():
                return None

            df = pd.read_csv(csv_path)
            for idx, row in df.iterrows():
                points.append(SpectralBandPoint(
                    band_index=int(idx),
                    wavelength_nm=float(row["wavelength_nm"]),
                    mean=float(row["mean_reflectance"]),
                    median=float(row["median_reflectance"]),
                    std=float(row["std_reflectance"]) if "std_reflectance" in row else None,
                    q25=float(row["q25_reflectance"]) if "q25_reflectance" in row else None,
                    q75=float(row["q75_reflectance"]) if "q75_reflectance" in row else None
                ))

            notes = [
                "Extracted from verified leaf ROI (53,854 pixels).",
                "Wavelengths verified against Specim IQ ENVI headers (397.32 - 1003.58 nm).",
                "Flagged outlier pixels set to NaN without unverified interpolation."
            ]
            return SpectralProfileResponse(
                image_id=image_id,
                spectral_axis="wavelength_nm",
                total_bands=len(points),
                has_verified_wavelengths=True,
                data=points,
                scientific_notes=notes
            )

        elif image_id == "3079":
            # Load verified lesion-level features for 3079
            csv_path = FEATURES_DIR / "3079_lesion_level_spectral_features.csv"
            if not csv_path.exists():
                return None

            df = pd.read_csv(csv_path)
            for idx, row in df.iterrows():
                points.append(SpectralBandPoint(
                    band_index=int(row["band_index_0based"]),
                    wavelength_nm=None,  # Strictly None
                    mean=float(row["lesion_mean"]),
                    median=float(row["lesion_median"]),
                    std=float(row["lesion_std"]),
                    q25=float(row["lesion_q25"]),
                    q75=float(row["lesion_q75"])
                ))

            notes = [
                "Zero-based band indices strictly used (no verified wavelength calibration).",
                "Mean and median reflect the visible necrotic lesion ROI (4,137 pixels).",
                "Visually annotated lesion is necrotic tissue, not laboratory-confirmed pathogen identity."
            ]
            return SpectralProfileResponse(
                image_id=image_id,
                spectral_axis="zero_based_band_indices",
                total_bands=len(points),
                has_verified_wavelengths=False,
                data=points,
                scientific_notes=notes
            )

        elif image_id == "2973":
            # Extract on-the-fly from 2973.npz
            cube_file = RAW_DATA_DIR / f"{image_id}.npz"
            if not cube_file.exists():
                return None

            with np.load(cube_file) as data:
                cube = data[list(data.keys())[0]].astype(np.float32)

            means = np.nanmean(cube, axis=(0, 1))
            medians = np.nanmedian(cube, axis=(0, 1))
            stds = np.nanstd(cube, axis=(0, 1))

            for b in range(cube.shape[2]):
                points.append(SpectralBandPoint(
                    band_index=b,
                    wavelength_nm=None,  # Strictly None
                    mean=float(means[b]),
                    median=float(medians[b]),
                    std=float(stds[b])
                ))

            notes = [
                "Zero-based band indices strictly used (no verified wavelength calibration).",
                "Whole-cube average profile across all 512x512 pixels.",
                "Values reflect author-normalized NPZ values."
            ]
            return SpectralProfileResponse(
                image_id=image_id,
                spectral_axis="zero_based_band_indices",
                total_bands=len(points),
                has_verified_wavelengths=False,
                data=points,
                scientific_notes=notes
            )

        return None


spectral_service = SpectralService()
