
from pathlib import Path
import numpy as np

DATA_DIR = Path("data/raw/tomato_botrytis")

IMAGE_IDS = ["2436", "2973", "3079"]

print("=" * 65)
print("HYPERSPECTRAL CALIBRATION METADATA INSPECTION")
print("=" * 65)

for image_id in IMAGE_IDS:
    file_path = DATA_DIR / f"{image_id}.npz"

    print(f"\nImage: {image_id}")

    with np.load(file_path, allow_pickle=False) as data:
        print("Available NPZ keys:", data.files)

        for key in data.files:
            array = data[key]

            print(
                f"Key: {key}, "
                f"Shape: {array.shape}, "
                f"Dtype: {array.dtype}"
            )

            if array.ndim == 1 and array.size > 10:
                print("First 10 values:", array[:10])
                print("Last 10 values:", array[-10:])

print("\nKnown RGB band references:")
print("Band 70: 598.60 nm")
print("Band 53: 548.55 nm")
print("Band 19: 449.35 nm")

print("\nInspection completed.")
