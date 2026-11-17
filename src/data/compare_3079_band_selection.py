
import numpy as np
import pandas as pd
from pathlib import Path

cube = np.load(
    "data/raw/tomato_botrytis/3079.npz"
)["arr_0"].astype(np.float32)

masks = np.load(
    "data/processed/segmentation/3079_roi_annotations.npz"
)

lesion_mask = masks["lesion_bearing_stem_mask"].astype(bool)
comparison_mask = masks["comparison_stem_mask"].astype(bool)

versions = {
    "A_original_204_bands": (0, 204),
    "B_remove_initial_3": (3, 204),
    "C_remove_initial_3_and_final_1": (3, 203),
}

output_dir = Path("data/processed/reports")
output_dir.mkdir(parents=True, exist_ok=True)

results = []

for name, (start, end) in versions.items():

    selected_cube = cube[:, :, start:end]

    lesion_values = selected_cube[lesion_mask]
    comparison_values = selected_cube[comparison_mask]

    lesion_mean = np.mean(lesion_values, axis=0)
    comparison_mean = np.mean(comparison_values, axis=0)

    lesion_std = np.std(lesion_values, axis=0)
    comparison_std = np.std(comparison_values, axis=0)

    results.append({
        "version": name,
        "selected_band_count": end - start,
        "first_original_band": start,
        "last_original_band": end - 1,
        "lesion_overall_mean": float(np.mean(lesion_mean)),
        "comparison_overall_mean": float(np.mean(comparison_mean)),
        "mean_absolute_spectral_difference": float(
            np.mean(np.abs(lesion_mean - comparison_mean))
        ),
        "lesion_average_band_std": float(np.mean(lesion_std)),
        "comparison_average_band_std": float(
            np.mean(comparison_std)
        ),
        "lesion_values_finite": bool(
            np.isfinite(lesion_values).all()
        ),
        "comparison_values_finite": bool(
            np.isfinite(comparison_values).all()
        ),
    })

df = pd.DataFrame(results)

csv_path = output_dir / "3079_band_selection_comparison.csv"
df.to_csv(csv_path, index=False)

print("\nBAND SELECTION COMPARISON")
print("-------------------------")
print(df.to_string(index=False))

print("\nSaved:", csv_path)
