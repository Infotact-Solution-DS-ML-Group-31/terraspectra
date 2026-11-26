# TerraSpectra Phase F2.2 - Alternaria Dataset Feasibility Audit

**Audit date:** 2026-11-26
**Dataset:** DataverseLV DOI [10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ)
**Scope:** Metadata and official file-list audit only. No Alternaria files were downloaded or opened, no model was trained, and no production pipeline or existing raw data was changed.

## Executive decision

**CONDITIONAL GO — suitable after clearly specified metadata and validation gaps are resolved, for source-separated exploratory work only.**

This is a relevant tomato-leaf disease dataset from the same Specim IQ camera family and cultivar as TerraSpectra's existing dataset, and its 1,000-row metadata describes 13 plants across five trials. However, the public record lists only three example NPZ cubes, one from each of three plants, while the other metadata observations do not have publicly listed cube files. The available subset is too small for a biologically independent train/test split that represents both infected and control classes. Its 204-band layout and calibration are source-described, but no cube headers, wavelength vector, calibration assets, or radiometric processing were verified in this phase.

Do not treat *Alternaria protenta* as a Botrytis class, pool the datasets, claim calibrated reflectance, or claim disease prediction or forecasting. Keep this experiment distinct. The Zenodo dataset's Phase F3 status remains **NO-GO**, unchanged from Phase F2.1.

## Repository state and scope control

At audit start, the repository was on branch `main`, HEAD `e5cfe8be45d4aa88009b9e592ff25369a6d987e4`, tracking `origin/main`. The worktree had no tracked modifications and had unrelated untracked reports, analyses, and verification images. These were preserved. No reset, cleanup, staging, commit, or push was performed.

Reviewed the Phase F1 source audit and acquisition recommendation, Phase F2 and F2.1 reports, source inventory, Phase F2 manifests, existing dataset inventory, biological-sample summary, and current preprocessing/feature-extraction assumptions. See [Phase F1 source audit](phase_f1_dataset_source_audit.md), [Phase F1 acquisition recommendation](phase_f1_acquisition_recommendation.md), [Phase F2 acquisition validation](phase_f2_acquisition_validation.md), and [Phase F2.1 external dataset inspection](phase_f2_1_external_dataset_inspection.md).

This was a metadata/file-list audit. No Alternaria cube or archive was downloaded, extracted, or opened. The three listed NPZ files total **201,798,652 bytes (~0.202 GB decimal)**. Downloading them or any raw archive requires a separately approved acquisition step; the three raw-camera ZIPs total **145,442,225 bytes**.

## Evidence and confidence

Confidence describes support for statements, not dataset quality:

- **High:** Directly present in the official DataCite record or in the prior Phase F1 inspection of the official Dataverse API, README, and metadata table.
- **Medium:** Reported by the source documentation or prior audit, but not independently rechecked against cube bytes/headers in F2.2.
- **Low / unknown:** Not provided by the accessed source material, or would require file-level inspection or author clarification.

The Dataverse API and landing-page requests were attempted on 2026-11-26 but returned HTTP 503/403 through the available fetch route. DataCite's DOI metadata API was accessible. The detailed Dataverse file list, README, and TSV facts below are carried forward from the Phase F1 audit, which records successful access to the official Dataverse API and the small metadata/readme files. F2.2 did not repeat those downloads.

## Dataset identity, publication, license, and access

| Item | Finding | Confidence |
|---|---|---|
| Title | “Hyperspectral imaging (HS) of tomato leaves inoculated with *Alternaria protenta*”; subtitle: “Alternaria protenta disease development study on tomato leaves.” | High |
| DOI / repository | 10.71782/DATA/MODVMZ; DataverseLV. DOI landing page is the repository's canonical access point. | High |
| Authors | Vitalijs Komasilovs, Maksims Filipovics, and Olvija Komasilova; DataCite lists Latvia University of Life Sciences and Technologies for all three. | High |
| Record details | DataCite version 1.0; publication year 2026; submitted 2026-01-30; available 2026-02-16. Collection dates are recorded as 2025-04-11 through 2025-08-28. | High |
| Associated publication | DataCite `relatedIdentifiers` is empty and the record presents the dataset itself as the published resource. No associated journal article or separate publication DOI was identified in the accessed record. This does not prove that no related paper exists. | High for no linked item in DataCite; low for absence of any external publication |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0), with open-access rights in DataCite. Preserve attribution and cite the DOI. | High |
| Repository availability | The prior official API/file-list audit reports nine listed files. The F2.2 fetch route returned errors; DataCite metadata was independently accessible. | High for prior file list; medium for current listing |

