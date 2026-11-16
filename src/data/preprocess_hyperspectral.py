
from pathlib import Path
import json
import csv

import numpy as np
import pandas as pd


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

IMAGE_ID = "2436"

DATA_DIR = Path("data/raw/tomato_botrytis")
METADATA_DIR = Path("data/processed/metadata")
MASK_DIR = Path("data/processed/quality_masks")

OUTPUT_DIR = Path("data/processed/cubes")
REPORT_DIR = Path("data/processed/reports")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LOAD AND VALIDATE INPUTS
# --------------------------------------------------

def load_cube(image_id):
    path = DATA_DIR / f"{image_id}.npz"

    if not path.exists():
        raise FileNotFoundError(path)

    with np.load(path, allow_pickle=False) as data:
        if "arr_0" not in data:
            raise KeyError("arr_0 is missing from the input cube.")

        cube = data["arr_0"].astype(np.float32)

    if cube.ndim != 3:
        raise ValueError(f"Expected a 3D cube, got {cube.shape}")

    if cube.shape[2] != 204:
        raise ValueError(
            f"Expected 204 spectral bands, got {cube.shape[2]}"
        )

    return cube


def load_wavelengths():
    path = METADATA_DIR / "wavelengths_2436.csv"

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = {"band_index", "wavelength_nm"}

    if not required.issubset(df.columns):
        raise ValueError("Wavelength CSV has unexpected columns.")

    if len(df) != 204:
        raise ValueError(
            f"Expected 204 wavelengths, found {len(df)}"
        )

    expected_indices = np.arange(204)

    if not np.array_equal(
        df["band_index"].to_numpy(),
        expected_indices
    ):
        raise ValueError("Band indices are incorrect or out of order.")

    wavelengths = df["wavelength_nm"].to_numpy(dtype=np.float32)

    if not np.isfinite(wavelengths).all():
        raise ValueError("Non-finite wavelength values detected.")

    if not np.all(np.diff(wavelengths) > 0):
        raise ValueError("Wavelengths are not strictly increasing.")

    return wavelengths


def load_quality_mask(shape, cube):
    path = MASK_DIR / f"{IMAGE_ID}_quality_mask.npz"

    nonfinite_mask = ~np.isfinite(cube)

    if not path.exists():
        print("WARNING: No existing quality mask found.")
        print("Only non-finite measurements will be flagged.")

        return nonfinite_mask, "incomplete_nonfinite_only"

    with np.load(path, allow_pickle=False) as data:
        if "quality_mask" not in data:
            raise KeyError("quality_mask missing from mask file.")

        saved_mask = data["quality_mask"].astype(bool)

    if saved_mask.shape != shape:
        raise ValueError(
            f"Mask shape {saved_mask.shape} "
            f"does not match cube shape {shape}"
        )

    combined_mask = saved_mask | nonfinite_mask

    return combined_mask, "existing_mask_applied"


# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------

def preprocess():

    print("=" * 60)
    print("TERRASPECTRA PREPROCESSING PIPELINE")
    print("=" * 60)

    print("\nLoading image:", IMAGE_ID)

    cube = load_cube(IMAGE_ID)
    wavelengths = load_wavelengths()

    print("Cube shape:", cube.shape)
    print("Cube dtype:", cube.dtype)
    print("Wavelength count:", len(wavelengths))
    print(
        "Wavelength range:",
        wavelengths.min(),
        "to",
        wavelengths.max(),
        "nm"
    )

    quality_mask, mask_status = load_quality_mask(
        cube.shape,
        cube
    )

    # Do not modify the original cube.
    processed_cube = cube.copy()

    # Replace flagged measurements only in the processed copy.
    processed_cube[quality_mask] = np.nan

    # --------------------------------------------------
    # SAVE PROCESSED CUBE
    # --------------------------------------------------

    cube_path = OUTPUT_DIR / f"{IMAGE_ID}_preprocessed.npz"

    np.savez_compressed(
        cube_path,
        cube=processed_cube,
        wavelengths_nm=wavelengths,
        image_id=IMAGE_ID
    )

    # Save mask independently.
    mask_path = OUTPUT_DIR / f"{IMAGE_ID}_preprocessed_mask.npy"

    np.save(mask_path, quality_mask)

    # --------------------------------------------------
    # PER-BAND QUALITY REPORT
    # --------------------------------------------------

    band_report_path = (
        REPORT_DIR / f"{IMAGE_ID}_preprocessing_band_report.csv"
    )

    with open(band_report_path, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "band_index",
            "wavelength_nm",
            "total_pixels",
            "flagged_pixels",
            "valid_pixels",
            "flagged_percentage",
            "valid_mean",
            "valid_std"
        ])

        for band in range(cube.shape[2]):

            band_mask = quality_mask[:, :, band]
            valid_values = processed_cube[:, :, band]
            valid_values = valid_values[np.isfinite(valid_values)]

            total_pixels = cube.shape[0] * cube.shape[1]
            flagged = int(band_mask.sum())
            valid = total_pixels - flagged

            if len(valid_values) > 0:
                mean_value = float(valid_values.mean())
                std_value = float(valid_values.std())
            else:
                mean_value = None
                std_value = None

            writer.writerow([
                band,
                float(wavelengths[band]),
                total_pixels,
                flagged,
                valid,
                round(flagged / total_pixels * 100, 6),
                mean_value,
                std_value
            ])

    # --------------------------------------------------
    # PROCESSING SUMMARY
    # --------------------------------------------------

    total_measurements = int(cube.size)
    flagged_measurements = int(quality_mask.sum())
    valid_measurements = total_measurements - flagged_measurements

    summary = {
        "project": "TerraSpectra",
        "image_id": IMAGE_ID,
        "input_file": str(DATA_DIR / f"{IMAGE_ID}.npz"),
        "output_file": str(cube_path),
        "cube_shape": list(cube.shape),
        "input_dtype": "float32",
        "spectral_bands": len(wavelengths),
        "wavelength_min_nm": float(wavelengths.min()),
        "wavelength_max_nm": float(wavelengths.max()),
        "quality_mask_status": mask_status,
        "total_measurements": total_measurements,
        "flagged_measurements": flagged_measurements,
        "valid_measurements": valid_measurements,
        "flagged_percentage": round(
            flagged_measurements / total_measurements * 100,
            6
        ),
        "nonfinite_measurements_after_processing": int(
            np.isnan(processed_cube).sum()
        ),
        "normalization_applied": False,
        "additional_calibration_applied": False,
        "raw_data_modified": False
    }

    summary_path = (
        REPORT_DIR / f"{IMAGE_ID}_preprocessing_summary.json"
    )

    with open(summary_path, "w") as file:
        json.dump(summary, file, indent=4)

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print("\nPREPROCESSING COMPLETED")
    print("-" * 60)

    print("Total measurements:", total_measurements)
    print("Flagged measurements:", flagged_measurements)
    print("Valid measurements:", valid_measurements)

    print(
        "Flagged percentage:",
        summary["flagged_percentage"],
        "%"
    )

    print("Mask status:", mask_status)

    print("\nSaved outputs:")
    print(cube_path)
    print(mask_path)
    print(band_report_path)
    print(summary_path)

    print("\nOriginal raw cube remains unchanged.")


if __name__ == "__main__":
    preprocess()
