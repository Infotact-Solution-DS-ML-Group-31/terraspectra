# TerraSpectra Phase F3 — Exploratory Unsupervised Spectral Learning

**Experiment date:** 2026-11-27
**Algorithm:** Standardized K-Means (`StandardScaler` + `KMeans`, `n_init=10`, `random_state=42`)
**K range evaluated:** [2, 3, 4, 5]
**Runtime:** 73.617 s | **Peak RSS:** 490.71 MiB

## 1. Scientific Boundaries & Scope

- Each hyperspectral cube was processed **independently**; spectral axes were never pooled or aligned.
- **Image 2436** uses its verified ENVI wavelength vector (`397.32–1003.58 nm`).
- **Image 3079** has 204 bands with **no verified wavelength calibration** and strictly uses zero-based band indices (`0–203`).
- **Image 2973** was skipped because no validated ROI mask exists; no ad-hoc segmentation was invented.
- Visual ROI labels for image 3079 are treated strictly as **post-hoc exploratory visual annotations**, not laboratory-confirmed disease ground truth, and were **never** used during clustering.
- **Pixels are not independent biological samples.** This experiment demonstrates an exploratory unsupervised workflow and is **not** a validated disease classifier, pathogen detector, or forecasting model.

## 2. Configuration & Memory-Conscious Design

- **Max fitting sample per cube:** 20,000 pixels via deterministic spatial grid-cell sampling (`32x32` tiles).
- **Batch prediction:** All valid ROI pixels assigned in batches of 4,096 pixels; only 1 cube loaded in memory at a time.
- **Silhouette evaluation:** Computed on a deterministic subsample of 5,000 pixels to avoid $O(N^2)$ pairwise distance memory pressure.
- **Stability evaluation:** Seed stability across seeds `(42, 101, 202)` (Adjusted Rand Index) and spatial block stability (`64x64` checkerboard split).

## 3. Per-Cube Results

### Image 2436 (Wavelength (nm))
- **Valid ROI pixels:** 53,693 | **Fit sample:** 20,000
- **Calibration status:** Verified for image 2436 only (Specim IQ ENVI headers).

| K | Silhouette (subsampled) | Inertia (std) | Seed ARI (mean) | Spatial Block ARI | Cluster Shares (%) |
|---:|---:|---:|---:|---:|---|
| 2 | 0.2751 | 2993236.0 | 0.9998 | -0.0111 | C0: 38.4%, C1: 61.6% |
| 3 | 0.3428 | 2207098.5 | 0.9950 | 0.8491 | C0: 25.9%, C1: 68.3%, C2: 5.9% |
| 4 | 0.2817 | 1886993.8 | 0.9951 | 0.6069 | C0: 33.2%, C1: 56.9%, C2: 5.3%, C3: 4.6% |
| 5 | 0.2879 | 1644747.2 | 0.9989 | 0.3111 | C0: 31.4%, C1: 56.7%, C2: 6.3%, C3: 5.2%, C4: 0.4% |

### Image 2973 (Skipped)
- **Reason:** No validated ROI mask exists for image 2973; no segmentation was invented.

### Image 3079 (Zero-based band index)
- **Valid ROI pixels:** 53,330 | **Fit sample:** 20,000
- **Calibration status:** No verified wavelength calibration for image 3079.

| K | Silhouette (subsampled) | Inertia (std) | Seed ARI (mean) | Spatial Block ARI | Cluster Shares (%) |
|---:|---:|---:|---:|---:|---|
| 2 | 0.4023 | 2834852.8 | 0.9983 | 0.5338 | C0: 84.4%, C1: 15.6% |
| 3 | 0.4457 | 1941208.6 | 0.9997 | 0.6545 | C0: 14.7%, C1: 9.1%, C2: 76.3% |
| 4 | 0.3197 | 1465057.4 | 0.9995 | 0.9157 | C0: 40.7%, C1: 46.2%, C2: 8.7%, C3: 4.4% |
| 5 | 0.3295 | 1214620.5 | 1.0000 | 0.8195 | C0: 37.8%, C1: 11.0%, C2: 4.2%, C3: 42.4%, C4: 4.6% |

#### Image 3079 Post-hoc Exploratory Comparison (K=3 vs Visual ROIs)
> Post-hoc exploratory comparison only. Visual ROI annotations are not laboratory-confirmed disease labels and were NOT used during clustering.
- **ARI vs visual ROIs:** 0.220606 | **NMI:** 0.224642

| Visual ROI | Cluster 0 | Cluster 1 | Cluster 2 |
|---|---:|---:|---:|
| visible_lesion | 924 | 3,212 | 1 |
| adjacent_unaffected | 4,062 | 929 | 13,670 |
| comparison_stem | 2,829 | 690 | 27,013 |

## 4. Limitations & Why This Is Not a Classifier

1. **Spatial autocorrelation:** Neighboring pixels on the same leaf or stem are strongly correlated; high seed/spatial ARI reflects within-specimen spectral structure, not population-level generalization.
2. **Specimen count:** Each cube represents a single biological specimen (*B. pseudocinerea* only, zero control cubes locally).
3. **Calibration asymmetry:** Image 3079 lacks verified wavelength calibration; clusters cannot be transferred between 2436 and 3079.
4. **Unsupervised clusters ≠ biological classes:** Clusters capture illumination geometry, curvature, specular highlights, and pigmentation variation alongside visual lesion contrast.
