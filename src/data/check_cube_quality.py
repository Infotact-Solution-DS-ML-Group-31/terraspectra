
from pathlib import Path
import numpy as np

DATA_DIR = Path("data/raw/tomato_botrytis")
IMAGE_IDS = ["2436", "2973", "3079"]

for image_id in IMAGE_IDS:
    path = DATA_DIR / f"{image_id}.npz"

    print("\n" + "=" * 65)
    print(f"QUALITY CHECK: IMAGE {image_id}")
    print("=" * 65)

    with np.load(path, allow_pickle=False) as data:
        cube = data["arr_0"].astype(np.float32)

    print("Shape:", cube.shape)
    print("Data type:", cube.dtype)

    finite_mask = np.isfinite(cube)
    values = cube[finite_mask]

    if values.size == 0:
        print("ERROR: No finite values!")
        continue

    print("Finite values:", values.size)
    print("Non-finite values:", (~finite_mask).sum())
    print("Zero percentage:", round((values == 0).mean() * 100, 4))

    percentiles = [0, 1, 25, 50, 75, 95, 99, 99.9, 100]

    print("\nPercentile distribution:")
    for p in percentiles:
        print(f"{p:>5}%: {np.percentile(values, p):.6f}")

    print("\nExtreme value counts:")
    for threshold in [1, 2, 10, 100, 1000]:
        count = np.sum(values > threshold)
        percentage = count / values.size * 100

        print(
            f"Values > {threshold}: "
            f"{count} ({percentage:.6f}%)"
        )

    # Locate the maximum-value pixel and spectral band.
    safe_cube = np.where(finite_mask, cube, -np.inf)
    max_location = np.unravel_index(
        np.argmax(safe_cube), safe_cube.shape
    )

    print("\nMaximum value location (row, column, band):")
    print(max_location)

    row, column, band = max_location

    print("Maximum value:", cube[row, column, band])

    # Inspect the spectrum at the maximum-value pixel.
    spectrum = cube[row, column, :]

    print("\nSpectrum at maximum-value pixel:")
    print("Minimum:", np.nanmin(spectrum))
    print("Maximum:", np.nanmax(spectrum))
    print("Mean:", np.nanmean(spectrum))

    # Per-band average values.
    band_means = np.nanmean(
        np.where(finite_mask, cube, np.nan),
        axis=(0, 1)
    )

    print("\nPer-band mean:")
    print("Minimum band mean:", np.nanmin(band_means))
    print("Maximum band mean:", np.nanmax(band_means))
    print("Bands with non-finite means:",
          np.sum(~np.isfinite(band_means)))

print("\nQuality checks completed.")
