
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = Path("data/processed/cubes/2436_leaf_roi.npz")

OUTPUT_DIR = Path("data/processed/features")
REPORT_DIR = Path("data/processed/reports")
FIGURE_DIR = Path("outputs/figures")

IMAGE_ID = "2436"


def main():
    print("=" * 65)
    print("TERRASPECTRA SPECTRAL FEATURE EXTRACTION")
    print("=" * 65)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    data = np.load(INPUT_FILE, allow_pickle=False)

    cube = data["cube"].astype(np.float32)
    wavelengths = data["wavelengths_nm"].astype(np.float32)
    leaf_mask = data["leaf_mask"].astype(bool)

    if cube.ndim != 3:
        raise ValueError("Expected a 3D hyperspectral cube.")

    if cube.shape[2] != len(wavelengths):
        raise ValueError("Cube bands and wavelengths do not match.")

    if cube.shape[:2] != leaf_mask.shape:
        raise ValueError("Leaf mask and cube spatial dimensions differ.")

    # Extract only leaf pixels. Invalid measurements remain NaN.
    leaf_spectra = cube[leaf_mask]

    valid_counts = np.sum(np.isfinite(leaf_spectra), axis=0)

    mean_spectrum = np.nanmean(leaf_spectra, axis=0)
    median_spectrum = np.nanmedian(leaf_spectra, axis=0)
    std_spectrum = np.nanstd(leaf_spectra, axis=0)

    # Create a table with one row per wavelength.
    results = pd.DataFrame({
        "wavelength_nm": wavelengths,
        "mean_reflectance": mean_spectrum,
        "median_reflectance": median_spectrum,
        "std_reflectance": std_spectrum,
        "valid_pixel_count": valid_counts
    })

    output_csv = OUTPUT_DIR / f"{IMAGE_ID}_spectral_features.csv"
    results.to_csv(output_csv, index=False)

    # Plot mean spectrum with standard deviation.
    plt.figure(figsize=(12, 6))

    plt.plot(
        wavelengths,
        mean_spectrum,
        label="Mean reflectance",
        linewidth=1.5
    )

    plt.fill_between(
        wavelengths,
        mean_spectrum - std_spectrum,
        mean_spectrum + std_spectrum,
        alpha=0.2,
        label="Mean ± 1 standard deviation"
    )

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Tomato Leaf Mean Spectral Profile - Image {IMAGE_ID}")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    mean_plot = FIGURE_DIR / f"{IMAGE_ID}_mean_spectral_profile.png"
    plt.savefig(mean_plot, dpi=200)
    plt.close()

    # Plot mean and median spectra together.
    plt.figure(figsize=(12, 6))

    plt.plot(
        wavelengths,
        mean_spectrum,
        label="Mean spectrum"
    )

    plt.plot(
        wavelengths,
        median_spectrum,
        label="Median spectrum",
        alpha=0.85
    )

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Mean vs Median Spectral Profile - Image {IMAGE_ID}")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    comparison_plot = FIGURE_DIR / f"{IMAGE_ID}_mean_median_spectrum.png"
    plt.savefig(comparison_plot, dpi=200)
    plt.close()

    summary = {
        "image_id": IMAGE_ID,
        "leaf_pixels": int(leaf_mask.sum()),
        "spectral_bands": int(len(wavelengths)),
        "wavelength_range_nm": [
            float(wavelengths.min()),
            float(wavelengths.max())
        ],
        "valid_measurements_per_band_min": int(valid_counts.min()),
        "valid_measurements_per_band_max": int(valid_counts.max()),
        "mean_reflectance_min": float(np.nanmin(mean_spectrum)),
        "mean_reflectance_max": float(np.nanmax(mean_spectrum)),
        "mean_reflectance_all_bands": float(np.nanmean(mean_spectrum)),
        "nan_values_in_mean_spectrum": int(np.isnan(mean_spectrum).sum())
    }

    summary_file = REPORT_DIR / f"{IMAGE_ID}_spectral_feature_summary.json"

    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\nExtraction completed.")
    print("Leaf pixels:", int(leaf_mask.sum()))
    print("Spectral bands:", len(wavelengths))
    print("Wavelength range:", wavelengths.min(), "to", wavelengths.max(), "nm")
    print("Valid measurements per band:", valid_counts.min(), "to", valid_counts.max())

    print("\nSaved:")
    print(output_csv)
    print(mean_plot)
    print(comparison_plot)
    print(summary_file)


if __name__ == "__main__":
    main()
