
import numpy as np
from compare_calibration_candidate import (
    BASE, NPZ_PATH, load_bil
)

# Load original measurements and references.
raw = load_bil(BASE / "2436.raw", BASE / "2436.hdr").astype(np.float32)
dark = load_bil(
    BASE / "DARKREF_2436.raw",
    BASE / "DARKREF_2436.hdr"
).astype(np.float32)

white = load_bil(
    BASE / "WHITEREF_2436.raw",
    BASE / "WHITEREF_2436.hdr"
).astype(np.float32)

processed = np.load(
    NPZ_PATH, allow_pickle=False
)["arr_0"].astype(np.float32)

candidate = (raw - dark) / (white - dark)

# Use identical measurement indices for every orientation.
rng = np.random.default_rng(42)
indices = rng.choice(
    candidate.shape[0] * candidate.shape[1] * candidate.shape[2],
    size=200_000,
    replace=False
)

processed_sample = processed.ravel()[indices]

def correlation_for(array):
    sample = array.ravel()[indices]
    return float(np.corrcoef(sample, processed_sample)[0, 1])

print("=" * 65)
print("SPATIAL ALIGNMENT TEST")
print("=" * 65)

results = []

for rotations in range(4):
    rotated = np.rot90(candidate, k=rotations, axes=(0, 1))
    results.append((
        f"Rotation {rotations * 90} degrees",
        correlation_for(rotated)
    ))

    flipped = np.flip(rotated, axis=1)
    results.append((
        f"Rotation {rotations * 90} + horizontal flip",
        correlation_for(flipped)
    ))

for name, corr in sorted(results, key=lambda x: x[1], reverse=True):
    print(f"{name:40s} Pearson correlation: {corr:.6f}")

print("\nOriginal orientation correlation:",
      correlation_for(candidate))

print("\nNo source files were modified.")
