# TerraSpectra Phase F3.1 — Clustering Methodology and Validation Audit

**Audit date:** 2026-11-27
**Audited artifacts:** `src/data/analyze_real_cube_clustering.py`, `backend/app/services/clustering_service.py`, `backend/app/api/clustering.py`, `tests/test_unsupervised_clustering.py`, `docs/phase_f3_unsupervised_clustering.md`, `data/processed/reports/phase_f3_unsupervised_clustering.json`, and `data/processed/clustering/{2436,3079}_{clustering.npz,summary.json}`.
**Audit script:** `src/data/audit_f3_clustering_validation.py` | **JSON output:** `data/processed/reports/phase_f3_1_methodology_audit.json`

---

## 1. Executive Summary

Phase F3's unsupervised K-Means pipeline is **technically reproducible, memory-safe, and compliant with per-cube scientific boundaries**. Re-running the pipeline in memory reproduces the saved NPZ cluster maps and silhouette scores bit-for-bit (`all_exact_match = True` for both `2436` and `3079`).

However, the independent audit identified **one moderate methodological limitation** in spatial stability validation and **two important interpretive caveats**:

1. **Confirmed Finding (`F3.1-M1`, Moderate):** The Phase F3 `64x64` checkerboard spatial-block stability check allows direct 1-pixel edge adjacency between even and odd tiles and fits `StandardScaler` on the combined even+odd sample before splitting. Supplementary **contiguous spatial-block validation with a 32-pixel buffer gap** and train-only scaling yields substantially lower Adjusted Rand Index (ARI) along spatially non-stationary axes (e.g., `2436` K=3 North→South `ARI_vs_full = 0.2066` vs checkerboard `0.8491`; `3079` K=3 West→East `ARI_vs_full = 0.2673` vs checkerboard `0.6545`).
2. **Confirmed Finding (`F3.1-M2`, Low):** The `5,000`-pixel silhouette subsample is stable across random seeds (`std ≈ 0.0024` at K=3) and closely matches `N=10,000`. However, cosine silhouette scores (`0.1884` for `2436`, `0.2259` for `3079` at K=3) are roughly half the Euclidean scores (`0.3428` and `0.4457`), indicating that standardized Euclidean K-Means is strongly influenced by overall brightness/magnitude variation rather than spectral shape alone.
3. **Confirmed Finding (`F3.1-M3`, Informational):** Preprocessing, quality masking, per-cube isolation, zero-based band indexing for `3079`, post-hoc-only ROI comparison, and backend API consistency all passed without discrepancies.

---

## 2. Data Preprocessing & Scientific Boundary Audit

| Check | Status | Evidence |
|---|---|---|
| Quality & ROI masks applied | **Confirmed** | `2436` uses `2436_leaf_roi.npz` + `2436_quality_mask.npz` (`53,693` valid px); `3079` uses `3079_lesion_level_annotations.npz` union (`53,330` valid px); `2973` skipped cleanly. |
| Invalid pixels excluded before fitting | **Confirmed** | `validate_and_combine_masks` excludes non-finite spectra and quality-flagged pixels; invalid pixels receive `-1` in `cluster_map_k*`. |
| `StandardScaler` fit scope | **Confirmed for main pipeline; leak in checkerboard** | Main pipeline fits `StandardScaler` on the `20,000`-pixel fit sample only. The checkerboard stability check reused the combined `fit_X_scaled`. |
| No ROI labels used in fitting | **Confirmed** | `sample_spatial_grid_indices` samples across `valid_mask` tiles without reading region identities. |
| Per-cube isolation & wavelength guard | **Confirmed** | `2436` uses `397.32–1003.58 nm`; `3079` strictly uses zero-based band indices `0–203`. |
| No arbitrary spectral clipping | **Confirmed** | Stored NPZ values (including `> 1.0` in `3079`) are preserved without clipping. |

---

## 3. Silhouette Evaluation Audit

- **Implementation:** Euclidean `silhouette_score` on standardized 204-D spectra (`StandardScaler`) using a `5,000`-pixel random subsample of the `20,000`-pixel fit sample (`silhouette_samples = 5000`).
- **Representativeness (`K=3` sensitivity):**
  - **Image `2436`:** `N=5,000` across seeds `(43, 100, 200)` gave `[0.342814, 0.346808, 0.348476]` (`std = 0.002376`); `N=10,000` gave `0.346912`. Cosine `N=5,000` gave `0.188361`.
  - **Image `3079`:** `N=5,000` across seeds `(43, 100, 200)` gave `[0.445704, 0.451198, 0.446954]` (`std = 0.002351`); `N=10,000` gave `0.448025`. Cosine `N=5,000` gave `0.225901`.
