
from pathlib import Path

import h5py
import numpy as np


def create_synthetic_dataset(
    output_path="data/mock/synthetic_hyperspectral.h5",
    height=128,
    width=128,
    bands=64,
    seed=42,
):
    """
    Generate a synthetic hyperspectral cube for pipeline testing.

    Class 0: Healthy (simulated)
    Class 1: Stressed (simulated)

    This is not real crop-disease data.
    """

    rng = np.random.default_rng(seed)

    # Simulated wavelength range: 400–1000 nm
    wavelengths = np.linspace(400, 1000, bands, dtype=np.float32)

    # Normalized spectral position
    x = (wavelengths - 400) / 600

    # Create illustrative healthy and stressed spectral signatures
    healthy_spectrum = (
        0.10
        + 0.12 * np.exp(-((x - 0.25) / 0.12) ** 2)
        + 0.35 / (1 + np.exp(-(x - 0.58) * 25))
    )

    stressed_spectrum = (
        0.12
        + 0.08 * np.exp(-((x - 0.25) / 0.15) ** 2)
        + 0.20 / (1 + np.exp(-(x - 0.58) * 25))
    )

    # Initialize hyperspectral cube: height x width x bands
    cube = np.zeros((height, width, bands), dtype=np.float32)

    # Initialize pixel-level labels
    # 0 = simulated healthy
    # 1 = simulated stressed
    labels = np.zeros((height, width), dtype=np.uint8)

    # Create several spatial regions of simulated stress
    labels[20:55, 20:60] = 1
    labels[75:110, 70:115] = 1
    labels[45:70, 90:115] = 1

    # Generate spectra for each pixel
    for row in range(height):
        for col in range(width):

            if labels[row, col] == 0:
                spectrum = healthy_spectrum
            else:
                spectrum = stressed_spectrum

            # Add small variations and measurement noise
            pixel_variation = rng.normal(0, 0.015, bands)
            sensor_noise = rng.normal(0, 0.008, bands)

            cube[row, col, :] = np.clip(
                spectrum + pixel_variation + sensor_noise,
                0,
                1,
            )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Store cube, labels, and metadata in HDF5
    with h5py.File(output, "w") as file:
        dataset = file.create_dataset(
            "hyperspectral_cube",
            data=cube,
            compression="gzip",
            compression_opts=4,
        )

        dataset.attrs["dimensions"] = "height, width, spectral_bands"
        dataset.attrs["units"] = "simulated_reflectance"

        file.create_dataset("labels", data=labels)
        file.create_dataset("wavelengths_nm", data=wavelengths)

        file.attrs["project"] = "TerraSpectra"
        file.attrs["data_type"] = "synthetic"
        file.attrs["description"] = (
            "Simulated hyperspectral data for pipeline testing only"
        )
        file.attrs["class_0"] = "simulated_healthy"
        file.attrs["class_1"] = "simulated_stressed"

    print("Synthetic dataset created successfully.")
    print(f"Output: {output.resolve()}")
    print(f"Cube shape: {cube.shape}")
    print(f"Labels shape: {labels.shape}")
    print(f"Spectral bands: {bands}")
    print(f"Healthy pixels: {np.sum(labels == 0)}")
    print(f"Stressed pixels: {np.sum(labels == 1)}")


if __name__ == "__main__":
    create_synthetic_dataset()
