
import numpy as np
from compare_calibration_candidate import (
    BASE, NPZ_PATH, load_bil
)

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

processed = np.load(
    NPZ_PATH, allow_pickle=False
)["arr_0"].astype(np.float32)

# Average reference measurements across the 512 samples.
dark_mean = dark.mean(axis=1, keepdims=True)
white_mean = white.mean(axis=1, keepdims=True)

# Broadcast the per-band reference means over image rows and columns.
denominator = white_mean - dark_mean

if np.any(denominator <= 0):
    raise ValueError("Invalid averaged reference values.")

candidate_mean = (raw - dark_mean) / denominator

print("=" * 60)
print("PER-BAND REFERENCE AVERAGING TEST")
print("=" * 60)

print("Candidate shape:", candidate_mean.shape)
print("Processed shape:", processed.shape)

rng = np.random.default_rng(42)
indices = rng.choice(
    candidate_mean.size,
    size=200_000,
    replace=False
)

x = candidate_mean.ravel()[indices]
y = processed.ravel()[indices]

correlation = np.corrcoef(x, y)[0, 1]

print("\nCandidate statistics:")
print("Median:", float(np.median(candidate_mean)))
print("99th percentile:",
      float(np.percentile(candidate_mean, 99)))
print("Maximum:", float(candidate_mean.max()))

print("\nExisting NPZ statistics:")
print("Median:", float(np.median(processed)))
print("99th percentile:",
      float(np.percentile(processed, 99)))
print("Maximum:", float(processed.max()))

print("\nComparison:")
print("Pearson correlation:", float(correlation))
print("Mean absolute difference:",
      float(np.mean(np.abs(x - y))))
print("Median absolute difference:",
      float(np.median(np.abs(x - y))))

print("\nNo source files were modified.")
