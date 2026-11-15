from pathlib import Path
import numpy as np

DATA_DIR = Path("data/raw/tomato_botrytis")
IMAGE_ID = "2436"

with np.load(DATA_DIR / f"{IMAGE_ID}.npz", allow_pickle=False) as data:
    cube = data["arr_0"].astype(np.float32)

# Each tuple is: (column, spectral band)
affected_pairs = [
    (96, 203),
    (220, 169),
    (222, 192),
    (16, 200),
    (49, 185),
]

print("=" * 70)
print("SPATIAL ARTIFACT PATTERN INSPECTION")
print("=" * 70)

for column, band in affected_pairs:
    values = cube[:, column, band]
    bad_rows = np.where(values > 2)[0]

    print(f"\nColumn {column}, Band {band}")
    print("-" * 45)

    print("Affected rows:", len(bad_rows), "out of", cube.shape[0])

    if len(bad_rows) > 0:
        print("First affected row:", bad_rows[0])
        print("Last affected row:", bad_rows[-1])
        print("Unique extreme values:", np.unique(values[values > 2]))

    # Compare the affected column with its immediate neighbors.
    print("\nNeighboring column statistics:")

    for col in range(max(0, column - 1), min(cube.shape[1], column + 2)):
        neighbor_values = cube[:, col, band]

        print(
            f"Column {col}: "
            f"min={np.min(neighbor_values):.4f}, "
            f"median={np.median(neighbor_values):.4f}, "
            f"max={np.max(neighbor_values):.4f}, "
            f"values > 2={np.sum(neighbor_values > 2)}"
        )

    print("\nFirst 12 values down the affected column:")
    print(values[:12])

print("\nInspection completed.")