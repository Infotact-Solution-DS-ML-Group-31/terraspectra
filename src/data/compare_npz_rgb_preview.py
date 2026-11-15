
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

DATA = Path("data/raw/tomato_botrytis")
IMAGE_ID = "2436"

npz_path = DATA / f"{IMAGE_ID}.npz"
preview_path = (
    DATA / "raw_2436" / IMAGE_ID / f"{IMAGE_ID}.png"
)

cube = np.load(npz_path, allow_pickle=False)["arr_0"]
preview = Image.open(preview_path).convert("RGB")

# README uses these 1-based ENVI band numbers.
# NumPy indexing is 0-based.
rgb = cube[:, :, [69, 52, 18]].astype(np.float32)

# Robust display scaling for visual comparison only.
# This does not modify the source cube.
rgb_display = np.zeros_like(rgb)

for channel in range(3):
    band = rgb[:, :, channel]
    low, high = np.percentile(band, [1, 99])

    if high > low:
        scaled = np.clip((band - low) / (high - low), 0, 1)
        rgb_display[:, :, channel] = scaled ** (1 / 2.2)

rgb_display = (rgb_display * 255).astype(np.uint8)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].imshow(preview)
axes[0].set_title("Original RGB preview")
axes[0].axis("off")

axes[1].imshow(rgb_display)
axes[1].set_title("RGB generated from calibrated NPZ")
axes[1].axis("off")

plt.tight_layout()

output = Path("outputs/figures/npz_rgb_preview_comparison.png")
output.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output, dpi=200, bbox_inches="tight")
plt.close()

print("Original preview size:", preview.size)
print("NPZ cube shape:", cube.shape)
print("Comparison saved:", output)
