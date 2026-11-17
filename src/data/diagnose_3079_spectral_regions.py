
import json
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

CUBE_FILE = Path("data/raw/tomato_botrytis/3079.npz")
MASK_FILE = Path("data/processed/segmentation/3079_roi_annotations.npz")

OUTPUT_DIR = Path("data/processed/features")
REPORT_DIR = Path("data/processed/reports")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load cube and annotations
# ---------------------------------------------------------

print("Loading hyperspectral cube and ROI masks...")

cube_data = np.load(CUBE_FILE)
cube = cube_data["arr_0"].astype(np.float32)

mask_data = np.load(MASK_FILE)

lesion_mask = mask_data["lesion_bearing_stem_mask"].astype(bool)
comparison_mask = mask_data["comparison_stem_mask"].astype(bool)

if cube.ndim != 3:
    raise ValueError(f"Expected a 3D cube, received {cube.shape}")

if lesion_mask.shape != cube.shape[:2]:
    raise ValueError("Lesion mask dimensions do not match cube.")

if comparison_mask.shape != cube.shape[:2]:
    raise ValueError("Comparison mask dimensions do not match cube.")

if np.any(lesion_mask & comparison_mask):
    raise ValueError("ROI masks overlap. Resolve overlap before analysis.")

if not lesion_mask.any() or not comparison_mask.any():
    raise ValueError("One or both ROI masks are empty.")


# ---------------------------------------------------------
# Calculate pixel-level statistics for each band
# ---------------------------------------------------------

