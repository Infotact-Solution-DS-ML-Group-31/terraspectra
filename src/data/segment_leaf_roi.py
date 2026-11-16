
from pathlib import Path
import json

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy import ndimage


IMAGE_ID = "2436"

RGB_FILE = Path(
    "data/raw/tomato_botrytis/raw_2436/2436/2436.png"
)

OUTPUT_DIR = Path("data/processed/segmentation")
FIGURE_DIR = Path("outputs/figures")

MIN_COMPONENT_AREA = 500
COMPONENTS_TO_KEEP = 2
HISTOGRAM_BINS = 256


def otsu_threshold(values, bins=256):
    values = values[np.isfinite(values)]

    if values.size == 0:
        raise ValueError("No valid ExG values found.")

    low = float(values.min())
    high = float(values.max())

    if low == high:
        raise ValueError("ExG values have no variation.")

    counts, edges = np.histogram(
        values,
        bins=bins,
        range=(low, high)
    )

    centers = (edges[:-1] + edges[1:]) / 2
    probabilities = counts.astype(np.float64)
    probabilities /= probabilities.sum()

    cumulative_probability = np.cumsum(probabilities)
    cumulative_mean = np.cumsum(probabilities * centers)

    total_mean = cumulative_mean[-1]

    denominator = (
        cumulative_probability *
        (1.0 - cumulative_probability)
    )

    numerator = (
        total_mean * cumulative_probability -
        cumulative_mean
    ) ** 2

    variance = np.zeros_like(numerator)
    valid = denominator > 0

    variance[valid] = numerator[valid] / denominator[valid]
    variance[-1] = 0

    return float(centers[np.argmax(variance)])


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TERRASPECTRA EXCESS GREEN SEGMENTATION")
    print("=" * 60)

    if not RGB_FILE.exists():
        raise FileNotFoundError(
            f"RGB preview not found: {RGB_FILE}"
        )

    # Load original RGB preview.
    rgb = np.asarray(
        Image.open(RGB_FILE).convert("RGB"),
        dtype=np.float32
    ) / 255.0

    if rgb.shape[:2] != (512, 512):
        raise ValueError(
            f"Unexpected RGB dimensions: {rgb.shape}"
        )

    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]

    print("\nRGB image shape:", rgb.shape)

    # Excess Green Index.
    exg = (2.0 * green) - red - blue

    threshold = otsu_threshold(
        exg.ravel(),
        bins=HISTOGRAM_BINS
    )

    print("Otsu ExG threshold:", threshold)

    # Initial binary mask.
    initial_mask = exg > threshold

    # Remove very small isolated components.
    labels = np.zeros(initial_mask.shape, dtype=np.int32)
    component_count = ndimage.label(initial_mask, output=labels)

    component_sizes = np.bincount(labels.ravel())
    component_sizes[0] = 0

    valid_components = np.where(
        component_sizes >= MIN_COMPONENT_AREA
    )[0]

    valid_components = valid_components[
        valid_components != 0
    ]

    largest_components = sorted(
        valid_components,
        key=lambda label: component_sizes[label],
        reverse=True
    )[:COMPONENTS_TO_KEEP]

    candidate_mask = np.isin(
        labels,
        largest_components
    )

    # Fill enclosed regions, including dark internal lesion areas.
    ndimage.binary_fill_holes(
        candidate_mask,
        output=candidate_mask
    )

    leaf_pixels = int(candidate_mask.sum())
    total_pixels = int(labels.size)

    print("\nConnected components detected:", component_count)
    print("Components retained:", len(largest_components))
    print("Candidate leaf pixels:", leaf_pixels)
    print("Total image pixels:", total_pixels)
    print(
        "Candidate area percentage:",
        round(100.0 * leaf_pixels / total_pixels, 4)
    )

    # Save candidate mask.
    mask_path = (
        OUTPUT_DIR /
        f"{IMAGE_ID}_leaf_mask_exg_candidate.npy"
    )

    np.save(mask_path, candidate_mask)

    # Save summary.
    summary = {
        "image_id": IMAGE_ID,
        "source_rgb": str(RGB_FILE),
        "image_shape": list(rgb.shape),
        "method": "Excess Green with Otsu threshold",
        "exg_formula": "2G - R - B",
        "otsu_threshold": threshold,
        "minimum_component_area": MIN_COMPONENT_AREA,
        "components_retained": len(largest_components),
        "candidate_leaf_pixels": leaf_pixels,
        "total_pixels": total_pixels,
        "candidate_leaf_percentage": (
            100.0 * leaf_pixels / total_pixels
        ),
        "mask_status": "candidate_requires_visual_and_alignment_validation",
        "hyperspectral_alignment_verified": False,
        "raw_data_modified": False
    }

    summary_path = (
        OUTPUT_DIR /
        f"{IMAGE_ID}_exg_segmentation_summary.json"
    )

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    # Diagnostic visualization.
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("Original RGB Preview")
    axes[0, 0].axis("off")

    exg_plot = axes[0, 1].imshow(exg, cmap="viridis")
    axes[0, 1].set_title("Excess Green Index")
    axes[0, 1].axis("off")
    fig.colorbar(exg_plot, ax=axes[0, 1], fraction=0.046)

    axes[1, 0].hist(
        exg.ravel(),
        bins=HISTOGRAM_BINS
    )
    axes[1, 0].axvline(
        threshold,
        linestyle="--",
        linewidth=2,
        label=f"Threshold = {threshold:.5f}"
    )
    axes[1, 0].set_title("ExG Distribution")
    axes[1, 0].set_xlabel("Excess Green")
    axes[1, 0].set_ylabel("Pixel count")
    axes[1, 0].legend()

    axes[1, 1].imshow(rgb)
    axes[1, 1].imshow(
        np.ma.masked_where(
            ~candidate_mask,
            candidate_mask
        ),
        cmap="autumn",
        alpha=0.45
    )
    axes[1, 1].set_title("ExG Candidate Mask Overlay")
    axes[1, 1].axis("off")

    fig.suptitle(
        f"TerraSpectra - Image {IMAGE_ID} ExG Segmentation",
        fontsize=15
    )

    plt.tight_layout()

    figure_path = (
        FIGURE_DIR /
        f"{IMAGE_ID}_exg_segmentation_diagnostic.png"
    )

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("\nSaved files:")
    print(mask_path)
    print(summary_path)
    print(figure_path)

    print("\nMask remains a candidate.")
    print("Hyperspectral alignment has NOT been verified.")


if __name__ == "__main__":
    main()
