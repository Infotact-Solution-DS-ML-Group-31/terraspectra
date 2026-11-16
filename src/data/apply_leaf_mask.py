
from pathlib import Path
import json
import numpy as np

IMAGE_ID = "2436"

CUBE_PATH = Path(
    f"data/processed/cubes/{IMAGE_ID}_preprocessed.npz"
)

QUALITY_MASK_PATH = Path(
    f"data/processed/cubes/{IMAGE_ID}_preprocessed_mask.npy"
)

LEAF_MASK_PATH = Path(
    f"data/processed/segmentation/{IMAGE_ID}_leaf_mask_exg_candidate.npy"
)

OUTPUT_DIR = Path("data/processed/cubes")
REPORT_DIR = Path("data/processed/reports")

OUTPUT_PATH = OUTPUT_DIR / f"{IMAGE_ID}_leaf_roi.npz"
REPORT_PATH = REPORT_DIR / f"{IMAGE_ID}_leaf_roi_summary.json"


def main():
    print("=" * 60)
    print("TERRASPECTRA LEAF ROI MASK APPLICATION")
    print("=" * 60)

    for path in [CUBE_PATH, QUALITY_MASK_PATH, LEAF_MASK_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file missing: {path}")

    # Load preprocessed hyperspectral data.
    with np.load(CUBE_PATH, allow_pickle=False) as data:
        cube = data["cube"].astype(np.float32)
        wavelengths = data["wavelengths_nm"].astype(np.float32)
        image_id = str(data["image_id"].item())

    # Load existing quality flags and candidate leaf mask.
    quality_mask = np.load(QUALITY_MASK_PATH).astype(bool)
    leaf_mask = np.load(LEAF_MASK_PATH).astype(bool)

    if image_id != IMAGE_ID:
        raise ValueError(f"Unexpected image ID: {image_id}")

    if cube.ndim != 3:
        raise ValueError(f"Expected 3D cube, got {cube.shape}")

    if leaf_mask.shape != cube.shape[:2]:
        raise ValueError(
            f"Leaf mask shape {leaf_mask.shape} "
            f"does not match cube spatial shape {cube.shape[:2]}"
        )

    if quality_mask.shape != cube.shape:
        raise ValueError(
            f"Quality mask shape {quality_mask.shape} "
            f"does not match cube shape {cube.shape}"
        )

    if wavelengths.size != cube.shape[2]:
        raise ValueError("Wavelength count does not match spectral bands.")

    if not leaf_mask.any():
        raise ValueError("Leaf mask is empty.")

    # Keep existing quality flags and exclude all pixels outside the ROI.
    outside_leaf_mask = ~leaf_mask[:, :, None]
    combined_invalid_mask = quality_mask | outside_leaf_mask

    cube[combined_invalid_mask] = np.nan

    leaf_pixels = int(leaf_mask.sum())
    total_pixels = int(leaf_mask.size)
    total_roi_measurements = leaf_pixels * cube.shape[2]

    valid_roi_measurements = int(
        np.isfinite(cube[leaf_mask]).sum()
    )

    flagged_inside_roi = int(
        quality_mask[leaf_mask].sum()
    )

    outside_pixels = total_pixels - leaf_pixels

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        OUTPUT_PATH,
        cube=cube,
        wavelengths_nm=wavelengths,
        image_id=np.array(IMAGE_ID),
        leaf_mask=leaf_mask,
        quality_mask=quality_mask,
        combined_invalid_mask=combined_invalid_mask
    )

    report = {
        "image_id": IMAGE_ID,
        "cube_shape": list(cube.shape),
        "leaf_pixels": leaf_pixels,
        "total_spatial_pixels": total_pixels,
        "leaf_area_percentage": round(
            100 * leaf_pixels / total_pixels, 4
        ),
        "pixels_outside_leaf_roi": outside_pixels,
        "spectral_bands": int(cube.shape[2]),
        "total_measurements_inside_roi": total_roi_measurements,
        "valid_measurements_inside_roi": valid_roi_measurements,
        "quality_flagged_measurements_inside_roi": flagged_inside_roi,
        "invalid_measurements_inside_roi": (
            total_roi_measurements - valid_roi_measurements
        ),
        "wavelength_range_nm": [
            float(wavelengths.min()),
            float(wavelengths.max())
        ],
        "outside_roi_handling": "NaN",
        "original_preprocessed_cube_modified": False
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nProcessing completed.")
    print("Cube shape:", cube.shape)
    print("Leaf pixels:", leaf_pixels)
    print("Leaf area:", report["leaf_area_percentage"], "%")
    print("Valid ROI measurements:", valid_roi_measurements)
    print("Quality-flagged ROI measurements:", flagged_inside_roi)
    print("\nSaved:")
    print(OUTPUT_PATH)
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