def calculate_statistics(pixel_values):
    values = pixel_values[np.isfinite(pixel_values)]

    if len(values) == 0:
        return {
            "valid_pixels": 0,
            "mean": None,
            "median": None,
            "std": None,
            "cv": None,
            "p05": None,
            "p25": None,
            "p75": None,
            "p95": None,
            "iqr": None,
            "skewness": None,
        }

    mean = float(np.mean(values))
    median = float(np.median(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0

    percentiles = np.percentile(values, [5, 25, 75, 95])
    p05, p25, p75, p95 = map(float, percentiles)

    if std > 0:
        standardized = (values - mean) / std
        skewness = float(np.mean(standardized ** 3))
    else:
        skewness = 0.0

    cv = float(std / abs(mean)) if mean != 0 else None

    return {
        "valid_pixels": int(len(values)),
        "mean": mean,
        "median": median,
        "std": std,
        "cv": cv,
        "p05": p05,
        "p25": p25,
        "p75": p75,
        "p95": p95,
        "iqr": float(p75 - p25),
        "skewness": skewness,
    }


# ---------------------------------------------------------
# Extract statistics for all 204 bands
# ---------------------------------------------------------

print("Calculating per-band statistics...")

results = []

for band in range(cube.shape[2]):

    lesion_values = cube[:, :, band][lesion_mask]
    comparison_values = cube[:, :, band][comparison_mask]

    lesion_stats = calculate_statistics(lesion_values)
    comparison_stats = calculate_statistics(comparison_values)

    row = {"band_index_0based": band}

    for key, value in lesion_stats.items():
        row[f"lesion_{key}"] = value

    for key, value in comparison_stats.items():
        row[f"comparison_{key}"] = value

    results.append(row)

df = pd.DataFrame(results)


# ---------------------------------------------------------
# Adjacent-band changes
# ---------------------------------------------------------

for roi in ["lesion", "comparison"]:

    mean_col = f"{roi}_mean"

    df[f"{roi}_adjacent_mean_difference"] = (
        df[mean_col].diff()
    )

    df[f"{roi}_adjacent_absolute_difference"] = (
        df[f"{roi}_adjacent_mean_difference"].abs()
    )


# ---------------------------------------------------------
# Between-ROI differences
# ---------------------------------------------------------

df["mean_difference_lesion_minus_comparison"] = (
    df["lesion_mean"] - df["comparison_mean"]
)

df["median_difference_lesion_minus_comparison"] = (
    df["lesion_median"] - df["comparison_median"]
)

df["lesion_mean_median_gap"] = (
    df["lesion_mean"] - df["lesion_median"]
)

df["comparison_mean_median_gap"] = (
    df["comparison_mean"] - df["comparison_median"]
)


# ---------------------------------------------------------
# Candidate region flags
# These are investigation flags, not automatic exclusions.
# ---------------------------------------------------------

def region_label(band):
    if 0 <= band <= 4:
        return "initial_edge_candidate"
    if 175 <= band <= 202:
        return "upper_nir_candidate"
    if 201 <= band <= 203:
        return "final_edge_candidate"
    if 75 <= band <= 98:
        return "red_absorption_candidate"
    if 115 <= band <= 175:
        return "nir_plateau_candidate"
    return "other"


df["region_flag"] = df["band_index_0based"].apply(region_label)


# ---------------------------------------------------------
# Save detailed CSV
# ---------------------------------------------------------

csv_path = OUTPUT_DIR / "3079_spectral_diagnostics.csv"
df.to_csv(csv_path, index=False)


# ---------------------------------------------------------
# Summarize candidate regions
# ---------------------------------------------------------

def summarize_region(start, end):
    subset = df[
        (df["band_index_0based"] >= start)
        & (df["band_index_0based"] <= end)
    ]

    def finite_values(column):
        return subset[column].dropna().astype(float)

    summary = {
        "start_band": start,
        "end_band": end,
        "band_count": int(len(subset)),
    }

    for roi in ["lesion", "comparison"]:
        summary[f"{roi}_mean_cv"] = (
            float(finite_values(f"{roi}_cv").mean())
            if not finite_values(f"{roi}_cv").empty else None
        )

        summary[f"{roi}_mean_absolute_adjacent_change"] = (
            float(
                finite_values(
                    f"{roi}_adjacent_absolute_difference"
                ).mean()
            )
            if not finite_values(
                f"{roi}_adjacent_absolute_difference"
            ).empty else None
        )

        summary[f"{roi}_mean_skewness"] = (
            float(finite_values(f"{roi}_skewness").mean())
            if not finite_values(f"{roi}_skewness").empty else None
        )

    summary["average_absolute_roi_mean_difference"] = (
        float(
            finite_values(
                "mean_difference_lesion_minus_comparison"
            ).abs().mean()
        )
        if not finite_values(
            "mean_difference_lesion_minus_comparison"
        ).empty else None
    )

    return summary


regions = {
    "initial_edge": (0, 4),
    "red_absorption": (75, 98),
    "nir_plateau": (115, 175),
    "upper_nir": (175, 202),
    "final_edge": (201, 203),
}

region_summaries = {
    name: summarize_region(start, end)
    for name, (start, end) in regions.items()
}


# ---------------------------------------------------------
# Identify largest adjacent-band changes
# ---------------------------------------------------------

largest_changes = {}

for roi in ["lesion", "comparison"]:
    column = f"{roi}_adjacent_absolute_difference"

    largest = (
        df[["band_index_0based", column]]
        .dropna()
        .nlargest(10, column)
    )

    largest_changes[roi] = [
        {
            "band_index_0based": int(row["band_index_0based"]),
            "absolute_adjacent_mean_change": float(row[column]),
        }
        for _, row in largest.iterrows()
    ]


# ---------------------------------------------------------
# Save JSON report
# ---------------------------------------------------------

report = {
    "image_id": 3079,
    "cube_shape": list(cube.shape),
    "spectral_band_count": int(cube.shape[2]),
    "wavelength_calibration": (
        "Unavailable for image 3079. "
        "All results use zero-based band indices."
    ),
    "lesion_roi_pixels": int(lesion_mask.sum()),
    "comparison_roi_pixels": int(comparison_mask.sum()),
    "comparison_roi_note": (
        "Visually non-lesioned comparison stem. "
        "It includes an attached lower-left lateral branch/petiole."
    ),
    "statistics_note": (
        "Percentiles and skewness describe pixel distributions "
        "within each ROI. Pixels are spatially correlated and "
        "must not be treated as independent biological replicates."
    ),
    "region_summaries": region_summaries,
    "largest_adjacent_band_changes": largest_changes,
    "interpretation_warning": (
        "Region flags identify areas for investigation only. "
        "They do not establish disease-specific bands or justify "
        "automatic band removal."
    ),
}

json_path = REPORT_DIR / "3079_spectral_diagnostics_summary.json"

with open(json_path, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=4)


# ---------------------------------------------------------
# Print completion
# ---------------------------------------------------------

print("\nSPECTRAL DIAGNOSTICS COMPLETED")
print("--------------------------------")
print("Cube shape:", cube.shape)
print("Lesion ROI pixels:", int(lesion_mask.sum()))
print("Comparison ROI pixels:", int(comparison_mask.sum()))
print("Bands analysed:", len(df))

print("\nSaved files:")
print(csv_path)
print(json_path)

print("\nCandidate region summaries:")

for name, summary in region_summaries.items():
    print(f"\n{name}:")
    print(summary)
