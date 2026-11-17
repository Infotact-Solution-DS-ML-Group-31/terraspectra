"""
TerraSpectra Hyperspectral Feature Extraction.

Extracts pixel-level spectral statistics across regions of interest:
1. Image 2436: Tomato leaf ROI (wavelength-calibrated, 397.32 - 1003.58 nm).
2. Image 3079 (Whole-stem baseline): Lesion-bearing stem vs comparison stem.
3. Image 3079 (Lesion-level three-region analysis):
   - Visible necrotic lesion (center-right stem).
   - Visually unaffected adjacent stem tissue (same stem).
   - Preserved comparison stem (separate stem).

Scientific notes:
- Image 3079 has NO verified wavelength calibration; analysis strictly uses zero-based band indices.
- Regions are visually annotated; they do not represent laboratory-confirmed histopathological ground truth.
- Visually unaffected tissue is not confirmed healthy tissue.
- Pixels are spatially correlated and cannot be treated as independent biological samples.
- Descriptive observations from single cubes; no predictive or forecasting claims are made.
"""

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUTPUT_DIR = Path("data/processed/features")
REPORT_DIR = Path("data/processed/reports")
FIGURE_DIR = Path("outputs/figures")


def extract_statistics(spectra):
    """
    Calculate per-band descriptive statistics for a 2D collection of pixel spectra (N_pixels, N_bands).
    Handles zero or near-zero means safely for Coefficient of Variation (CV).
    """
    if spectra.size == 0 or len(spectra) == 0:
        raise ValueError("Spectra array is empty; cannot extract statistics.")

    valid_counts = np.sum(np.isfinite(spectra), axis=0)
    mean = np.nanmean(spectra, axis=0)
    median = np.nanmedian(spectra, axis=0)
    std = np.nanstd(spectra, axis=0)
    q25 = np.nanpercentile(spectra, 25, axis=0)
    q75 = np.nanpercentile(spectra, 75, axis=0)

    # Coefficient of Variation (CV = std / mean), handled safely against division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(np.abs(mean) > 1e-7, std / mean, 0.0)
        cv = np.nan_to_num(cv, nan=0.0, posinf=0.0, neginf=0.0)

    return {
        "mean": mean,
        "median": median,
        "std": std,
        "q25": q25,
        "q75": q75,
        "cv": cv,
        "valid_counts": valid_counts
    }


def extract_2436():
    """Extract spectral features from the existing 2436 leaf ROI."""
    input_file = Path("data/processed/cubes/2436_leaf_roi.npz")

    if not input_file.exists():
        raise FileNotFoundError(input_file)

    data = np.load(input_file, allow_pickle=False)

    cube = data["cube"].astype(np.float32)
    wavelengths = data["wavelengths_nm"].astype(np.float32)
    leaf_mask = data["leaf_mask"].astype(bool)

    if cube.ndim != 3:
        raise ValueError("Expected a 3D hyperspectral cube.")

    if cube.shape[2] != len(wavelengths):
        raise ValueError("Cube bands and wavelengths do not match.")

    if cube.shape[:2] != leaf_mask.shape:
        raise ValueError("Leaf mask and cube dimensions differ.")

    spectra = cube[leaf_mask]
    stats = extract_statistics(spectra)

    results = pd.DataFrame({
        "wavelength_nm": wavelengths,
        "mean_reflectance": stats["mean"],
        "median_reflectance": stats["median"],
        "std_reflectance": stats["std"],
        "q25_reflectance": stats["q25"],
        "q75_reflectance": stats["q75"],
        "cv_reflectance": stats["cv"],
        "valid_pixel_count": stats["valid_counts"]
    })

    output_csv = OUTPUT_DIR / "2436_spectral_features.csv"
    results.to_csv(output_csv, index=False)

    plt.figure(figsize=(12, 6))
    plt.plot(wavelengths, stats["mean"], label="Mean reflectance", color="#2E7D32")
    plt.fill_between(
        wavelengths,
        stats["mean"] - stats["std"],
        stats["mean"] + stats["std"],
        alpha=0.2,
        color="#2E7D32",
        label="Mean ± 1 standard deviation"
    )
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title("Tomato Leaf Mean Spectral Profile - Image 2436")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    mean_plot = FIGURE_DIR / "2436_mean_spectral_profile.png"
    plt.savefig(mean_plot, dpi=200)
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.plot(wavelengths, stats["mean"], label="Mean spectrum", color="#2E7D32")
    plt.plot(wavelengths, stats["median"], label="Median spectrum", color="#1565C0", linestyle="--")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title("Mean vs Median Spectral Profile - Image 2436")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    comparison_plot = FIGURE_DIR / "2436_mean_median_spectrum.png"
    plt.savefig(comparison_plot, dpi=200)
    plt.close()

    summary = {
        "image_id": "2436",
        "roi_type": "leaf",
        "leaf_pixels": int(leaf_mask.sum()),
        "spectral_bands": int(len(wavelengths)),
        "wavelength_range_nm": [
            float(wavelengths.min()),
            float(wavelengths.max())
        ],
        "valid_measurements_per_band_min": int(stats["valid_counts"].min()),
        "valid_measurements_per_band_max": int(stats["valid_counts"].max()),
        "mean_reflectance_min": float(np.nanmin(stats["mean"])),
        "mean_reflectance_max": float(np.nanmax(stats["mean"])),
        "mean_reflectance_all_bands": float(np.nanmean(stats["mean"])),
        "nan_values_in_mean_spectrum": int(np.isnan(stats["mean"]).sum())
    }

    summary_file = REPORT_DIR / "2436_spectral_feature_summary.json"
    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\n2436 extraction completed.")
    print("Leaf pixels:", int(leaf_mask.sum()))
    print("Spectral bands:", len(wavelengths))
    print("Wavelength range:", wavelengths.min(), "to", wavelengths.max(), "nm")
    print("Saved:", output_csv)
    print("Saved:", mean_plot)
    print("Saved:", comparison_plot)
    print("Saved:", summary_file)


