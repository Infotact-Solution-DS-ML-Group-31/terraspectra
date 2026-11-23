# Phase F1 - Acquisition Recommendation for Phase F2

## Decision

Proceed to Phase F2 for a small, source-separated acquisition and provenance check. Do not merge new data into the existing Botrytis dataset or train a combined model yet. No source was found to be directly compatible without further validation.

## Acquire first: Zenodo fungal tomato HSI

The [Zenodo dataset, DOI 10.5281/zenodo.15800414](https://doi.org/10.5281/zenodo.15800414), is the best first candidate for additional Botrytis-labeled material: it publicly lists eight `Botrytis_cinerea_*.mat` image candidates and eight healthy-control files. The listing includes original image files as well as derived feature matrices. Its CC BY 4.0 license is verified in the record API and DataCite.

Download only this 16-file pilot in F2:

- `Botrytis_cinerea_1.mat` through `Botrytis_cinerea_8.mat`
- `Healthy_1.mat` through `Healthy_8.mat`

The current manifest totals **2,254,793,632 bytes** for these files (about 2.10 GiB). Record the manifest checksums and keep these files in a separate source staging area. Do not download the full approximately 6.05 GB record as the first step.

Do **not** use these derived feature files for a new model or evaluation:

- `Botrytis_cinerea_features.mat`
- `Healthy_features.mat`
- the other three `*_features.mat` files
- `Simillaritycheck_Manhatan_and_Cosine.m` results/splits

The extraction script is useful documentation, but its assumptions (20 images per class and 550 bands) are not reconciled with the eight numbered image files per class; its file-to-plant/timepoint mapping is unknown.

Before or alongside F2 download, request from the dataset author:

1. The plant/pot, leaf, replicate, and time-point key for each numbered MAT file.
2. Confirmation of which days are present (Zenodo says days 1/3/5/7; the paper reports days 1/3/5/7/9/11).
3. The actual MAT variable names, cube dimensions, wavelength vector/band order, radiometric units, and reflectance calibration procedure.
4. The number of independent plants represented by these files and whether scans are repeated measurements.
5. The per-sample disease-label and inoculum verification method, including any severity scores or laboratory results.
6. The provenance and exact sample membership of each bundled feature MAT file and the published train/test split.

Until confirmed, treat these MAT files as *Botrytis cinerea*-labeled external candidates, not as eight independent plants or calibrated TerraSpectra-compatible cubes.

## Second: DataverseLV Alternaria source, for separate technical comparison

For a same-camera-family comparison, acquire these small files from [DataverseLV DOI 10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ):

- `metadata.tab`
- `readme.md`
- `1797.npz`
- `1827.npz`
- `1855.npz`

These are three cubes from three distinct plants in one *Alternaria protenta* experiment, not Botrytis data. Keep *A. protenta* and its isolates (028/065) separate from both Botrytis species. Resolve README/metadata distance and integration-time units before comparing acquisition settings.

If F2 needs to audit wavelength calibration, then download the corresponding raw archives separately and inspect only their headers and dark/white references:

- `1797.zip`
- `1827.zip`
- `1855.zip`

Do not treat their presence in the public listing as proof that the archives contain complete, valid calibration assets until inspected.

## Keep separate or defer

- **Current DataverseLV Botrytis baseline (10.71782/DATA/MPCTZC):** do not reacquire its three example NPZ cubes already present locally. The public listing has `metadata.tab`, `readme.md`, `rgb.zip`, `2436.npz`/`2973.npz`/`3079.npz`, and `2436.zip`/`2973.zip`/`3079.zip`. Request the full dataset only if additional *B. cinerea*, *B. pseudocinerea*, or control samples and plant/time identifiers are needed. Do not substitute the 2436 wavelength vector for the other cubes.
- **USDA Ag Data Commons bacterial leaf spot:** retain as an external *Xanthomonas perforans* benchmark, not a fungal class. Do not download the 15.4 GB `tomato_leaf.zip` unless the Phase F2 scope explicitly includes a bacterial benchmark. Pin the latest version and checksum; the current page is version 2, while DataCite metadata also describes version 1.
- **Zenodo point spectroscopy 10.5281/zenodo.10498473:** no public files are listed and access is restricted. Request access and license-scope clarification only if point spectroscopy is in scope; it is not an image-cube source.
- **Zenodo sepal abstract 10.5281/zenodo.4896828:** no dataset files to acquire.

## Required pre-integration validation

1. Verify file checksums and source versions; keep an immutable source manifest.
2. Inspect MAT/NPZ/ENVI headers without silently converting or assuming wavelength axes; document actual shape, dtype, units, and per-cube calibration.
3. Obtain one unambiguous row per image/cube with source, species, isolate, plant, leaf/organ, replicate, date, days post inoculation, severity, and validation status where available.
4. Verify whether each image is a new plant or a repeated image/leaf/timepoint. Set biological sample counts from plant IDs, never from cube, leaf, pixel, or band counts.
5. Keep pathogen species and experiment IDs distinct. Do not relabel Alternaria or bacterial observations as Botrytis.
6. Check differences in cultivar, greenhouse/lab conditions, illumination, sensor response, spectral calibration, and spatial resolution. Do not concatenate spectra or reuse calibration across datasets without a verified wavelength mapping and preprocessing protocol.
7. Create plant-grouped partitions before extracting features. Keep all timepoints and organs from one plant in one partition; consider trial-grouped external validation.
8. Use sample-level assay/label evidence where provided. Treat image class names and visual symptoms as weaker evidence unless connected to inoculation and pathology records.
9. Recompute features from validated source cubes for any new evaluation. Avoid packaged feature matrices and random image-level splits until their sample membership and provenance are resolved.

**Phase F2 gate:** limited acquisition and data-integrity checks are approved. Integration into the existing Botrytis modeling pool remains **NO-GO** until biological identity, data calibration, and plant-level leakage controls are verified.
