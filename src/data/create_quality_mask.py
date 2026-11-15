from pathlib import Path
import numpy as np
import csv

DATA_DIR = Path("data/raw/tomato_botrytis")
OUTPUT_DIR = Path("data/processed/quality_masks")

IMAGE_ID = "2436"
EXTREME_THRESHOLD = 2.0

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

file_path = DATA_DIR / f"{IMAGE_ID}.npz"

with np.load(file_path, allow_pickle=False) as data:
    cube = data["arr_0"].astype(np.float32)

# Flag non-finite and extreme measurements.
nonfinite_mask = ~np.isfinite(cube)
extreme_mask = np.isfinite(cube) & (cube > EXTREME_THRESHOLD)

quality_mask = nonfinite_mask | extreme_mask

# Save the mask separately. The raw cube remains untouched.
mask_path = OUTPUT_DIR / f"{IMAGE_ID}_quality_mask.npz"

np.savez_compressed(
    mask_path,
    quality_mask=quality_mask,
    nonfinite_mask=nonfinite_mask,
    extreme_mask=extreme_mask,
    threshold=EXTREME_THRESHOLD,
    image_id=IMAGE_ID
)

# Create a per-band quality report.
report_path = OUTPUT_DIR / f"{IMAGE_ID}_band_quality_report.csv"

with open(report_path, "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "band",
        "total_pixels",
        "extreme_pixels",
        "nonfinite_pixels",
        "flagged_pixels",
        "flagged_percentage"
    ])

    for band in range(cube.shape[2]):
        extreme_count = int(extreme_mask[:, :, band].sum())
        nonfinite_count = int(nonfinite_mask[:, :, band].sum())
        flagged_count = int(quality_mask[:, :, band].sum())

        percentage = (
            flagged_count / (cube.shape[0] * cube.shape[1])
        ) * 100

        writer.writerow([
            band,
            cube.shape[0] * cube.shape[1],
            extreme_count,
            nonfinite_count,
            flagged_count,
            round(percentage, 6)
        ])

print("=" * 60)
print("QUALITY MASK CREATED")
print("=" * 60)

print("Image:", IMAGE_ID)
print("Cube shape:", cube.shape)
print("Total measurements:", cube.size)
print("Extreme measurements:", int(extreme_mask.sum()))
print("Non-finite measurements:", int(nonfinite_mask.sum()))
print("Total flagged measurements:", int(quality_mask.sum()))
print(
    "Flagged percentage:",
    round(quality_mask.mean() * 100, 6), "%"
)

print("\nSaved files:")
print(mask_path)
print(report_path)

print("\nOriginal raw dataset was not modified.")