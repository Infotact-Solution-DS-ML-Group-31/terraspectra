# TerraSpectra Phase F2.3 - Controlled Alternaria Cube Acquisition and Validation

**Audit date:** 2026-11-26
**Source:** DataverseLV DOI [10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ), version 1
**Scope:** Acquire and technically inspect only `1797.npz`, `1827.npz`, and `1855.npz`. No models were trained, no disease classification was run, and no production pipeline or existing Botrytis/Zenodo files were modified.

## Executive result and decision

All three files were acquired from their official Dataverse file-ID endpoints into `data/raw/external/alternaria/`. Their byte sizes and MD5 checksums match the published Dataverse API manifest. Their combined size is **201,798,652 bytes**. Raw files are ignored by Git.

Each NPZ contains only one key, `arr_0`: a numeric cube candidate with shape **512 x 512 x 204**, dtype **float16**, and 53,477,376 values. All entries are finite. The files have matching shape/dtype and are not exact duplicates. The arrays contain no wavelength, calibration/reference, or sample-metadata arrays.

The array maximum ranges from 1,928 to 2,730, while means are about 0.186–0.209 and standard deviations about 1.702–4.423. Values greater than 1 occur in each cube. These distributions need source clarification; no arbitrary cutoff was used to call the files corrupt, and the values are **not claimed to be reflectance**.

**CONDITIONAL GO — technically inspectable, but metadata and calibration gaps remain.** These are suitable only for source-separated descriptive exploration after the wavelength axis and radiometric processing are clarified. The three samples map through the source metadata to three distinct inoculated plants in trial 4 (two isolate 028, one isolate 065); none is a public control cube. The plant mapping is external to the NPZ files and does not provide diagnostic assay confirmation. This is not a suitable dataset for classification or forecasting, and it must remain separate from Botrytis.

Zenodo Phase F3 remains **NO-GO**, unchanged.

## Pre-acquisition verification and controlled transfer

The official Dataverse API was accessible during F2.3. Its latest-version file list confirmed each exact filename, file ID, byte size, and MD5 checksum. The official download endpoint was confirmed by successful HTTP HEAD requests before transfer. No unofficial mirrors were used.

| File | Dataverse file ID | Official download URL | Published bytes | Official MD5 | Actual MD5 | Actual SHA-256 | Download started UTC |
|---|---:|---|---:|---|---|---|---|
| `1797.npz` | 3362 | <https://dv.dataverse.lv/api/access/datafile/3362> | 68,008,284 | `e385373eb2407eb1fdf0c7a7e80467e2` | `e385373eb2407eb1fdf0c7a7e80467e2` | `602cd4970366c4380e12866b4f4a47d18556f16736ad47d085e15906b425ff10` | 2026-11-26T17:22:24.375Z |
| `1827.npz` | 3360 | <https://dv.dataverse.lv/api/access/datafile/3360> | 66,098,654 | `703ec0db82405afbd76b4271a1965931` | `703ec0db82405afbd76b4271a1965931` | `1b67f776d3a818cd0fc85e17e3cddf9ccb3cb71c832e0ec7737eba0ebb048a80` | 2026-11-26T17:26:22.056Z |
| `1855.npz` | 3361 | <https://dv.dataverse.lv/api/access/datafile/3361> | 67,691,714 | `c601acf8b0298916a100b99211fac8db` | `c601acf8b0298916a100b99211fac8db` | `879d2b1929c6a7a302f3fc35d2617ca4ec855158474796a4a0dd21c2eea4cc4c` | 2026-11-26T17:29:59.235Z |
| **Total** |  |  | **201,798,652** |  | **3/3 match** |  |  |

Acquisition timestamps record the start of each individual transfer. Files were downloaded to temporary `.download` names and moved to their final names only after size and MD5 verification. The destination directory did not exist before acquisition; no files were overwritten. `.gitignore` ignores `data/raw/`, and `git check-ignore` confirmed all three raw files are ignored. No raw file was staged.

## NPZ inspection

Inspection used NumPy `np.load(..., allow_pickle=False)`. All three files opened successfully. Each has only the `arr_0` key and one unambiguous three-dimensional numeric candidate. The raw arrays were not normalized, clipped, or otherwise transformed. Array SHA-256 below is computed over the canonical array dtype, shape, and C-order bytes; it is distinct from the compressed-file SHA-256 in the acquisition manifest.

