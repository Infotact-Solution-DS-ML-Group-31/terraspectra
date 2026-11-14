
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

# --------------------------------------------------
# 1. Load the synthetic hyperspectral dataset
# --------------------------------------------------

DATA_PATH = "data/mock/synthetic_hyperspectral.h5"
OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with h5py.File(DATA_PATH, "r") as file:
    cube = file["hyperspectral_cube"][:]
    labels = file["labels"][:]
    wavelengths = file["wavelengths_nm"][:]

height, width, bands = cube.shape

print("Dataset loaded successfully")
print("Cube shape:", cube.shape)
print("Number of spectral bands:", bands)


# --------------------------------------------------
# 2. Visualize selected spectral bands
# --------------------------------------------------

selected_bands = [10, 30, 50]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, band_index in zip(axes, selected_bands):
    image = cube[:, :, band_index]

    ax.imshow(image, cmap="viridis")
    ax.set_title(
        f"Band {band_index} ({wavelengths[band_index]:.1f} nm)"
    )
    ax.axis("off")

fig.suptitle("Selected Hyperspectral Bands")
plt.tight_layout()

fig.savefig(
    OUTPUT_DIR / "spectral_band_visualization.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()


# --------------------------------------------------
# 3. Compare healthy and stressed spectral signatures
# --------------------------------------------------

healthy_pixels = cube[labels == 0]
stressed_pixels = cube[labels == 1]

healthy_mean = healthy_pixels.mean(axis=0)
stressed_mean = stressed_pixels.mean(axis=0)

healthy_std = healthy_pixels.std(axis=0)
stressed_std = stressed_pixels.std(axis=0)

plt.figure(figsize=(11, 6))

plt.plot(
    wavelengths,
    healthy_mean,
    label="Simulated Healthy",
    linewidth=2,
)

plt.plot(
    wavelengths,
    stressed_mean,
    label="Simulated Stressed",
    linewidth=2,
)

plt.fill_between(
    wavelengths,
    healthy_mean - healthy_std,
    healthy_mean + healthy_std,
    alpha=0.2,
)

plt.fill_between(
    wavelengths,
    stressed_mean - stressed_std,
    stressed_mean + stressed_std,
    alpha=0.2,
)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Simulated Reflectance")
plt.title("Mean Spectral Signatures")
plt.legend()
plt.grid(alpha=0.3)

plt.savefig(
    OUTPUT_DIR / "spectral_signature_comparison.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()


# --------------------------------------------------
# 4. Apply Principal Component Analysis (PCA)
# --------------------------------------------------

# Convert H x W x B cube into N x B matrix.
# Each row represents one pixel's spectral signature.

X = cube.reshape(-1, bands)

# Fit PCA for exploratory visualization only.
pca = PCA(n_components=3)

X_pca = pca.fit_transform(X)

explained_variance = pca.explained_variance_ratio_

print("\nPCA RESULTS")
print("-" * 40)

for i, variance in enumerate(explained_variance, start=1):
    print(f"PC{i} explained variance: {variance * 100:.2f}%")

print(
    "Total variance explained by first 3 components:",
    f"{explained_variance.sum() * 100:.2f}%",
)


# --------------------------------------------------
# 5. Display first three PCA components
# --------------------------------------------------

pca_image = X_pca.reshape(height, width, 3)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, ax in enumerate(axes):
    image = ax.imshow(pca_image[:, :, i], cmap="viridis")
    ax.set_title(f"Principal Component {i + 1}")
    ax.axis("off")
    fig.colorbar(image, ax=ax, fraction=0.046)

fig.suptitle("PCA Component Visualization")
plt.tight_layout()

fig.savefig(
    OUTPUT_DIR / "pca_components.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()


# --------------------------------------------------
# 6. Display PCA explained variance
# --------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    ["PC1", "PC2", "PC3"],
    explained_variance * 100,
)

plt.ylabel("Explained Variance (%)")
plt.xlabel("Principal Components")
plt.title("PCA Explained Variance")

plt.savefig(
    OUTPUT_DIR / "pca_explained_variance.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()


# --------------------------------------------------
# 7. Final summary
# --------------------------------------------------

print("\nEDA completed successfully.")

print("Generated figures:")

for filename in [
    "spectral_band_visualization.png",
    "spectral_signature_comparison.png",
    "pca_components.png",
    "pca_explained_variance.png",
]:
    print(OUTPUT_DIR / filename)
