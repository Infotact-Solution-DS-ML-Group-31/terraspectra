
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = Path("data/processed/cubes/2436_leaf_roi.npz")
OUTPUT_DIR = Path("data/processed/reports")
FIGURE_DIR = Path("outputs/figures")


def main():
    data = np.load(INPUT_FILE, allow_pickle=False)

    cube = data["cube"]
    wavelengths = data["wavelengths_nm"]
    leaf_mask = data["leaf_mask"]

    # Extract all leaf spectra, excluding invalid measurements.
    spectra = cube[leaf_mask]

    report = []

    for band in range(cube.shape[2]):
        values = spectra[:, band]
        values = values[np.isfinite(values)]

        report.append({
            "band_index": band,
            "wavelength_nm": wavelengths[band],
            "valid_pixels": len(values),
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "p01": np.percentile(values, 1),
            "p05": np.percentile(values, 5),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99)
        })

    df = pd.DataFrame(report)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / "2436_band_variability_report.csv"
    df.to_csv(csv_path, index=False)

    # Plot robust spectral statistics.
    plt.figure(figsize=(13, 6))

    plt.plot(
        df["wavelength_nm"],
        df["mean"],
        label="Mean"
    )

    plt.plot(
        df["wavelength_nm"],
        df["median"],
        label="Median"
    )

    plt.fill_between(
        df["wavelength_nm"],
        df["p05"],
        df["p95"],
        alpha=0.2,
        label="5th–95th percentile"
    )

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title("Image 2436: Spatial Spectral Variability")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    plot_path = FIGURE_DIR / "2436_spectral_variability.png"
    plt.savefig(plot_path, dpi=200)
    plt.close()

    # Inspect important wavelength regions.
    regions = [
        ("Red edge", 690, 715),
        ("NIR variability", 930, 965),
        ("Upper wavelength endpoint", 990, 1004)
    ]

    print("=" * 65)
    print("BAND-LEVEL VARIABILITY INVESTIGATION")
    print("=" * 65)

    for name, lower, upper in regions:
        subset = df[
            (df["wavelength_nm"] >= lower)
            & (df["wavelength_nm"] <= upper)
        ]

        print(f"\n{name}: {lower}-{upper} nm")
        print(
            subset[
                ["wavelength_nm", "mean", "median", "std", "p05", "p95"]
            ].to_string(index=False)
        )

    print("\nLargest mean-median differences:")
    df["mean_median_gap"] = abs(df["mean"] - df["median"])

    print(
        df.nlargest(10, "mean_median_gap")[
            ["wavelength_nm", "mean", "median", "std", "p99"]
        ].to_string(index=False)
    )

    print("\nSaved:")
    print(csv_path)
    print(plot_path)


if __name__ == "__main__":
    main()