No separate publication methods, per-plant pathology assay, or disease-severity protocol can be attributed to this record on the evidence inspected. The dataset abstract describes a greenhouse disease-development study and additional preprocessing/feature-extraction data, but it does not identify a linked paper.

## Public file inventory and expected storage

The prior Phase F1 audit of the official file list reports **9 files**, about **636,304,181 bytes (~0.636 GB decimal)** total:

| Listed file | Bytes | Format / evidence |
|---|---:|---|
| `metadata.tab` | 58,140 | TSV metadata table; prior audit reports 1,000 rows and 9 columns |
| `readme.md` | 5,296 | Dataset documentation |
| `rgb.zip` | 288,999,868 | ZIP archive; contents not inspected in F2.2 |
| `1797.npz` | 68,008,284 | Listed NPZ cube candidate; not downloaded/opened |
| `1827.npz` | 66,098,654 | Listed NPZ cube candidate; not downloaded/opened |
| `1855.npz` | 67,691,714 | Listed NPZ cube candidate; not downloaded/opened |
| `1797.zip` | 47,126,377 | Listed raw-camera archive; contents not inspected |
| `1827.zip` | 48,558,287 | Listed raw-camera archive; contents not inspected |
| `1855.zip` | 49,757,561 | Listed raw-camera archive; contents not inspected |

The three NPZ files are **three publicly listed cube artifacts**, not proof of only three experiment samples. Conversely, 1,000 metadata rows are not 1,000 downloadable cubes or independent biological samples. The raw archives' names and listed sizes do not prove that each archive contains complete dark/white references or usable wavelength calibration.

## Biological design, labels, and time information

- **Crop / tissue:** Tomato, cultivar *Encore*; tomato leaves are the described target. **High** confidence from the DataCite abstract and prior README audit.
- **Pathogen:** *Alternaria protenta*, with isolates `028` and `065`; controls are marked `K` in the metadata's combined `plant` field. **High** confidence from the prior README/TSV audit.
- **Metadata structure:** 1,000 observation rows, nine fields: `image_id`, `trial`, `plant`, `leaf`, `part`, `date`, `imaging_distance`, `integration_time`, and `weather`. **High** confidence based on prior direct inspection recorded in Phase F1.
- **Plants / trials:** 13 distinct plant identifiers across five trials: five plants per isolate and three controls. The `plant` value combines isolate/control and plant identifier; it must be parsed without losing either component. **High** confidence from the prior TSV audit.
- **Cube-to-plant mapping:** The three public cubes map to three distinct plants, all in trial 4: `1797.npz` → `065/I` (leaf 2, part G, 2025-07-07); `1827.npz` → `028/IV` (leaf 2, part 2, 2025-07-10); `1855.npz` → `028/II` (leaf 1, part 8, 2025-07-14). **High** confidence from the prior TSV audit; not re-read in F2.2.
- **Replicates:** Plant identifiers are available in the metadata, but the available public cube subset has only one cube from each of three plants. The full 13-plant metadata does not make unavailable cube data available.
- **Labels:** Isolate/control grouping is present in the combined plant identifier. No cube-linked laboratory assay, molecular identification result, or per-sample diagnostic verification was established by the reviewed materials. These are inoculation/group labels, not independently verified disease ground truth for each cube.
- **Severity / visual annotation:** No numeric disease severity or sample-linked lesion annotation was identified in the reviewed record, README, or metadata description. The RGB archive was not opened.
- **Acquisition dates / longitudinal observations:** The dataset describes repeated observations over several weeks. The metadata includes dates and repeated plant/leaf/part records, and DataCite records collection dates from 2025-04-11 to 2025-08-28. This is **metadata-level longitudinal coverage**; the three public HSI cubes are only three single listed captures and do not supply a usable spectral time series.

