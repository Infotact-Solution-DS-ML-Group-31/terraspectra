# Real-Cube PCA and ML Readiness

**Status:** Reproducible exploratory PCA completed; no classifier trained.

## Real-data PCA

PCA was fit independently for each eligible cube using 204 spectral measurements
per pixel and `IncrementalPCA`. Only existing annotated/segmented ROIs were used;
pixels outside each ROI, pixels with any non-finite spectral measurement, and
pixels flagged by an existing quality mask remain missing in spatial score maps.
No 1.0 threshold or clipping rule was added; an existing quality mask, where
available, was applied as stored. The NPZ measurements are not described as
independently calibrated laboratory reflectance. Cubes were not pooled, aligned, or compared as if their spectral
axes were interchangeable.

| Image | Status | Valid ROI pixels | PCA fit samples | PC1 / PC2 / PC3 variance | Spectral axis |
|---|---|---:|---:|---|---|
| 2436 | analyzed | 53,693 | 20,000 | 57.66% / 21.65% / 5.53% | Wavelength (nm) |
| 2973 | skipped: no appropriate existing ROI mask; no segmentation was invented, so this cube was not analyzed. | — | — | — | — |
| 3079 | analyzed | 53,330 | 12,411 | 73.22% / 21.41% / 3.65% | Zero-based band index |

### Sampling and reproducibility

- Method: deterministic sampling without replacement, stratified across a
  spatial grid; for image 3079, equal fit quotas were used for the visible
  lesion, adjacent visually unaffected stem, and comparison stem.
- Random seed: `42`.
- Maximum fit sample budget per cube: `20,000`;
  incremental fit and score transformation batch size:
  `2,048`.
- PCA was fit separately per cube. The wavelength axis is used only for image
  2436 (397.32–1003.58 nm); images 2973 and 3079 use zero-based band indices.
- Runtime for this run: 7.63 seconds.
- Peak process working set observed during this run:
  410.99
  MiB.

### Skipped cubes

- Image 2973: no appropriate existing ROI mask; no segmentation was invented, so this cube was not analyzed.

### Figures

- Image 2436 explained_variance: `outputs\figures\real_pca_2436_explained_variance.png`
- Image 2436 spatial_scores: `outputs\figures\real_pca_2436_spatial_scores.png`
- Image 2436 component_loadings: `outputs\figures\real_pca_2436_component_loadings.png`
- Image 3079 explained_variance: `outputs\figures\real_pca_3079_explained_variance.png`
- Image 3079 spatial_scores: `outputs\figures\real_pca_3079_spatial_scores.png`
- Image 3079 component_loadings: `outputs\figures\real_pca_3079_component_loadings.png`
- Image 3079 region_score_distributions: `outputs\figures\real_pca_3079_region_score_distributions.png`

## Application integration

The FastAPI application exposes the saved PCA artifacts under `/api/pca/`:

- `/api/pca/cubes`
- `/api/pca/{image_id}/summary`
- `/api/pca/{image_id}/explained-variance`
- `/api/pca/{image_id}/loadings`
- `/api/pca/{image_id}/spatial-scores`

Spatial score maps are averaged into a bounded downsampled grid for dashboard
visualization. The region-wise score-distribution figure for image 3079 is
present, but it has no structured saved CSV/NPZ values, so the API does not
fabricate or return per-pixel region distributions. The region-scores endpoint
returns a meaningful 404 for unavailable structured data.

## Interpretation limits

PCA is unsupervised dimensionality reduction, not classification. Components
are not disease indicators. Any separation in the image 3079 ROI score
distributions is exploratory only; the lesion is not laboratory-confirmed, and
the adjacent and comparison regions are not confirmed healthy. The PCA cannot
establish pathogen discrimination, disease classification, forecasting, or
predictive accuracy.

## Dataset and ML readiness

The local metadata contains **49 biological plant identities** and **193
plant-organ objects**. The project’s biological plant key is
`replicate + pathogen + sample`; the organ key adds `part`. The longitudinal
metadata script groups by all four fields, which identifies organ-level
objects, not independent biological plants. The existing identifiers were not
changed. For leakage prevention, future supervised evaluation must group by
biological plant identity (and report replicate-held-out results separately).

The three local cubes (2436, 2973, 3079) are each associated with
*B. pseudocinerea* and map to three distinct plant identities. They do not
provide validated healthy-versus-diseased or pathogen-discrimination labels.
Reliable supervised labels are not available locally: metadata pathogen
assignments are not pixel-level lesion ground truth, and the three cubes
contain only one pathogen class. A valid baseline classification experiment
cannot be trained or evaluated from these cubes.

GroupKFold is structurally possible on the 49 metadata plant groups, and
Leave-One-Replicate-Out can be specified across five replicates, but neither
creates a defensible experiment from the three local, single-class cubes.
Replicate-held-out folds also require checks for class coverage and
acquisition/season confounding. Before supervised baselines, obtain the
remaining class-diverse cubes (including controls and *B. cinerea*), traceable
and consistent spectral calibration/band mapping, and independent,
laboratory-confirmed plant/lesion labels. Evaluation must be grouped by
biological plant and must not treat pixels or multiple organs from one plant
as independent biological replicates.

## Geospatial scope

The local greenhouse cubes are not georeferenced field imagery. Rasterio/
GeoTIFF geospatial processing and geographic-coordinate claims are not part of
this completed work; no coordinates are fabricated.
