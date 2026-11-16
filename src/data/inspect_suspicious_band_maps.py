
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


INPUT_FILE = Path("data/processed/cubes/2436_leaf_roi.npz")
OUTPUT_DIR = Path("outputs/figures")


def main():
    data = np.load(INPUT_FILE, allow_pickle=False)

    cube = data["cube"]
    wavelengths = data["wavelengths_nm"]
    leaf_mask = data["leaf_mask"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pairs = [
        (1000.49, 1003.58),
        (932.74, 935.81),
        (957.32, 960.40)
    ]

    print("=" * 65)
    print("SPATIAL SUSPICIOUS-BAND INVESTIGATION")
    print("=" * 65)

    fig, axes = plt.subplots(
        len(pairs), 3,
        figsize=(15, 13)
    )

    for row, (target_a, target_b) in enumerate(pairs):

        idx_a = int(np.argmin(abs(wavelengths - target_a)))
        idx_b = int(np.argmin(abs(wavelengths - target_b)))

        actual_a = float(wavelengths[idx_a])
        actual_b = float(wavelengths[idx_b])

        band_a = cube[:, :, idx_a]
        band_b = cube[:, :, idx_b]

        valid = (
            leaf_mask
            & np.isfinite(band_a)
            & np.isfinite(band_b)
        )

        a = band_a[valid]
        b = band_b[valid]

        difference = b - a
        correlation = np.corrcoef(a, b)[0, 1]

        print(f"\nPair: {actual_a:.2f} -> {actual_b:.2f} nm")
        print("Valid pixels:", len(a))
        print("Band A mean:", float(np.mean(a)))
        print("Band B mean:", float(np.mean(b)))
        print("Mean pixel difference:", float(np.mean(difference)))
        print("Median pixel difference:", float(np.median(difference)))
        print("Difference P05:", float(np.percentile(difference, 5)))
        print("Difference P95:", float(np.percentile(difference, 95)))
        print("Pixel-wise correlation:", float(correlation))

        # Robust display limits, calculated from valid leaf pixels.
        low_a, high_a = np.percentile(a, [2, 98])
        low_b, high_b = np.percentile(b, [2, 98])

        image_a = np.where(leaf_mask, band_a, np.nan)
        image_b = np.where(leaf_mask, band_b, np.nan)
        image_diff = np.where(leaf_mask, band_b - band_a, np.nan)

        diff_limit = np.nanpercentile(
            np.abs(image_diff), 98
        )

        panels = [
            (image_a, f"{actual_a:.2f} nm", low_a, high_a),
            (image_b, f"{actual_b:.2f} nm", low_b, high_b),
            (
                image_diff,
                f"Difference: B - A",
                -diff_limit,
                diff_limit
            )
        ]

        for col, (image, title, vmin, vmax) in enumerate(panels):
            ax = axes[row, col]

            plot = ax.imshow(
                image,
                cmap="coolwarm" if col == 2 else "viridis",
                vmin=vmin,
                vmax=vmax
            )

            ax.set_title(title)
            ax.axis("off")
            fig.colorbar(plot, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle(
        "Image 2436: Spatial Distribution of Suspicious Spectral Bands",
        fontsize=14
    )

    fig.tight_layout()

    output = OUTPUT_DIR / "2436_suspicious_band_maps.png"
    fig.savefig(output, dpi=200)
    plt.close(fig)

    print("\nSaved:", output)


if __name__ == "__main__":
    main()
