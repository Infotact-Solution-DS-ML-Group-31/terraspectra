
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from scipy import ndimage


DATA = Path("data/raw/tomato_botrytis")
IMAGE_ID = "2436"

NPZ_PATH = DATA / f"{IMAGE_ID}.npz"
PREVIEW_PATH = DATA / "raw_2436" / IMAGE_ID / f"{IMAGE_ID}.png"

OUTPUT_PATH = Path("outputs/figures/2436_rgb_alignment_diagnostic.png")

# Load hyperspectral cube and original RGB preview.
cube = np.load(NPZ_PATH, allow_pickle=False)["arr_0"].astype(np.float32)
preview = np.asarray(Image.open(PREVIEW_PATH).convert("RGB"))

if cube.ndim != 3 or cube.shape[2] < 70:
    raise ValueError(f"Unexpected cube shape: {cube.shape}")

# README documents RGB bands as 70, 53, 19 (1-based).
rgb = cube[:, :, [69, 52, 18]]

# Robust display scaling for visualization only.
rgb_display = np.zeros(rgb.shape, dtype=np.float32)

for channel in range(3):
    band = rgb[:, :, channel]
    valid = np.isfinite(band)

    if not valid.any():
        raise ValueError(f"RGB channel {channel} has no valid values.")

    low, high = np.percentile(band[valid], [1, 99])

    if high > low:
        scaled = np.clip((band - low) / (high - low), 0, 1)
        rgb_display[:, :, channel] = scaled ** (1 / 2.2)

rgb_display = (rgb_display * 255).astype(np.uint8)

# Both images must have the same dimensions for direct comparison.
if preview.shape[:2] != rgb_display.shape[:2]:
    raise ValueError(
        f"Image dimensions differ: preview={preview.shape[:2]}, "
        f"cube RGB={rgb_display.shape[:2]}. "
        "Do not resize automatically; investigate the discrepancy."
    )


def edge_map(image):
    """Create a normalized grayscale edge map."""
    gray = (
        0.299 * image[:, :, 0]
        + 0.587 * image[:, :, 1]
        + 0.114 * image[:, :, 2]
    ).astype(np.float32)

    gray = gray / 255.0

    gx = ndimage.sobel(gray, axis=1)
    gy = ndimage.sobel(gray, axis=0)

    edges = np.hypot(gx, gy)

    low, high = np.percentile(edges, [1, 99])

    if high <= low:
        return np.zeros_like(edges)

    return np.clip((edges - low) / (high - low), 0, 1)


preview_edges = edge_map(preview)
cube_edges = edge_map(rgb_display)


def correlation(a, b):
    a = a.ravel()
    b = b.ravel()

    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0

    return float(np.corrcoef(a, b)[0, 1])


# Test four rotations, with and without horizontal flipping.
results = []

for rotations in range(4):
    rotated = np.rot90(cube_edges, k=rotations)

    for flipped in [False, True]:
        candidate = np.fliplr(rotated) if flipped else rotated

        label = (
            f"Rotation {rotations * 90} degrees"
            + (" + horizontal flip" if flipped else "")
        )

        results.append((label, correlation(preview_edges, candidate)))

results.sort(key=lambda item: item[1], reverse=True)

print("=" * 65)
print("RGB–HYPERSPECTRAL SPATIAL ALIGNMENT DIAGNOSTIC")
print("=" * 65)

print("Original preview dimensions:", preview.shape)
print("Hyperspectral cube shape:", cube.shape)
print("\nOrientation comparison (edge-map correlation):")

for label, score in results:
    print(f"{label:40s} {score:.6f}")

best_label, best_score = results[0]
print("\nBest orientation:", best_label)
print("Best edge correlation:", round(best_score, 6))

# Create a visual edge overlay in the original orientation.
# Red = original preview edges; cyan = cube-derived RGB edges.
overlay = np.zeros((*preview_edges.shape, 3), dtype=np.float32)
overlay[:, :, 0] = preview_edges
overlay[:, :, 1] = cube_edges
overlay[:, :, 2] = cube_edges

fig, axes = plt.subplots(2, 2, figsize=(13, 11))

axes[0, 0].imshow(preview)
axes[0, 0].set_title("Original RGB preview")

axes[0, 1].imshow(rgb_display)
axes[0, 1].set_title("RGB reconstructed from NPZ bands")

axes[1, 0].imshow(overlay)
axes[1, 0].set_title("Edge overlay: red=preview, cyan=NPZ")

axes[1, 1].imshow(preview_edges, cmap="gray")
axes[1, 1].imshow(cube_edges, cmap="magma", alpha=0.45)
axes[1, 1].set_title("Edge comparison")

for ax in axes.ravel():
    ax.axis("off")

plt.tight_layout()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight")
plt.close()

print("\nDiagnostic saved to:", OUTPUT_PATH)
print("No source files were modified.")