def extract_3079_whole_stem():
    """Compare spectral features from the two original whole-stem ROIs."""
    cube_file = Path("data/raw/tomato_botrytis/3079.npz")
    annotation_file = Path("data/processed/segmentation/3079_roi_annotations.npz")

    if not cube_file.exists():
        raise FileNotFoundError(cube_file)
    if not annotation_file.exists():
        raise FileNotFoundError(annotation_file)

    cube_data = np.load(cube_file, allow_pickle=False)
    annotation_data = np.load(annotation_file, allow_pickle=False)

    if "arr_0" not in cube_data.files:
        raise KeyError("Expected arr_0 in the 3079 hyperspectral NPZ.")

    cube = cube_data["arr_0"].astype(np.float32)
    class1_mask = annotation_data["lesion_bearing_stem_mask"].astype(bool)
    class2_mask = annotation_data["comparison_stem_mask"].astype(bool)

    if cube.ndim != 3:
        raise ValueError("Expected a 3D hyperspectral cube.")
    if cube.shape[:2] != class1_mask.shape or cube.shape[:2] != class2_mask.shape:
        raise ValueError("Stem masks and cube dimensions differ.")
    if np.any(class1_mask & class2_mask):
        raise ValueError("ROI masks overlap. Resolve overlap before extraction.")
    if class1_mask.sum() == 0 or class2_mask.sum() == 0:
        raise ValueError("One or both ROI masks are empty.")

    class1_spectra = cube[class1_mask]
    class2_spectra = cube[class2_mask]

    class1_stats = extract_statistics(class1_spectra)
    class2_stats = extract_statistics(class2_spectra)

    band_indices = np.arange(cube.shape[2])

    results = pd.DataFrame({
        "band_index_0based": band_indices,
        "lesion_mean": class1_stats["mean"],
        "lesion_median": class1_stats["median"],
        "lesion_std": class1_stats["std"],
        "lesion_valid_pixel_count": class1_stats["valid_counts"],
        "comparison_mean": class2_stats["mean"],
        "comparison_median": class2_stats["median"],
        "comparison_std": class2_stats["std"],
        "comparison_valid_pixel_count": class2_stats["valid_counts"]
    })

    output_csv = OUTPUT_DIR / "3079_stem_roi_spectral_features.csv"
    results.to_csv(output_csv, index=False)

    plt.figure(figsize=(13, 6))
    plt.plot(band_indices, class1_stats["mean"], label="Lesion-bearing stem", linewidth=1.5, color="#D32F2F")
    plt.fill_between(
        band_indices,
        class1_stats["mean"] - class1_stats["std"],
        class1_stats["mean"] + class1_stats["std"],
        alpha=0.15,
        color="#D32F2F"
    )
    plt.plot(band_indices, class2_stats["mean"], label="Visually non-lesioned comparison stem", linewidth=1.5, color="#00897B")
    plt.fill_between(
        band_indices,
        class2_stats["mean"] - class2_stats["std"],
        class2_stats["mean"] + class2_stats["std"],
        alpha=0.15,
        color="#00897B"
    )
    plt.xlabel("Spectral band index (0-based)")
    plt.ylabel("Cube value")
    plt.title("Stem ROI Mean Spectral Comparison - Image 3079")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    mean_plot = FIGURE_DIR / "3079_stem_roi_mean_spectral_profile.png"
    plt.savefig(mean_plot, dpi=200)
    plt.close()

    plt.figure(figsize=(13, 6))
    plt.plot(band_indices, class1_stats["mean"], label="Lesion stem - mean", color="#D32F2F")
    plt.plot(band_indices, class1_stats["median"], label="Lesion stem - median", color="#D32F2F", linestyle="--")
    plt.plot(band_indices, class2_stats["mean"], label="Comparison stem - mean", color="#00897B")
    plt.plot(band_indices, class2_stats["median"], label="Comparison stem - median", color="#00897B", linestyle="--")
    plt.xlabel("Spectral band index (0-based)")
    plt.ylabel("Cube value")
    plt.title("Mean vs Median Stem Spectra - Image 3079")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    comparison_plot = FIGURE_DIR / "3079_stem_roi_mean_median_spectrum.png"
    plt.savefig(comparison_plot, dpi=200)
    plt.close()

    summary = {
        "image_id": "3079",
        "roi_type": "stem",
        "spectral_bands": int(cube.shape[2]),
        "spectral_axis": "zero_based_band_index",
        "wavelength_calibration": "Unavailable for image 3079. No wavelength values assigned.",
        "roi_description": {
            "class_1": "Lesion-bearing stem",
            "class_2": "Visually non-lesioned comparison stem; includes attached lateral branch/petiole."
        },
        "overlap_pixels": int(np.logical_and(class1_mask, class2_mask).sum()),
        "class_1": {
            "pixel_count": int(class1_mask.sum()),
            "valid_measurements_per_band_min": int(class1_stats["valid_counts"].min()),
            "valid_measurements_per_band_max": int(class1_stats["valid_counts"].max()),
            "mean_value_min": float(np.nanmin(class1_stats["mean"])),
            "mean_value_max": float(np.nanmax(class1_stats["mean"]))
        },
        "class_2": {
            "pixel_count": int(class2_mask.sum()),
            "valid_measurements_per_band_min": int(class2_stats["valid_counts"].min()),
            "valid_measurements_per_band_max": int(class2_stats["valid_counts"].max()),
            "mean_value_min": float(np.nanmin(class2_stats["mean"])),
            "mean_value_max": float(np.nanmax(class2_stats["mean"]))
        },
        "interpretation_limitations": [
            "The comparison ROI is visually non-lesioned, not confirmed healthy.",
            "The two ROIs may differ anatomically and in illumination.",
            "Pixel measurements are spatially correlated.",
            "Spectral bands are not assigned verified wavelengths."
        ]
    }

    summary_file = REPORT_DIR / "3079_stem_roi_spectral_summary.json"
    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\n3079 whole-stem extraction completed.")
    print("Cube shape:", cube.shape)
    print("Spectral bands:", cube.shape[2])
    print("Class 1 lesion-bearing stem pixels:", int(class1_mask.sum()))
    print("Class 2 comparison stem pixels:", int(class2_mask.sum()))
    print("Overlap pixels:", int(np.logical_and(class1_mask, class2_mask).sum()))
    print("Wavelength calibration: unavailable; using band indices only.")


