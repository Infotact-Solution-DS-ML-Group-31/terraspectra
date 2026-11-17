
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

input_file = Path(
    "data/processed/features/3079_spectral_diagnostics.csv"
)

output_dir = Path("outputs/figures")
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file)

bands = df["band_index_0based"]

# -------------------------------------------------
# Plot 1: Mean spectra and ROI differences
# -------------------------------------------------

plt.figure(figsize=(13, 6))

plt.plot(
    bands,
    df["lesion_mean"],
    label="Lesion-bearing stem",
    linewidth=1.8
)

plt.plot(
    bands,
    df["comparison_mean"],
    label="Comparison stem",
    linewidth=1.8
)

plt.axvspan(103, 111, alpha=0.12, label="Red-edge transition")
plt.axvspan(175, 202, alpha=0.10, label="Upper-NIR region")
plt.axvline(203, linestyle="--", alpha=0.8, label="Final band")

plt.xlabel("Spectral band index (0-based)")
plt.ylabel("Mean cube value")
plt.title("Image 3079: Mean Spectral Profiles")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig(
    output_dir / "3079_band_mean_diagnostics.png",
    dpi=200
)
plt.close()


# -------------------------------------------------
# Plot 2: Adjacent-band absolute mean changes
# -------------------------------------------------

plt.figure(figsize=(13, 6))

plt.plot(
    bands,
    df["lesion_adjacent_absolute_difference"],
    label="Lesion-bearing stem",
    linewidth=1.5
)

plt.plot(
    bands,
    df["comparison_adjacent_absolute_difference"],
    label="Comparison stem",
    linewidth=1.5
)

plt.axvspan(103, 111, alpha=0.12, label="Red-edge transition")
plt.axvspan(175, 202, alpha=0.10, label="Upper-NIR region")
plt.axvline(203, linestyle="--", alpha=0.8, label="Final band")

plt.xlabel("Spectral band index (0-based)")
plt.ylabel("Absolute adjacent-band mean change")
plt.title("Image 3079: Adjacent-Band Spectral Changes")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig(
    output_dir / "3079_adjacent_band_changes.png",
    dpi=200
)
plt.close()

print("Diagnostic plots generated:")
print(output_dir / "3079_band_mean_diagnostics.png")
print(output_dir / "3079_adjacent_band_changes.png")
