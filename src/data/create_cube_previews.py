
from pathlib import Path

import numpy as np
from PIL import Image


DATA_DIR = Path("data/raw/tomato_botrytis")
OUTPUT_DIR = Path("outputs/figures")

IMAGE_IDS = ["2973", "3079"]

# Zero-based band indices used in the previous previews.
BAND_INDICES = [69, 52, 18]


def scale_channel(channel):
    """Scale a channel robustly for visualization."""
    low, high = np.nanpercentile(channel, [2, 98])

    if high <= low:
        return np.zeros_like(channel, dtype=np.float32)

    scaled = (channel - low) / (high - low)
    return np.clip(scaled, 0, 1)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for image_id in IMAGE_IDS:
        file_path = DATA_DIR / f"{image_id}.npz"

        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        with np.load(file_path) as data:
            cube = data["arr_0"].astype(np.float32)

        if cube.ndim != 3 or cube.shape[2] <= max(BAND_INDICES):
            print(f"Invalid cube shape for {image_id}: {cube.shape}")
            continue

        print(f"\nImage {image_id}")
        print(f"Cube shape: {cube.shape}")

        channels = [
            scale_channel(cube[:, :, band])
            for band in BAND_INDICES
        ]

        pseudo_rgb = np.stack(channels, axis=-1)

        # Convert to uint8 RGB without resizing or adding margins.
        pseudo_rgb_uint8 = np.round(
            pseudo_rgb * 255
        ).astype(np.uint8)

        output_path = (
            OUTPUT_DIR / f"{image_id}_pseudo_rgb_preview.png"
        )

        Image.fromarray(
            pseudo_rgb_uint8,
            mode="RGB"
        ).save(output_path)

        # Verify the saved image dimensions.
        with Image.open(output_path) as saved:
            print(f"Saved: {output_path}")
            print(f"Preview dimensions: {saved.size}")
            print(f"Preview mode: {saved.mode}")

            assert saved.size == (cube.shape[1], cube.shape[0])
            assert saved.mode == "RGB"


if __name__ == "__main__":
    main()
