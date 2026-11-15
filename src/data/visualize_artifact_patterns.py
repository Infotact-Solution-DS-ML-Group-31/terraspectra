from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DATA_DIR = Path("data/raw/tomato_botrytis")
OUTPUT_DIR = Path("outputs/figures")

IMAGE_ID = "2436"
AFFECTED_BANDS = [169, 185, 187, 192, 200, 203]
THRESHOLD = 2.0

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with np.load(DATA_DIR / f"{IMAGE_ID}.npz", allow_pickle=False) as data:
    cube = data["arr_0"].astype(np.float32)

fig, axes = plt.subplots(
    2, len(AFFECTED_BANDS),
    figsize=(18, 7)
)

fig.suptitle(
    "Image 2436: Spectral Artifact Quality Inspection",
    fontsize=15
)

for index, band in enumerate(AFFECTED_BANDS):
    band_data = cube[:, :, band]
    mask = band_data > THRESHOLD

    # Exclude extreme values only for visualization scaling.
    # The original measurements remain unchanged.
    valid_values = band_data[~mask]

    vmin, vmax = np.percentile(valid_values, [1, 99])

    axes[0, index].imshow(
        band_data,
        cmap="gray",
        vmin=vmin,
        vmax=vmax
    )

    axes[0, index].set_title(
        f"Band {band}\n{mask.sum()} extreme pixels"
    )

    axes[1, index].imshow(mask, cmap="gray", vmin=0, vmax=1)
    axes[1, index].set_title("Extreme-value mask")

    axes[0, index].axis("off")
    axes[1, index].axis("off")

axes[0, 0].set_ylabel("Band image", fontsize=10)
axes[1, 0].set_ylabel("Artifact mask", fontsize=10)

plt.tight_layout()

output_path = OUTPUT_DIR / "image_2436_artifact_diagnostic.png"

plt.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Diagnostic image saved to:", output_path)
print("Original dataset was not modified.")