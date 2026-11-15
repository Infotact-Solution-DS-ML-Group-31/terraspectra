from pathlib import Path
import numpy as np

DATA_DIR = Path("data/raw/tomato_botrytis")
IMAGE_IDS = ["2436", "2973", "3079"]

THRESHOLD = 2.0

print("=" * 70)
print("CROSS-IMAGE ARTIFACT COMPARISON")
print("=" * 70)

for image_id in IMAGE_IDS:
    file_path = DATA_DIR / f"{image_id}.npz"

    with np.load(file_path, allow_pickle=False) as data:
        cube = data["arr_0"].astype(np.float32)

    mask = cube > THRESHOLD

    total_extreme = int(mask.sum())
    band_counts = mask.sum(axis=(0, 1))
    column_counts = mask.sum(axis=(0, 2))

    print(f"\nIMAGE: {image_id}")
    print("-" * 50)
    print("Cube shape:", cube.shape)
    print("Total values above", THRESHOLD, ":", total_extreme)

    affected_bands = np.where(band_counts > 0)[0]
    affected_columns = np.where(column_counts > 0)[0]

    print("Number of affected bands:", len(affected_bands))
    print("Number of affected columns:", len(affected_columns))

    if total_extreme > 0:
        print("\nAffected bands and counts:")

        for band in affected_bands:
            print(f"Band {band}: {band_counts[band]}")

        print("\nAffected columns and counts:")

        for column in affected_columns:
            print(f"Column {column}: {column_counts[column]}")

    else:
        print("No values above threshold found.")

print("\nCross-image comparison completed.")