- **Interpretation limits:** In 204-D space with spatially autocorrelated pixels, silhouette measures within-specimen geometric compactness in standardized Euclidean space, not biological separability or cross-plant generalizability.

---

## 4. Stability Evaluation & Supplementary Contiguous Spatial Validation

### Critique of Original Checkerboard Split
The Phase F3 `64x64` checkerboard split assigns adjacent tiles to train (`even`) and validation (`odd`). Because neighboring pixels share strong spatial autocorrelation and tiles touch along all four edges, spatial leakage inflates apparent stability.

### Supplementary Buffered Contiguous Spatial Split Protocol
Implemented in `src/data/audit_f3_clustering_validation.py`:
- **Splits:** (1) `north_to_south_buffered` around median valid row; (2) `west_to_east_buffered` around median valid column.
- **Spatial buffer:** `32` pixels excluded between train and validation regions (`±16` px around split line).
- **Strict isolation:** `StandardScaler` and `KMeans` (`n_init=10`, `random_state=42`) fit strictly on up to `10,000` pixels from the train half only, then evaluated on all pixels in the held-out validation half against both the full-ROI Phase F3 labels (`ARI_vs_full`) and an independent `KMeans` fit on the validation half (`ARI_vs_indep`).

### Comparison Table (`K=3`)

| Cube | Original Checkerboard ARI | Split | Train px / Val px | `ARI_vs_full` | `ARI_vs_indep` |
|---|---:|---|---:|---:|---:|
| `2436` | `0.8491` | North→South (32px buffer) | `21,415` / `21,556` | `0.2066` | `0.2091` |
| `2436` | `0.8491` | West→East (32px buffer) | `23,272` / `23,576` | `0.6512` | `0.2371` |
| `3079` | `0.6545` | North→South (32px buffer) | `25,451` / `25,560` | `0.8571` | `0.1366` |
| `3079` | `0.6545` | West→East (32px buffer) | `18,754` / `23,268` | `0.2673` | `0.2142` |

**Key observation:** Contiguous buffered splits expose strong spatial non-stationarity—North→South illumination/shading gradients in `2436` and West→East separation between the lesion-bearing stem and comparison stem in `3079`.

---

## 5. Cluster Interpretation & Nuisance Variation (`K=3`)

| Cube | Cluster | Pixels | Mean All-Band Intensity | Pixel Mean Intensity SD | Pixels with Any Band > 1.0 (%) |
|---|---|---:|---:|---:|---:|
| `2436` | `cluster_0` | `13,883` | `0.22678` | `0.01685` | `0.000%` |
| `2436` | `cluster_1` | `36,653` | `0.26429` | `0.01252` | `0.000%` |
| `2436` | `cluster_2` | `3,157` | `0.29681` | `0.03063` | `0.000%` |
| `3079` | `cluster_0` | `7,815` | `0.29558` | `0.06743` | `0.000%` |
| `3079` | `cluster_1` | `4,831` | `0.41579` | `0.04333` | `0.021%` |
| `3079` | `cluster_2` | `40,684` | `0.42928` | `0.03765` | `2.576%` |

- In **`2436`**, clusters stratify cleanly by overall brightness (`0.227 → 0.264 → 0.297`), consistent with leaf illumination gradients and surface orientation rather than distinct pathological states.
- In **`3079`**, `cluster_2` concentrates `99.9%` of the `> 1.0` measurements (`2.576%` of its pixels), consistent with cylindrical stem curvature and possible specular highlights, while `cluster_1` (`4,831` px) overlaps post-hoc with `3,212` pixels of the visual `visible_lesion` ROI alongside `929` `adjacent_unaffected` and `690` `comparison_stem` pixels. No cluster is labeled healthy or diseased.

---

## 6. Reproducibility & API Consistency

- In-memory re-execution of `analyze_cube_clustering` produced `all_exact_match = True` for both `2436` and `3079` across all $K \in \{2, 3, 4, 5\}$.
- `tests/test_unsupervised_clustering.py` verifies API responses (`/api/clustering/{id}/summary`, `/profiles`, `/spatial-map`) match saved JSON/NPZ artifacts.

---

## 7. Recommendations (Distinguished from Confirmed Findings)

1. **Recommendation:** Retain the Phase F3 checkerboard metric as historical baseline, and report the Phase F3.1 buffered contiguous spatial ARI alongside it in future experiments so spatial non-stationarity is not masked.
2. **Recommendation:** If shape-based clustering is explored in future work, evaluate L2-normalized / SNV-transformed spectra or cosine distance alongside standardized Euclidean K-Means to decouple overall brightness/illumination from spectral shape.
3. **Recommendation:** Do not attempt supervised classification or cross-cube transfer until independent biological plant replicates, control cubes, and verified wavelength calibration for `3079` are acquired.