def extract_3079_lesion_level():
    """
    Extract and compare spectral features across three distinct regions in image 3079:
    1. Visible necrotic lesion (center-right stem)
    2. Visually unaffected adjacent stem tissue (same stem)
    3. Preserved comparison stem (separate stem)

    Strictly preserves all 204 bands using zero-based band indices.
    """
    cube_file = Path("data/raw/tomato_botrytis/3079.npz")
    annotation_file = Path("data/processed/segmentation/3079_lesion_level_annotations.npz")

    if not cube_file.exists():
        raise FileNotFoundError(f"Missing cube file: {cube_file}")
    if not annotation_file.exists():
        raise FileNotFoundError(f"Missing annotation file: {annotation_file}")

    cube_data = np.load(cube_file, allow_pickle=False)
    ann_data = np.load(annotation_file, allow_pickle=False)

    if "arr_0" not in cube_data.files:
        raise KeyError("Expected arr_0 in 3079 hyperspectral cube.")

    cube = cube_data["arr_0"].astype(np.float32)

    # Load validated masks
    lesion_mask = ann_data["visible_lesion_mask"].astype(bool)
    unaffected_mask = ann_data["adjacent_non_lesioned_stem_mask"].astype(bool)
    comparison_mask = ann_data["comparison_stem_mask"].astype(bool)
    stem_mask = ann_data["lesion_bearing_stem_mask"].astype(bool)

    # Validation checks on inputs
    if cube.ndim != 3:
        raise ValueError(f"Expected 3D hyperspectral cube, got ndim={cube.ndim}")

    num_bands = cube.shape[2]
    if num_bands != 204:
        raise ValueError(f"Expected 204 spectral bands, got {num_bands}")

    spatial_shape = cube.shape[:2]
    for name, mask in [
        ("Lesion", lesion_mask),
        ("Unaffected adjacent stem", unaffected_mask),
        ("Comparison stem", comparison_mask),
        ("Lesion-bearing stem", stem_mask)
    ]:
        if mask.shape != spatial_shape:
            raise ValueError(f"{name} mask shape {mask.shape} does not match cube {spatial_shape}")
        if mask.sum() == 0:
            raise ValueError(f"{name} mask is empty (0 pixels).")

    # Enforce zero overlap between lesion and unaffected masks
    overlap_lesion_unaff = int((lesion_mask & unaffected_mask).sum())
    if overlap_lesion_unaff != 0:
        raise ValueError(f"Lesion and unaffected masks overlap by {overlap_lesion_unaff} pixels.")

    # Extract pixel spectra
    lesion_spectra = cube[lesion_mask]
    unaffected_spectra = cube[unaffected_mask]
    comparison_spectra = cube[comparison_mask]

    # Data quality telemetry
    lesion_nan = int(np.isnan(lesion_spectra).sum())
    lesion_inf = int(np.isinf(lesion_spectra).sum())
    unaff_nan = int(np.isnan(unaffected_spectra).sum())
    unaff_inf = int(np.isinf(unaffected_spectra).sum())
    comp_nan = int(np.isnan(comparison_spectra).sum())
    comp_inf = int(np.isinf(comparison_spectra).sum())

    # Calculate statistics per region
    lesion_stats = extract_statistics(lesion_spectra)
    unaffected_stats = extract_statistics(unaffected_spectra)
    comparison_stats = extract_statistics(comparison_spectra)

    band_indices = np.arange(num_bands)

    # Pairwise mean differences
    diff_lesion_minus_unaffected = lesion_stats["mean"] - unaffected_stats["mean"]
    abs_diff_lesion_vs_unaffected = np.abs(diff_lesion_minus_unaffected)

    diff_lesion_minus_comparison = lesion_stats["mean"] - comparison_stats["mean"]
    abs_diff_lesion_vs_comparison = np.abs(diff_lesion_minus_comparison)

    diff_unaffected_minus_comparison = unaffected_stats["mean"] - comparison_stats["mean"]
    abs_diff_unaffected_vs_comparison = np.abs(diff_unaffected_minus_comparison)

    # Assemble per-band DataFrame
    results = pd.DataFrame({
        "band_index_0based": band_indices,

        # ROI 1: Visible necrotic lesion
        "lesion_mean": lesion_stats["mean"],
        "lesion_median": lesion_stats["median"],
        "lesion_std": lesion_stats["std"],
        "lesion_q25": lesion_stats["q25"],
        "lesion_q75": lesion_stats["q75"],
        "lesion_cv": lesion_stats["cv"],
        "lesion_valid_pixel_count": lesion_stats["valid_counts"],

        # ROI 2: Visually unaffected adjacent stem tissue
        "unaffected_mean": unaffected_stats["mean"],
        "unaffected_median": unaffected_stats["median"],
        "unaffected_std": unaffected_stats["std"],
        "unaffected_q25": unaffected_stats["q25"],
        "unaffected_q75": unaffected_stats["q75"],
        "unaffected_cv": unaffected_stats["cv"],
        "unaffected_valid_pixel_count": unaffected_stats["valid_counts"],

        # ROI 3: Preserved comparison stem
        "comparison_mean": comparison_stats["mean"],
        "comparison_median": comparison_stats["median"],
        "comparison_std": comparison_stats["std"],
        "comparison_q25": comparison_stats["q25"],
        "comparison_q75": comparison_stats["q75"],
        "comparison_cv": comparison_stats["cv"],
        "comparison_valid_pixel_count": comparison_stats["valid_counts"],

        # Pairwise differences
        "diff_mean_lesion_minus_unaffected": diff_lesion_minus_unaffected,
        "abs_diff_mean_lesion_vs_unaffected": abs_diff_lesion_vs_unaffected,
        "diff_mean_lesion_minus_comparison": diff_lesion_minus_comparison,
        "abs_diff_mean_lesion_vs_comparison": abs_diff_lesion_vs_comparison,
        "diff_mean_unaffected_minus_comparison": diff_unaffected_minus_comparison,
        "abs_diff_mean_unaffected_vs_comparison": abs_diff_unaffected_vs_comparison
    })

    output_csv = OUTPUT_DIR / "3079_lesion_level_spectral_features.csv"
    results.to_csv(output_csv, index=False)

    # -------------------------------------------------------------
    # Visualizations
    # -------------------------------------------------------------
    color_lesion = "#D32F2F"       # Deep Red
    color_unaff = "#1976D2"        # Medium Blue
    color_comp = "#00897B"         # Teal

    # 1. Three-region mean spectral profile (with ± 1 std ribbon)
    plt.figure(figsize=(13, 6))
    plt.plot(band_indices, lesion_stats["mean"], label="Visible necrotic lesion (ROI 1)", color=color_lesion, linewidth=1.6)
    plt.fill_between(
        band_indices,
        lesion_stats["mean"] - lesion_stats["std"],
        lesion_stats["mean"] + lesion_stats["std"],
        alpha=0.18,
        color=color_lesion,
        label="Lesion ± 1 std"
    )
    plt.plot(band_indices, unaffected_stats["mean"], label="Visually unaffected adjacent stem (ROI 2)", color=color_unaff, linewidth=1.6)
    plt.fill_between(
        band_indices,
        unaffected_stats["mean"] - unaffected_stats["std"],
        unaffected_stats["mean"] + unaffected_stats["std"],
        alpha=0.18,
        color=color_unaff,
        label="Unaffected ± 1 std"
    )
    plt.plot(band_indices, comparison_stats["mean"], label="Preserved comparison stem (ROI 3)", color=color_comp, linewidth=1.6)
    plt.fill_between(
        band_indices,
        comparison_stats["mean"] - comparison_stats["std"],
        comparison_stats["mean"] + comparison_stats["std"],
        alpha=0.15,
        color=color_comp,
        label="Comparison ± 1 std"
    )
    plt.xlabel("Spectral band index (0-based)")
    plt.ylabel("Cube value (uncalibrated reflectance)")
    plt.title("Image 3079: Three-Region Mean Spectral Profiles (Mean ± 1 SD)")
    plt.legend(loc="upper right", framealpha=0.9)
    plt.grid(alpha=0.25)
    plt.tight_layout()

    mean_fig_path = FIGURE_DIR / "3079_three_region_mean_spectral_profile.png"
    plt.savefig(mean_fig_path, dpi=200)
    plt.close()

    # 2. Three-region median spectral profile (with Q25 - Q75 IQR ribbon)
    plt.figure(figsize=(13, 6))
    plt.plot(band_indices, lesion_stats["median"], label="Visible necrotic lesion (ROI 1) - Median", color=color_lesion, linewidth=1.6)
    plt.fill_between(
        band_indices,
        lesion_stats["q25"],
        lesion_stats["q75"],
        alpha=0.18,
        color=color_lesion,
        label="Lesion IQR (Q25-Q75)"
    )
    plt.plot(band_indices, unaffected_stats["median"], label="Visually unaffected adjacent stem (ROI 2) - Median", color=color_unaff, linewidth=1.6)
    plt.fill_between(
        band_indices,
        unaffected_stats["q25"],
        unaffected_stats["q75"],
        alpha=0.18,
        color=color_unaff,
        label="Unaffected IQR (Q25-Q75)"
    )
    plt.plot(band_indices, comparison_stats["median"], label="Preserved comparison stem (ROI 3) - Median", color=color_comp, linewidth=1.6)
    plt.fill_between(
        band_indices,
        comparison_stats["q25"],
        comparison_stats["q75"],
        alpha=0.15,
        color=color_comp,
        label="Comparison IQR (Q25-Q75)"
    )
    plt.xlabel("Spectral band index (0-based)")
    plt.ylabel("Cube value (uncalibrated reflectance)")
    plt.title("Image 3079: Three-Region Median Spectral Profiles (Median + IQR)")
    plt.legend(loc="upper right", framealpha=0.9)
    plt.grid(alpha=0.25)
    plt.tight_layout()

    median_fig_path = FIGURE_DIR / "3079_three_region_median_spectral_profile.png"
    plt.savefig(median_fig_path, dpi=200)
    plt.close()

    # 3. Variability comparison (Standard Deviation and Coefficient of Variation)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

    ax1.plot(band_indices, lesion_stats["std"], label="Visible necrotic lesion (ROI 1)", color=color_lesion, linewidth=1.5)
    ax1.plot(band_indices, unaffected_stats["std"], label="Visually unaffected adjacent stem (ROI 2)", color=color_unaff, linewidth=1.5)
    ax1.plot(band_indices, comparison_stats["std"], label="Preserved comparison stem (ROI 3)", color=color_comp, linewidth=1.5)
    ax1.set_ylabel("Standard Deviation (SD)")
    ax1.set_title("Image 3079: Spectral Variability Comparison Across Bands")
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.grid(alpha=0.25)

    ax2.plot(band_indices, lesion_stats["cv"], label="Visible necrotic lesion (ROI 1)", color=color_lesion, linewidth=1.5)
    ax2.plot(band_indices, unaffected_stats["cv"], label="Visually unaffected adjacent stem (ROI 2)", color=color_unaff, linewidth=1.5)
    ax2.plot(band_indices, comparison_stats["cv"], label="Preserved comparison stem (ROI 3)", color=color_comp, linewidth=1.5)
    ax2.set_xlabel("Spectral band index (0-based)")
    ax2.set_ylabel("Coefficient of Variation (CV)")
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.grid(alpha=0.25)

    plt.tight_layout()
    variability_fig_path = FIGURE_DIR / "3079_three_region_variability_comparison.png"
    plt.savefig(variability_fig_path, dpi=200)
    plt.close()

    # 4. Pairwise absolute mean-difference plot
    plt.figure(figsize=(13, 6))
    plt.plot(
        band_indices,
        abs_diff_lesion_vs_unaffected,
        label="|Lesion - Unaffected adjacent|",
        color="#C2185B",
        linewidth=1.7
    )
    plt.plot(
        band_indices,
        abs_diff_lesion_vs_comparison,
        label="|Lesion - Comparison stem|",
        color="#7B1FA2",
        linewidth=1.7,
        linestyle="--"
    )
    plt.plot(
        band_indices,
        abs_diff_unaffected_vs_comparison,
        label="|Unaffected adjacent - Comparison stem|",
        color="#388E3C",
        linewidth=1.7,
        linestyle=":"
    )

    max_band_les_unaff = int(np.argmax(abs_diff_lesion_vs_unaffected))
    max_val_les_unaff = float(abs_diff_lesion_vs_unaffected[max_band_les_unaff])
    plt.annotate(
        f"Peak lesion/unaffected divergence\n(Band {max_band_les_unaff}: {max_val_les_unaff:.3f})",
        xy=(max_band_les_unaff, max_val_les_unaff),
        xytext=(max_band_les_unaff - 35, max_val_les_unaff + 0.02),
        arrowprops=dict(facecolor="#C2185B", arrowstyle="->", lw=1.2),
        fontsize=9,
        fontweight="semibold"
    )

    plt.xlabel("Spectral band index (0-based)")
    plt.ylabel("Absolute Difference in Mean Cube Value")
    plt.title("Image 3079: Pairwise Spectral Divergence Between Stem Regions")
    plt.legend(loc="upper right", framealpha=0.9)
    plt.grid(alpha=0.25)
    plt.tight_layout()

    diff_fig_path = FIGURE_DIR / "3079_three_region_pairwise_differences.png"
    plt.savefig(diff_fig_path, dpi=200)
    plt.close()

    # -------------------------------------------------------------
    # Summary JSON Report
    # -------------------------------------------------------------
    top5_les_unaff = [int(b) for b in np.argsort(abs_diff_lesion_vs_unaffected)[::-1][:5]]
    top5_les_comp = [int(b) for b in np.argsort(abs_diff_lesion_vs_comparison)[::-1][:5]]
    top5_unaff_comp = [int(b) for b in np.argsort(abs_diff_unaffected_vs_comparison)[::-1][:5]]

    summary = {
        "image_id": "3079",
        "analysis_type": "three_region_lesion_level_spectral_profile",
        "spatial_dimensions": list(spatial_shape),
        "spectral_bands": int(num_bands),
        "spectral_axis": "zero_based_band_index",
        "wavelength_calibration": "Unavailable for image 3079. No wavelength values assigned.",
        "region_pixel_counts": {
            "visible_necrotic_lesion": int(lesion_mask.sum()),
            "visually_unaffected_adjacent_stem": int(unaffected_mask.sum()),
            "preserved_comparison_stem": int(comparison_mask.sum()),
            "lesion_bearing_stem_total": int(stem_mask.sum()),
            "unannotated_stem_margin": int(stem_mask.sum()) - int(lesion_mask.sum()) - int(unaffected_mask.sum()),
            "overlap_lesion_unaffected": overlap_lesion_unaff
        },
        "data_quality": {
            "visible_necrotic_lesion": {
                "nan_count": lesion_nan,
                "inf_count": lesion_inf,
                "min_value": float(np.nanmin(lesion_spectra)),
                "max_value": float(np.nanmax(lesion_spectra)),
                "total_pixel_measurements": int(lesion_spectra.size),
                "valid_pixel_measurements": int(np.sum(np.isfinite(lesion_spectra)))
            },
            "visually_unaffected_adjacent_stem": {
                "nan_count": unaff_nan,
                "inf_count": unaff_inf,
                "min_value": float(np.nanmin(unaffected_spectra)),
                "max_value": float(np.nanmax(unaffected_spectra)),
                "total_pixel_measurements": int(unaffected_spectra.size),
                "valid_pixel_measurements": int(np.sum(np.isfinite(unaffected_spectra)))
            },
            "preserved_comparison_stem": {
                "nan_count": comp_nan,
                "inf_count": comp_inf,
                "min_value": float(np.nanmin(comparison_spectra)),
                "max_value": float(np.nanmax(comparison_spectra)),
                "total_pixel_measurements": int(comparison_spectra.size),
                "valid_pixel_measurements": int(np.sum(np.isfinite(comparison_spectra)))
            }
        },
        "pairwise_spectral_divergence": {
            "lesion_vs_adjacent_unaffected": {
                "max_abs_diff_band": int(top5_les_unaff[0]),
                "max_abs_diff_value": float(abs_diff_lesion_vs_unaffected[top5_les_unaff[0]]),
                "lesion_mean_at_max_band": float(lesion_stats["mean"][top5_les_unaff[0]]),
                "unaffected_mean_at_max_band": float(unaffected_stats["mean"][top5_les_unaff[0]]),
                "mean_abs_diff_all_bands": float(np.mean(abs_diff_lesion_vs_unaffected)),
                "top_5_divergent_bands": top5_les_unaff
            },
            "lesion_vs_comparison_stem": {
                "max_abs_diff_band": int(top5_les_comp[0]),
                "max_abs_diff_value": float(abs_diff_lesion_vs_comparison[top5_les_comp[0]]),
                "lesion_mean_at_max_band": float(lesion_stats["mean"][top5_les_comp[0]]),
                "comparison_mean_at_max_band": float(comparison_stats["mean"][top5_les_comp[0]]),
                "mean_abs_diff_all_bands": float(np.mean(abs_diff_lesion_vs_comparison)),
                "top_5_divergent_bands": top5_les_comp
            },
            "adjacent_unaffected_vs_comparison_stem": {
                "max_abs_diff_band": int(top5_unaff_comp[0]),
                "max_abs_diff_value": float(abs_diff_unaffected_vs_comparison[top5_unaff_comp[0]]),
                "unaffected_mean_at_max_band": float(unaffected_stats["mean"][top5_unaff_comp[0]]),
                "comparison_mean_at_max_band": float(comparison_stats["mean"][top5_unaff_comp[0]]),
                "mean_abs_diff_all_bands": float(np.mean(abs_diff_unaffected_vs_comparison)),
                "top_5_divergent_bands": top5_unaff_comp
            }
        },
        "scientific_limitations_and_disclaimers": [
            "These are descriptive measurements from a single hyperspectral cube (image 3079).",
            "The visually annotated lesion is necrotic tissue, not laboratory-confirmed pathogen ground truth.",
            "The visually unaffected adjacent stem tissue is not confirmed healthy tissue.",
            "The preserved comparison stem is not confirmed healthy tissue.",
            "Pixel measurements exhibit high spatial correlation and must not be treated as independent biological samples.",
            "No disease-classification accuracy, predictive modeling, or forecasting capability has been demonstrated."
        ]
    }

    summary_file = REPORT_DIR / "3079_lesion_level_spectral_summary.json"
    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\n" + "=" * 70)
    print("3079 THREE-REGION SPECTRAL FEATURE EXTRACTION COMPLETED")
    print("=" * 70)
    print(f"Cube Shape:                                    {cube.shape}")
    print(f"Spectral Bands Preserved:                      {num_bands} (0 to {num_bands - 1})")
    print(f"Visible Necrotic Lesion (ROI 1):               {int(lesion_mask.sum()):,} px (0 NaNs)")
    print(f"Visually Unaffected Adjacent Stem (ROI 2):     {int(unaffected_mask.sum()):,} px (0 NaNs)")
    print(f"Preserved Comparison Stem (ROI 3):             {int(comparison_mask.sum()):,} px (0 NaNs)")
    print(f"Unannotated Stem Margin:                       {int(stem_mask.sum()) - int(lesion_mask.sum()) - int(unaffected_mask.sum()):,} px")
    print(f"Lesion / Unaffected Overlap:                   {overlap_lesion_unaff} px (PASS)")
    print("-" * 70)
    print("Key Spectral Findings:")
    print(f"  - Peak Lesion vs Unaffected divergence:     Band {top5_les_unaff[0]} (|diff| = {abs_diff_lesion_vs_unaffected[top5_les_unaff[0]]:.4f})")
    print(f"  - Top 5 Divergent Bands (Lesion vs Unaff):   {top5_les_unaff}")
    print(f"  - Peak Lesion vs Comparison divergence:     Band {top5_les_comp[0]} (|diff| = {abs_diff_lesion_vs_comparison[top5_les_comp[0]]:.4f})")
    print(f"  - Peak Unaffected vs Comparison divergence: Band {top5_unaff_comp[0]} (|diff| = {abs_diff_unaffected_vs_comparison[top5_unaff_comp[0]]:.4f})")
    print("-" * 70)
    print("Saved Outputs:")
    print(f"  - CSV Table:       {output_csv}")
    print(f"  - Summary JSON:    {summary_file}")
    print(f"  - Mean Plot:       {mean_fig_path}")
    print(f"  - Median Plot:     {median_fig_path}")
    print(f"  - Variability:     {variability_fig_path}")
    print(f"  - Pairwise Diff:   {diff_fig_path}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Extract TerraSpectra hyperspectral ROI features."
    )
    parser.add_argument(
        "--image-id",
        choices=["2436", "3079", "3079-whole-stem", "all"],
        default="3079",
        help="Image extraction to execute (default: 3079 lesion-level)."
    )
    parser.add_argument(
        "--mode",
        choices=["lesion-level", "whole-stem"],
        default="lesion-level",
        help="Extraction mode for image 3079 (default: lesion-level)."
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("TERRASPECTRA SPECTRAL FEATURE EXTRACTION")
    print("=" * 70)

    if args.image_id == "2436":
        extract_2436()
    elif args.image_id == "3079-whole-stem" or (args.image_id == "3079" and args.mode == "whole-stem"):
        extract_3079_whole_stem()
    elif args.image_id == "3079":
        extract_3079_lesion_level()
    elif args.image_id == "all":
        extract_2436()
        extract_3079_whole_stem()
        extract_3079_lesion_level()


if __name__ == "__main__":
    main()
