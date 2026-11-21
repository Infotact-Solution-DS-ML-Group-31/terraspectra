
# TerraSpectra: Hyperspectral Crop Disease Forecasting

## Project Overview

TerraSpectra is a hyperspectral image analysis project focused on exploring machine learning and deep learning techniques for agricultural crop health monitoring.

The project aims to build a pipeline for hyperspectral data ingestion, preprocessing, spectral analysis, classification, and geospatial visualization.

## Current Progress

- [x] Python environment setup
- [x] Synthetic hyperspectral dataset generation
- [x] HDF5 data storage
- [x] Dataset validation
- [x] Exploratory analysis and PCA on a synthetic 64-band dataset
- [x] Local tomato hyperspectral data integration and real-data spectral analysis
- [x] Independent, mask-aware PCA on eligible real 204-band cubes (see [real-data PCA report](docs/real_data_pca_report.md))
- [ ] Baseline machine learning models
- [ ] 3D-CNN implementation
- [ ] Vision Transformer integration
- [ ] Model evaluation
- [ ] FastAPI inference backend
- [ ] GIS dashboard (field geospatial data and georeferencing not yet available)

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

## Synthetic Development Dataset

The synthetic dataset remains useful for software development and pipeline testing.

- Image dimensions: 128 × 128 pixels
- Spectral bands: 64
- Wavelength range: 400–1000 nm
- Classes: Simulated healthy and stressed pixels
- Storage format: HDF5

**Note:** The synthetic dataset is for software development and pipeline testing only. It does not represent real crop disease measurements or validated disease predictions.

## Local Real Dataset and Analysis

Three local tomato hyperspectral cubes are available (images 2436, 2973, and 3079), each with 204 bands and associated with *B. pseudocinerea*. Real-data spectral analyses are complete for the available supported tasks. Real-data PCA is fit separately per eligible cube using existing ROI/quality masks; cubes are not combined or spectrally aligned without evidence. Image 2436 alone has verified wavelengths (397.32–1003.58 nm); images 2973 and 3079 are represented only by zero-based band indices.

Image 2973 currently has no appropriate local ROI mask and is skipped by real-cube PCA. The local cubes do not support supervised disease classification: they represent only one pathogen class, with no confirmed lesion/healthy labels. No model performance or disease forecasting is claimed. See the [real-data PCA and ML readiness report](docs/real_data_pca_report.md) and [dataset suitability assessment](docs/dataset_suitability_assessment.md).

The synthetic PCA in `src/data/exploratory_analysis.py` is separate from the real-data PCA workflow in `src/data/analyze_real_cube_pca.py`.

## PCA API and Dashboard

The dashboard includes a dedicated **PCA Analysis** view for saved real-cube PCA artifacts:

- Image 2436: independent PCA with verified wavelengths from 397.32 to 1003.58 nm.
- Image 3079: independent PCA using zero-based band indices 0–203.
- Image 2973: explicitly unavailable because no appropriate existing ROI mask was available.

PCA results are served from `data/processed/pca/` and saved NPZ/CSV artifacts; the backend does not load or refit the original hyperspectral cubes for these endpoints.

| Endpoint | Purpose |
|---|---|
| `GET /api/pca/cubes` | List available and unavailable PCA cubes |
| `GET /api/pca/{image_id}/summary` | Retrieve per-cube PCA metadata |
| `GET /api/pca/{image_id}/explained-variance` | Retrieve PC1–PC3 variance and cumulative variance |
| `GET /api/pca/{image_id}/loadings` | Retrieve saved component loadings |
| `GET /api/pca/{image_id}/spatial-scores?max_size=64` | Retrieve downsampled saved spatial score maps |
| `GET /api/pca/{image_id}/region-scores` | Reserved availability check; 3079 structured distributions are not saved |

PCA was fitted independently per cube. Component scores and loadings do not share a common basis and must not be compared across cubes. Components are exploratory mathematical components, not healthy/diseased classes. No disease classification, forecasting, or predictive accuracy is claimed.

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

Under development. Baseline modeling remains blocked on class-diverse cubes, scientifically defensible plant-level labels, and validated evaluation data. 3D-CNN and Vision Transformer development has not begun. The available greenhouse cubes are not georeferenced field imagery; Rasterio/GeoTIFF field processing is not complete.

## Disclaimer

This is an academic internship project. Disease forecasting performance will only be assessed after integration of suitable real-world labelled agricultural data.