| File | Keys | Shape | Dtype | Elements | Finite | NaN / +Inf / -Inf | Min | Max | Mean | Std. dev. | Zero | Negative | >1 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1797.npz` | `arr_0` | 512 x 512 x 204 | float16 | 53,477,376 | 53,477,376 | 0 / 0 / 0 | 0 | 2,184 | 0.186395 | 2.042187 | 241 | 0 | 465,637 |
| `1827.npz` | `arr_0` | 512 x 512 x 204 | float16 | 53,477,376 | 53,477,376 | 0 / 0 / 0 | 0 | 2,730 | 0.200248 | 4.422753 | 338 | 0 | 198,748 |
| `1855.npz` | `arr_0` | 512 x 512 x 204 | float16 | 53,477,376 | 53,477,376 | 0 / 0 / 0 | 0 | 1,928 | 0.209237 | 1.702373 | 30 | 0 | 444,163 |

The full per-array record, including hashes and non-finite counts, is in [the array inventory CSV](../data/processed/reports/phase_f2_3_alternaria_array_inventory.csv). These are descriptive statistics over stored array values, not calibrated physical measurements. The large maxima relative to means and the presence of values greater than 1 merit author clarification; without verified units/calibration they are not enough to conclude that values are invalid or to label them reflectance.

### Axis and wavelength evidence

No key indicates wavelengths, band centers, calibration, references, plant, leaf, replicate, date, pathogen, or disease label. The arrays do not embed a wavelength vector or reference captures. Their NPZ structure alone does not identify axis order.

The likely organization is `(row, column, band)` because the prior source README describes calibrated cubes as `512 x 512 x 204` and 204 spectral bands, matching this observed layout and the project's existing format. This is an **inference**, not an axis annotation in the files. Since the first two dimensions are both 512, their orientation cannot be distinguished from shape. A wavelength-aware analysis is not supportable until the actual per-cube headers/vector, band ordering, and axis mapping are confirmed.

## Cross-file and biological-sample validation

- **Structure:** All three files have the same single `arr_0` numeric 3D candidate, shape `(512, 512, 204)`, dtype `float16`.
- **Exact duplicates:** None. Canonical array SHA-256 values differ: `1797` = `c6f3a616ca1803b91f51482b4a22ba020c37d4ebaef9ad33b796a4ad01e778fb`; `1827` = `d808c2328e9e4048e2cdadb3e5e01138c5b23e44288ddfca320000c2ef6d7e96`; `1855` = `fe5f97389fbac796493e58eb24d27e0720793cd876200bc25e80ccf21b6ea021`.
- **Finite values:** All values in all files are finite; no NaN, positive infinity, or negative infinity was found. No negative values were found. No source-specific valid range is documented well enough to call high values invalid.
- **Identifiers inside NPZ:** None. File contents provide no plant, leaf, date, replicate, or label metadata.
- **External metadata join:** The F1 inspection of the official TSV, carried forward in the F2.2 report, maps these filenames as follows:

| File | Trial | Plant identifier | Leaf / part | Date | Source grouping |
|---|---:|---|---|---|---|
| `1797.npz` | 4 | `065/I` | 2 / G | 2025-07-07 | *A. protenta* isolate 065 |
| `1827.npz` | 4 | `028/IV` | 2 / 2 | 2025-07-10 | *A. protenta* isolate 028 |
| `1855.npz` | 4 | `028/II` | 1 / 8 | 2025-07-14 | *A. protenta* isolate 028 |

This mapping supports three distinct plant identifiers **via external source metadata**, not through NPZ contents. All three are inoculated isolate groups; the publicly listed cube set contains **no control cube**. These are source grouping labels, not per-cube pathogen assay results or disease-severity labels.

**Correction to Phase F2.2 narrative:** The F2.2 JSON and report text incorrectly said one of the three public cubes was a control. The cube-to-plant mapping in that same audit and the source TSV show `065/I`, `028/IV`, and `028/II`; all are inoculated plants. The F2.2 report and JSON have been corrected to state that there is no public control cube. The F2.2 conclusion that the public set cannot support a valid classification split remains unchanged.

## Existing pipeline compatibility

Reviewed [preprocess_hyperspectral.py](../src/data/preprocess_hyperspectral.py) and [extract_spectral_features.py](../src/data/extract_spectral_features.py):

- The cube key `arr_0`, shape, band count, and dtype match the current loader's structural expectations.
- The loader is tied to `data/raw/tomato_botrytis/`, a fixed image ID, and the project-specific 2436 wavelength CSV. Pointing it at these files without an adapter would incorrectly reuse that wavelength vector and metadata.
- Feature extraction expects TerraSpectra-specific ROI files and treats output as reflectance. No compatible Alternaria masks, calibrated units, or verified wavelength axis were present in these NPZs.
- A future separate adapter must map `arr_0` without altering raw values; attach the official DOI/file ID and explicit TSV sample mapping; retain trial, plant, isolate, leaf, part, and date; and represent wavelength/calibration status as unknown until verified. Keep this adapter and outputs separate from Botrytis.

Author clarification required before wavelength-aware integration: provide per-file ENVI headers/wavelength vectors and axis definition; band ordering and dropped/bad bands; calibration equation, units, and reference association; explanation of stored values and the large maxima; and confirmation of each file-to-plant/trial/label mapping and diagnostic evidence. The three-cube set has no control and only one plant for isolate 065, so more independently sampled cubes, including controls, are required before designing classification evaluation.

## Reproducibility and validation

The isolated inspector is [inspect_alternaria_cubes.py](../src/data/inspect_alternaria_cubes.py). Focused tests use small synthetic NPZ files and do not load the 202 MB source cubes:

```powershell
python -m pytest -q tests/test_alternaria_cube_validation.py
```

The manifest records official and computed checksums. The array inventory records one row per NPZ array key. No model or production preprocessing was run.

## Final scientific decision

**CONDITIONAL GO — technically inspectable, but specific metadata or validation gaps remain.**

The files are structurally valid, checksum-verified numeric cube candidates and map through the source TSV to three different inoculated plants. However, the NPZ files contain no wavelength or calibration data, do not carry sample identifiers or labels internally, and show unexplained high maxima relative to their means. The three publicly available cubes also contain no control and are insufficient for biologically independent classification evaluation. Restrict any next step to source-separated descriptive exploration after author confirmation of axis, wavelengths, units, and calibration. Keep Alternaria separate from Botrytis, do not claim reflectance, prediction, or forecasting, and keep Zenodo Phase F3 at **NO-GO**.
