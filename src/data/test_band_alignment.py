
import numpy as np
from compare_calibration_candidate import (
    BASE, NPZ_PATH, load_bil
)

# Load raw cube and reference measurements.
raw = load_bil(
    BASE / "2436.raw", BASE / "2436.hdr"
).astype(np.float32)

dark = load_bil(
    BASE / "DARKREF_2436.raw",
    BASE / "DARKREF_2436.hdr"
).astype(np.float32)

white = load_bil(
    BASE / "WHITEREF_2436.raw",
    BASE / "WHITEREF_2436.hdr"
).astype(np.float32)

candidate = (raw - dark) / (white - dark)

processed = np.load(
    NPZ_PATH, allow_pickle=False
)["arr_0"].astype(np.float32)

# Flatten only the spatial dimensions.
candidate = candidate.reshape(-1, candidate.shape[-1])
processed = processed.reshape(-1, processed.shape[-1])

# Use identical spatial pixel locations for both cubes.
rng = np.random.default_rng(42)
indices = rng.choice(
    candidate.shape[0],
    size=30000,
    replace=False
)

x = candidate[indices]
y = processed[indices]

# Standardize each band independently.
x_std = x.std(axis=0)
y_std = y.std(axis=0)

valid_x = x_std > 1e-8
valid_y = y_std > 1e-8

x = (x - x.mean(axis=0)) / np.where(valid_x, x_std, 1)
y = (y - y.mean(axis=0)) / np.where(valid_y, y_std, 1)

# Each matrix entry is the correlation between one candidate
# band and one processed NPZ band.
correlations = (x.T @ y) / len(indices)

print("=" * 70)
print("SPECTRAL BAND ALIGNMENT TEST")
print("=" * 70)

print("Candidate bands:", correlations.shape[0])
print("Processed bands:", correlations.shape[1])
print("Same-index mean correlation:",
      float(np.mean(np.diag(correlations))))

best_indices = np.argmax(correlations, axis=1)
best_values = np.max(correlations, axis=1)

print("\nBEST MATCHES FOR SELECTED CANDIDATE BANDS")
print("-" * 70)

for band in [0, 1, 10, 18, 30, 50, 70, 100, 150, 180, 203]:
    print(
        f"Candidate band {band:3d} -> "
        f"NPZ band {best_indices[band]:3d} | "
        f"correlation {best_values[band]:.4f}"
    )

print("\nOVERALL MATCH QUALITY")
print("-" * 70)
print("Mean best correlation:",
      float(np.mean(best_values)))
print("Median best correlation:",
      float(np.median(best_values)))
print("Bands with best correlation > 0.8:",
      int(np.sum(best_values > 0.8)))
print("Bands with best correlation > 0.5:",
      int(np.sum(best_values > 0.5)))

print("\nTOP MATCHES FOR FIRST 10 CANDIDATE BANDS")
print("-" * 70)

for band in range(10):
    top = np.argsort(correlations[band])[-3:][::-1]
    matches = [
        (int(index), round(float(correlations[band, index]), 4))
        for index in top
    ]
    print(f"Candidate band {band}: {matches}")

print("\nNo source files were modified.")
