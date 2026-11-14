
# TerraSpectra: Hyperspectral Crop Disease Forecasting

## Project Overview

TerraSpectra is a hyperspectral image analysis project focused on exploring machine learning and deep learning techniques for agricultural crop health monitoring.

The project aims to build a pipeline for hyperspectral data ingestion, preprocessing, spectral analysis, classification, and geospatial visualization.

## Current Progress

- [x] Python environment setup
- [x] Synthetic hyperspectral dataset generation
- [x] HDF5 data storage
- [x] Dataset validation
- [x] Exploratory Data Analysis
- [x] Principal Component Analysis (PCA)
- [ ] Real agricultural hyperspectral dataset integration
- [ ] Baseline machine learning models
- [ ] 3D-CNN implementation
- [ ] Vision Transformer integration
- [ ] Model evaluation
- [ ] FastAPI inference backend
- [ ] GIS dashboard

## Technology Stack

- Python
- PyTorch
- NumPy
- Pandas
- Scikit-learn
- Rasterio
- HDF5 / h5py
- Matplotlib
- FastAPI
- React
- Deck.gl

## Project Structure

```text
terraspectra/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── mock/
│   └── metadata/
├── notebooks/
├── src/
│   ├── data/
│   ├── models/
│   ├── training/
│   └── inference/
├── backend/
├── frontend/
├── models/
├── outputs/
│   ├── figures/
│   └── predictions/
├── docs/
└── tests/
```

## Current Dataset

A synthetic hyperspectral dataset is currently being used to test the data pipeline.

- Image dimensions: 128 × 128 pixels
- Spectral bands: 64
- Wavelength range: 400–1000 nm
- Classes: Simulated healthy and stressed pixels
- Storage format: HDF5

**Note:** The synthetic dataset is for software development and pipeline testing only. It does not represent real crop disease measurements or validated disease predictions.

## Running the Dataset Generator

```bash
python src/data/create_synthetic_dataset.py
```

## Running Dataset Validation

```bash
python src/data/inspect_dataset.py
```

## Running Exploratory Data Analysis

```bash
python src/data/exploratory_analysis.py
```

## Project Status

Under development.

## Disclaimer

This is an academic internship project. Disease forecasting performance will only be assessed after integration of suitable real-world labelled agricultural data.
