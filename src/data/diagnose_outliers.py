
from pathlib import Path
import numpy as np

DATA_DIR = Path("data/raw/tomato_botrytis")
IMAGE_ID = "2436"

file_path = DATA_DIR / f"{IMAGE_ID}.npz"

with np.load(file_path, allow_pickle=False) as data:
    cube = data["arr_0"].astype(np.float32)

print("=" * 65)
print("EXTREME VALUE DIAGNOSTICS")
print("=" * 65)

# Identify values above 2.
mask = cube > 2

coordinates = np.argwhere(mask)

print("\nTotal values above 2:", len(coordinates))

if len(coordinates) == 0:
    print("No extreme values found.")
    raise SystemExit

# Distribution across spectral bands.
band_counts = mask.sum(axis=(0, 1))

print("\nBands containing extreme values:")

for band in np.where(band_counts > 0)[0]:
    print(
        f"Band {band}: {band_counts[band]} extreme values"
    )

# Distribution across image rows and columns.
row_counts = mask.sum(axis=(1, 2))
column_counts = mask.sum(axis=(0, 2))

print("\nRows with most extreme values:")

for row in np.argsort(row_counts)[-10:][::-1]:
    if row_counts[row] > 0:
        print(f"Row {row}: {row_counts[row]}")

print("\nColumns with most extreme values:")

for column in np.argsort(column_counts)[-10:][::-1]:
    if column_counts[column] > 0:
        print(f"Column {column}: {column_counts[column]}")

# Inspect the first 20 extreme coordinates.
print("\nFirst 20 extreme-value coordinates:")
print("(row, column, band, value)")

for row, column, band in coordinates[:20]:
    print(
        row,
        column,
        band,
        float(cube[row, column, band])
    )

# Examine per-band maximum and median.
print("\nBands with highest maximum values:")

band_max = cube.max(axis=(0, 1))

for band in np.argsort(band_max)[-10:][::-1]:
    print(
        f"Band {band}: maximum={band_max[band]:.4f}, "
        f"extreme_count={band_counts[band]}"
    )

print("\nDiagnostics completed.")
