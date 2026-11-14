import h5py
import numpy as np

file_path = "data/mock/synthetic_hyperspectral.h5"

with h5py.File(file_path, "r") as file:

    cube = file["hyperspectral_cube"][:]
    labels = file["labels"][:]
    wavelengths = file["wavelengths_nm"][:]

    print("DATASET VALIDATION")
    print("-" * 40)

    print("Cube shape:", cube.shape)
    print("Labels shape:", labels.shape)
    print("Wavelength shape:", wavelengths.shape)

    print("Data type:", cube.dtype)
    print("Minimum reflectance:", cube.min())
    print("Maximum reflectance:", cube.max())

    print("Healthy pixels:", np.sum(labels == 0))
    print("Stressed pixels:", np.sum(labels == 1))

    print("First wavelength:", wavelengths[0], "nm")
    print("Last wavelength:", wavelengths[-1], "nm")

    print("Metadata:", dict(file.attrs))

    assert cube.shape == (128, 128, 64)
    assert labels.shape == (128, 128)
    assert wavelengths.shape == (64,)
    assert np.isfinite(cube).all()
    assert labels.min() == 0
    assert labels.max() == 1

    print("\nAll validation checks passed!")