Thus, the three public cubes cannot support an infected-versus-control evaluation: all three metadata-mapped cubes are from inoculated plants, and no public cube maps to a control. They also cannot support a valid isolate-level train/test evaluation: there is one public plant for isolate 065 and two for isolate 028, all in trial 4. Do not count pixels, leaves, metadata rows, or repeated measurements as independent plants.

## Spectral, instrument, and calibration assessment

| Property | Evidence and limitation | Confidence |
|---|---|---|
| Listed cube format | Three files have `.npz` extensions. Their actual internal keys/arrays were not opened. | High for listing; low for contents |
| Dimensions / dtype | The prior README audit reports a calibrated-cube layout of `512 x 512 x 204`, `float16`, matching the existing project cube convention. F2.2 did not verify these properties against the NPZ files. | Medium |
| Spectral bands | 204 bands are reported by the prior README audit. | Medium |
| Wavelength vector / range | The README says raw camera headers contain wavelength information and identifies RGB anchors at bands 70/53/19 as approximately 598.60/548.55/449.35 nm. No 204-element vector or range was verified for these cubes. The three RGB anchors do not determine the full spectral axis. | Low for full axis |
| Sensor / illumination | Prior README audit describes Specim IQ, greenhouse natural sunlight, a black background, and white references. Same sensor family as the existing dataset is a useful technical similarity, not proof of identical acquisition response. | Medium |
| Calibration | The README describes NPZ files as calibrated cubes and says raw captures/references are available. F2.2 did not inspect any NPZ, ENVI header, dark/white capture, or calibration formula. Do not call values calibrated reflectance or assume that calibration can be reproduced. | Medium for source claim; low for verified calibration |
| Units / metadata consistency | Phase F1 documented conflicting README and metadata interpretations for imaging distance (README summary 13–48 mm versus metadata values with schema units of cm) and integration time (README 15–100 s versus metadata schema and values reported in ms, including values outside that stated range). Resolve with authors before using these fields. | High that prior audit recorded conflict; unresolved |

The existing pipeline is source-specific: [preprocess_hyperspectral.py](../src/data/preprocess_hyperspectral.py) enforces 204 bands and loads the single `2436` wavelength vector; [extract_spectral_features.py](../src/data/extract_spectral_features.py) assumes its current project cube/ROI schema and labels summaries as reflectance. The same shape and camera do not make it safe to reuse the 2436 wavelengths or reflectance interpretation for Alternaria. A future adapter must preserve source DOI, cube ID, trial, plant, isolate/control, leaf/part, date, wavelength provenance, and calibration status; load this source in a separate namespace; validate NPZ keys/shape/dtype; and prevent the existing 2436 wavelength vector from being attached by default.

## Compatibility with TerraSpectra and scientific uses

| Evaluation dimension | Assessment |
|---|---|
| Crop and pathogen | Same tomato crop and reported cultivar *Encore* as TerraSpectra; pathogen *A. protenta* is different from the existing *B. cinerea*/*B. pseudocinerea*. Keep pathogen and experiment labels distinct. |
| Cube shape / pipeline | Source documentation reports the existing `512 x 512 x 204` convention, but F2.2 did not inspect cube bytes. A separate input/metadata adapter is required; the current pipeline is tied to an existing image ID and wavelength vector. |
| Bands / wavelength | Same reported 204-band count, but no verified per-cube wavelength vector/range. Band-count equality is insufficient for wavelength alignment or band-wise comparisons. |
| Calibration | Source-described calibration only; no per-cube references, conversion equation, units, or radiometric compatibility verified. Do not call calibrated reflectance. |
| Labels / independence | The metadata gives 13 plant identifiers, but only three plants have publicly listed cube files. Class labels derive from the inoculation/control grouping and are not sample-linked laboratory confirmation. A balanced biological split is impossible on the public cube subset. |
| Preprocessing / features | Existing preprocessing may be structurally reusable only after source-specific loading, wavelength validation, calibration-status handling, and metadata normalization. Existing feature plots and reflectance labels are not suitable as-is. |
| Exploratory analysis | **Potentially suitable after** validating the three cubes and their wavelength/calibration metadata, for descriptive, source-separated exploration with the plant as the unit. The three-cube public subset remains highly limited and cannot establish generalizable disease differences. |
| Classification | **Not supported for valid train/test evaluation** by the public cube subset. All three mapped cubes are inoculated samples, with no public control cube; isolate 065 has only one public plant. Obtain additional independent cubes and verify labels before designing classification. |
| Forecasting | **Not supported.** Metadata dates and repeated rows are not a spectral longitudinal cube series; no forecast target or sample-linked severity series is established. |
| Cross-source pooling | **Not justified.** Do not combine Alternaria with Botrytis; a multi-pathogen protocol would require a distinct scientific question, verified per-source acquisition/calibration, and plant/trial-grouped evaluation. |

### Required adapter and validation before any future integration

1. If acquisition is approved, begin with the three listed NPZ files (201,798,652 bytes total), not the raw archives. Validate exact arrays, NPZ keys, dimensions, dtype, finite values, and checksums without overwriting existing files.
2. Obtain and verify each cube's wavelength vector, sensor header, band ordering, bad-band treatment, calibration formula, and units. Do not infer the full wavelength axis from RGB anchor bands.
3. If wavelength/calibration cannot be resolved from NPZ metadata, separately request approval before downloading the three raw ZIP files (145,442,225 bytes total); inspect their contents and reference/header association. This is not authorization to download.
4. Normalize `trial` and the combined `plant` field with an explicit, reversible mapping; retain isolate/control identity and the independent plant key.
5. Request additional cube files if classification or time-series research is intended. Confirm per-cube plant/leaf/date mapping, actual independent plant count, control representation, per-sample pathogen verification, disease severity, and repeated-capture structure.
6. Only then define a source-separated, plant-grouped analysis plan. Keep all leaves, parts, and dates for a plant in one partition. Do not report predictive performance from three public cubes.

## Dataset decision matrix

| Dataset | Crop / pathogen | Data availability | Spectral metadata | Calibration status | Biological samples | Label quality | Time-series availability | Main limitations | Recommended use |
|---|---|---|---|---|---|---|---|---|---|
| Existing TerraSpectra Botrytis, DataverseLV `MPCTZC` | Tomato; *B. cinerea*, *B. pseudocinerea*, control | 904 metadata rows; 3 local example cubes; full set on request per README | 204 bands; wavelength vector verified only for 2436 (397.32–1003.58 nm) | Only 2436 has local header/references; exact supplied-NPZ calibration reconstruction remains uncertain; 2973/3079 wavelength metadata unavailable | 49 plants in source metadata; 3 local cubes are distinct *B. pseudocinerea* plants | Metadata pathogen/control labels; no severity endpoint in reviewed metadata | Repeated observations over 34 dates; dates are not documented DAI/severity | 901 cubes absent locally; heterogeneous source calibration; repeated organs/dates; not a new independent dataset | Existing source-specific baseline and descriptive analysis; preserve plant grouping |
| Zenodo Botrytis/Healthy, `10.5281/zenodo.15800414` | Tomato; filename-labeled *B. cinerea* and healthy | 16 acquired MAT files (8/class), 16 verified; 12 unique numeric arrays due to 4 exact healthy duplicate pairs | Verified shape `140 x 280 x 550`, float64; no wavelength vector; paper reports 400–950 nm | Per-file calibration/reference mapping unresolved; unexplained Botrytis 0–4095 vs healthy <1 scales | No verified plant IDs; 16 files and 12 unique arrays are not plant counts | Filename/inoculation grouping only; no per-file assay or severity | Variable names show day tokens 1/3/5/7 but file mapping unverified; paper reports days 1/3/5/7/9/11 | Duplicate healthy arrays, class scale mismatch, no independent plant mapping or wavelength vector, different sensor/cultivar/setup | Keep isolated for provenance work; Phase F3 remains NO-GO |
| Alternaria, DataverseLV `MODVMZ` | Tomato, *Encore*; *A. protenta* isolates 028/065 and control | 9 listed files; 3 NPZ cubes (~202 MB), metadata/readme, RGB ZIP, 3 raw ZIPs; none downloaded in F2.2 | 204 bands reported; full wavelength vector/range not verified; RGB anchors only | README calls cubes calibrated, but per-cube calibration and reflectance units not independently verified | 13 plants in 1,000 metadata rows/five trials; 3 public cubes map to 3 distinct plants in trial 4 | Isolate/control grouping; per-cube lab verification and severity not established | Metadata has repeated dated observations; only 3 public spectral cube captures, not a spectral time series | Inadequate public cube count/class balance for ML split; wavelength/calibration and README-unit conflicts; distinct pathogen | Conditional source-separated exploratory use after cube/wavelength/calibration verification; request more data for ML |
| USDA Ag Data Commons bacterial leaf spot, `10.15482/USDA.ADC/26046328` | Tomato; *Xanthomonas perforans* | One public v2 ZIP, 15.4 GB; not downloaded or inspected | Paper reports two sensors: PIKA-L 300 bands (385.63–1027.18 nm) and PIKA-NIR320 168 bands (890.68–1719.81 nm); headers/cubes unverified | Paper reports dark/response correction and reference tile; archive-level calibration not inspected | Paper reports 36 images/228 leaves; independent plant count and file mapping unverified | Paper reports CFU/cm² and severity ratings; archive/sample joins unverified | Paper reports seven consecutive days; archive-level mapping unverified | Large archive; different sensor/ranges and bacterial disease; versioned archive and labels need verification | Separate bacterial methodological benchmark only after version/checksum and sample joins are verified |

Pixel counts and metadata observations are not used as biological sample counts in this matrix.

## Sources

URLs below were consulted or referenced on **2026-11-26**, unless identified as source material reviewed in the earlier Phase F1 audit.

1. DataverseLV DOI landing page: <https://doi.org/10.71782/DATA/MODVMZ> — canonical dataset entry; current fetch returned an access error.
2. DataverseLV official API: <https://dv.dataverse.lv/api/datasets/:persistentId/?persistentId=doi%3A10.71782%2FDATA%2FMODVMZ> — current fetch returned HTTP 503; successful access and file/README/TSV inspection are documented in Phase F1.
3. DataCite DOI metadata: <https://api.datacite.org/dois/10.71782/DATA/MODVMZ> — title, creators, publisher, dates, license, size/format lists, abstract, version, and empty `relatedIdentifiers`.
4. DataCite schema/metadata record for existing Botrytis source: <https://api.datacite.org/dois/10.71782/DATA/MPCTZC>.
5. Phase F1 source audit: [docs/phase_f1_dataset_source_audit.md](phase_f1_dataset_source_audit.md) — prior official Dataverse file list, README, metadata TSV, study structure, cube mapping, and unit conflicts.
6. Existing source inventory: [data/processed/reports/phase_f1_source_inventory.json](../data/processed/reports/phase_f1_source_inventory.json).
7. Existing baseline inventory: [data/processed/reports/dataset_inventory.json](../data/processed/reports/dataset_inventory.json) and [data/processed/reports/biological_sample_summary.json](../data/processed/reports/biological_sample_summary.json).
8. USDA Ag Data Commons source and associated paper links are recorded in [the Phase F1 source audit](phase_f1_dataset_source_audit.md#source-d---tomato-bacterial-leaf-spot-hsi). Data availability, spectra, samples, and methods in the matrix are paper/source reported, not archive-inspected in F2.2.
9. Zenodo source record and related paper/API evidence are recorded in [Phase F2](phase_f2_acquisition_validation.md) and [Phase F2.1](phase_f2_1_external_dataset_inspection.md).

## Final decision

**CONDITIONAL GO — suitable after clearly specified missing information or validation is resolved.**

The dataset is a plausible, source-separated future exploratory candidate because it concerns the same crop/cultivar and a related plant-disease domain, and the source metadata distinguishes plants, trials, isolates, dates, and controls. It is not currently suitable for direct pipeline integration or disease ML: cube internals, full wavelength axes, and calibration were not verified; only three cubes are public; one is a control; individual assay/severity ground truth is unavailable; and a valid biologically independent train/test split is not possible with the public cube subset. Resolve these gaps and obtain sufficient independent cubes before reconsidering ML. Keep the Alternaria and Botrytis experiments separate, make no forecasting claim, and leave Zenodo Phase F3 status unchanged.
