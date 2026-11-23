# Phase F2 - Zenodo Acquisition and Technical Validation

**Record:** [Javidan Tomato Disease Dataset HSI, DOI 10.5281/zenodo.15800414](https://doi.org/10.5281/zenodo.15800414)

**Record version:** 1

**Scope:** Acquire only the eight `Botrytis_cinerea_*.mat` and eight `Healthy_*.mat` candidates selected in Phase F1, and inspect them technically. No model was trained, and no existing TerraSpectra application, processing code, PCA output, or source dataset was changed.

## Executive result

All 16 exact candidates listed in the official Zenodo record were downloaded to `data/raw/external/zenodo_15800414/` and verified against the record's declared byte size and MD5 checksum. Their total is **2,254,793,632 bytes**. The first transfer attempt stopped after a connection reset at `Healthy_7.mat`; its partial file was retained, resumed, and verified. No selected file remains partial, and no other disease classes were downloaded.

All 16 MAT files contain one numeric 3D array of shape `140 x 280 x 550` (`float64`) and are plausible HSI cube candidates. They have no embedded wavelength vector. The Botrytis-named arrays have values from 0 to 4095, while healthy arrays have values below 0.8. The files therefore cannot be assumed to share the same radiometric encoding or to contain calibrated reflectance.

The eight Botrytis arrays have distinct numeric contents. The eight healthy files contain only **four unique arrays**: four pairs are exactly identical after loading, despite different file and day-variable names. No independent biological plant, leaf, scan, replicate, or acquisition date can be verified from the released files or record. Thus the package contains 16 files, 12 unique numeric arrays, and **zero verified independent plant identities**. These counts do not imply that there are zero plants in the experiment.

**Integration recommendation: NO-GO.** Keep these files isolated. Request per-file sample/plant mapping, clarification of the exact duplicate healthy arrays and inconsistent class scales, wavelength calibration, and calibration/reference details before any scientific comparison or integration.

## Acquisition procedure and official manifest

The official [Zenodo record API](https://zenodo.org/api/records/15800414) was saved unmodified as `data/raw/external/zenodo_15800414/source_metadata/zenodo_record.json`. Its version 1 metadata identifies open access and **CC BY 4.0**. Selected filenames, file IDs, content URLs, byte sizes, and MD5 values below come from that API response. Downloaded files were individually hashed and checked against both declared size and MD5. The successful resume of `Healthy_7.mat` used the retained partial file; the final checksum matches the official manifest.

| Class | Filename | File ID | Bytes | Official MD5 | Result |
|---|---|---|---:|---|---|
| Botrytis cinerea | `Botrytis_cinerea_1.mat` | `bbc21820-8d49-49d3-abc7-5a8a61784324` | 121,763,573 | `8b57769935247579fbfad0b9a87f1aae` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_2.mat` | `3d01b608-c6dc-4034-93cb-05a8c1a6f0d1` | 122,347,407 | `1aa3e80b42f90c9170f7042e7f8f38bc` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_3.mat` | `1277df58-0a6d-42aa-9901-baaaebb73a74` | 122,233,114 | `3b3becff259743a2b3f23abd5011afdc` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_4.mat` | `5b0b85b3-3a0f-4de0-ba89-e8c083cad313` | 120,454,561 | `ae673ee5f627f244aedab5506a1243ec` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_5.mat` | `e81c066a-d620-4246-92c0-b5041001ed60` | 122,270,326 | `35490f2c842f7fb44ca017ee919d00a9` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_6.mat` | `eaa2d569-e201-4035-b237-3d6b1c3b5eb8` | 120,628,089 | `2aa2656828c4aef6fae65eb550a1e5b5` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_7.mat` | `2401285c-7374-48ec-b9b7-1433be9a0984` | 118,958,903 | `3b32de55cd99646c4eb533fb8d9e0dda` | Verified |
| Botrytis cinerea | `Botrytis_cinerea_8.mat` | `c9e21f0a-a8a1-4a2c-bbe6-6c7addc7892a` | 121,514,703 | `6d18e767fae987686266aa231d3ada7f` | Verified |
| Healthy control | `Healthy_1.mat` | `7a7a12fb-2f8c-4a6b-8822-fa6c345e9cbd` | 160,689,583 | `e55b73666d43cd2b6f38fa2eaf10d532` | Verified |
| Healthy control | `Healthy_2.mat` | `c25296ca-2ad3-479b-9e97-6481c0a2ec94` | 160,560,820 | `c5bc67afa8ce02c2becccf87a3925508` | Verified |
| Healthy control | `Healthy_3.mat` | `0b6eb4a3-b124-4025-8b62-654abd6ace9d` | 160,858,502 | `8fab75879297658d645c15ba0be6ddfc` | Verified |
| Healthy control | `Healthy_4.mat` | `be30cf32-50e8-489d-95fe-64df1ef990d4` | 160,202,571 | `571e5aca948484b588df402e52d4b930` | Verified |
| Healthy control | `Healthy_5.mat` | `80125984-89a0-45cf-98c6-e81aef3b15eb` | 160,560,821 | `e8ba3484d8c23dbdc28799bc85f06a8b` | Verified |
| Healthy control | `Healthy_6.mat` | `cfe27a6a-54c1-4674-bb01-0bc66dfab2e3` | 160,689,586 | `90201764ecd5a4871d3b364063afad63` | Verified |
| Healthy control | `Healthy_7.mat` | `f0fd0ee8-29fd-4274-a944-31149cf2f99e` | 160,858,503 | `3f8aec5cd0f61e644ee96042fbc21b83` | Verified after resume |
| Healthy control | `Healthy_8.mat` | `de3b16b4-f2bc-4e54-b444-e491c73989a0` | 160,202,570 | `d75a9a574ebc3596aa8f97fee2b894fa` | Verified |

The acquisition is organized as:

- `data/raw/external/zenodo_15800414/botrytis_cinerea/`
- `data/raw/external/zenodo_15800414/healthy/`
- `data/raw/external/zenodo_15800414/source_metadata/`

The saved record metadata is the original API response; `acquisition_progress.json` records final verified states. The machine-readable per-file results are in [the Phase F2 manifest](../data/processed/reports/phase_f2_acquisition_manifest.json).

## MAT inspection results

MAT files were inspected sequentially with SciPy's MATLAB v5 reader (`whosmat` and `loadmat`); arrays were released before the next file was loaded. Each inspected header identifies a MATLAB 5.0 MAT-file. Each file has one `double` / `float64` numeric variable, shape `140 x 280 x 550`, with 21,560,000 finite values. The third dimension is consistent with the record's 550 stated bands, but no file contains a wavelength vector; **550 bands does not verify a 400-950 nm per-file wavelength calibration**. The release does not establish whether the first two dimensions are rows/columns or their physical spatial resolution.

`Mean` and population standard deviation below are over all array elements. All 16 files have zero NaNs, zero Infs, and 21,560,000 finite values.

| File | MAT variable | File min | File max | Mean | Std. dev. | Array comparison |
|---|---|---:|---:|---:|---:|---|
| `Botrytis_cinerea_1.mat` | `Day_one_1` | 0 | 4095 | 2033.965220 | 1044.025485 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_2.mat` | `Day_one_2` | 0 | 4095 | 1956.416384 | 1010.578024 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_3.mat` | `Day_three_1` | 0 | 4095 | 2005.508769 | 1032.073702 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_4.mat` | `Day_three_2` | 0 | 4095 | 2049.027143 | 1061.787149 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_5.mat` | `Day_five_1` | 0 | 4095 | 1973.478280 | 1019.014220 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_6.mat` | `Day_five_2` | 0 | 4095 | 2026.780450 | 1053.619276 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_7.mat` | `Day_seven_1` | 0 | 4095 | 2112.152084 | 1091.535425 | Unique among inspected Botrytis arrays |
| `Botrytis_cinerea_8.mat` | `Day_seven_2` | 0 | 4095 | 2038.910141 | 1052.036119 | Unique among inspected Botrytis arrays |
| `Healthy_1.mat` | `Day_one_1` | 0 | 0.794462 | 0.235399 | 0.136368 | Exactly identical array to `Healthy_6.mat` |
| `Healthy_2.mat` | `Day_one_2` | 0.000087 | 0.761946 | 0.224144 | 0.124173 | Exactly identical array to `Healthy_5.mat` |
| `Healthy_3.mat` | `Day_three_1` | 0 | 0.779282 | 0.235995 | 0.137775 | Exactly identical array to `Healthy_7.mat` |
| `Healthy_4.mat` | `Day_three_2` | 0 | 0.747830 | 0.216351 | 0.106458 | Exactly identical array to `Healthy_8.mat` |
| `Healthy_5.mat` | `Day_five_1` | 0.000087 | 0.761946 | 0.224144 | 0.124173 | Exactly identical array to `Healthy_2.mat` |
| `Healthy_6.mat` | `Day_five_2` | 0 | 0.794462 | 0.235399 | 0.136368 | Exactly identical array to `Healthy_1.mat` |
| `Healthy_7.mat` | `Day_seven_1` | 0 | 0.779282 | 0.235995 | 0.137775 | Exactly identical array to `Healthy_3.mat` |
| `Healthy_8.mat` | `Day_seven_2` | 0 | 0.747830 | 0.216351 | 0.106458 | Exactly identical array to `Healthy_4.mat` |

Array equality was checked with SHA-256 fingerprints of the loaded numeric arrays. These four healthy pairs are exact data duplicates, not merely arrays with matching summary statistics. This makes their distinct filenames and `Day_*` variable tokens insufficient evidence of independent scans or time points. The resulting 12 unique array contents (eight Botrytis, four healthy) are a technical count only, not a biological sample count. Every file is a plausible cube candidate by its 3D numeric structure; none is declared a validated raw cube or calibrated-reflectance cube.

The class-level value ranges are a critical issue: every Botrytis-named array reaches 4095, while every Healthy array is below 1. The source metadata does not explain this difference. It could reflect different processing or encodings, but this inspection cannot determine the cause. No clipping, normalization, band removal, calibration, or value conversion was performed.

## Biological identity and labels

The MAT variable names encode `Day_one`, `Day_three`, `Day_five`, and `Day_seven`, each with suffix `_1` or `_2`. This appears consistent with the Zenodo description's days 1, 3, 5, and 7, but neither the numeric suffix nor the day token is linked to a plant, leaf, scan, acquisition date, or replicate in the released metadata. These tokens are recorded as filename/variable evidence only; they are not treated as verified biological identifiers.

| Measure | Botrytis class | Healthy control | Interpretation |
|---|---:|---:|---|
| Downloaded files | 8 | 8 | Verified against the official version 1 file manifest |
| Distinct numeric arrays | 8 | 4 | Four healthy pairs are exactly duplicated |
| Verified independent plants | Unknown (0 verified) | Unknown (0 verified) | No file-to-plant mapping; do not infer independence from filenames |
| Verified leaves, scans, or replicates | Unknown | Unknown | Not identified in the data files or record |
| Acquisition dates | Unknown | Unknown | MAT header creation timestamps are not evidence of acquisition dates |
| Variable-name day tokens | Days 1, 3, 5, 7; two tokens per day | Days 1, 3, 5, 7; two tokens per day | Not author-confirmed as a per-file time-point join |

The related paper reports tomato cultivar *Solanum lycopersicum* var. 4921, 25 pots per fungal class and 25 control pots, inoculation with a 5 x 10^6 spores/mL suspension, and imaging on days 1, 3, 5, 7, 9, and 11. It reports pathogen isolation, morphological identification, and pathogenicity tests. These are **paper-reported study methods**, not evidence that each released MAT array maps to a distinct pot or has an individual laboratory result. The record's shorter days 1, 3, 5, and 7 description and the observed exact healthy duplicates need reconciliation with the authors.

The labels are based on filenames and the experiment's inoculation/control groups; no sample-linked label audit or per-file biological ground truth is included. This may support a provisional class grouping for a separately governed investigation, but it does not establish disease severity or a verified label for each cube.

## Sensor, spectral, and calibration comparison

The paper reports a Hyspim HSI-Vis_Nir-15fps camera, 400-950 nm range, two halogen sources, a dark chamber/background, 25 cm camera distance, and a white paper reference captured every 10 minutes. It reports imaging under laboratory conditions, with plants cultivated in a greenhouse in Gorgan, Iran, at 20 +/- 2 C and 80% humidity. Zenodo describes the dataset as 550-band HSI.

Those details do not supply a calibration vector or calibration products for each released MAT file. The paper's white-reference procedure is not enough to reconstruct per-file reflectance from these arrays without the applicable raw/reference data, formulas, and sample linkage. The arrays' differing class-level numeric ranges make radiometric comparability especially uncertain. Therefore:

- Sensor range and model are paper-reported, not independently verified from MAT headers.
- The 550-sized axis is identifiable from the array shape and record description; exact wavelengths, sampling interval, axis orientation, and per-cube wavelength calibration are unavailable.
- Spatial shape is `140 x 280`, but physical pixel size, spatial resolution, and acquisition geometry in the arrays are unverified.
- No MAT file contains a wavelength vector or dark/white reference array.
- Values are not called reflectance; no processing or calibration was applied.
- Do not transfer TerraSpectra's 204-band wavelengths from image 2436 to this dataset. TerraSpectra images 2973 and 3079 also lack verified wavelength calibration.

The existing TerraSpectra Botrytis cubes are `512 x 512 x 204` float16, and only image 2436 has a verified wavelength vector (~397.32-1003.58 nm). The Zenodo candidates differ in array dimensions, dtype, band count, reported spectral range, sensor, cultivar, location, lighting, and unresolved numeric encoding/calibration. A common tomato crop or Botrytis class does not make the measurements directly comparable.

## License, attribution, and outstanding questions

Zenodo version 1 identifies an open record under **CC BY 4.0**. Cite and attribute Seyed Mohamad Javidan and the dataset DOI, and retain license/attribution information in any permitted redistribution. This dataset license is separate from the related paper's terms.

Before any integration, request clarification from the dataset author on:

1. Plant, leaf, scan, and replicate IDs for each filename; whether the files represent distinct plants, repeated measurements, or time points.
2. The exact healthy array duplicates across `Healthy_1`/`Healthy_6`, `Healthy_2`/`Healthy_5`, `Healthy_3`/`Healthy_7`, and `Healthy_4`/`Healthy_8`, and how those pairs relate to their conflicting day tokens.
3. Why Botrytis-named values are 0-4095 while healthy values are below 1; whether arrays are raw digital numbers, reflectance, or differently processed exports.
4. Per-file wavelength vectors, sensor calibration/metadata, band order, and any excluded or bad bands.
5. Dark/white reference files and the exact reflectance calibration method, including whether calibration is already applied to the MAT arrays.
6. File-to-inoculation/time-point mapping, disease-severity observations, and any per-sample lab verification.
7. Whether the reported days 9 and 11 exist in the released data but are omitted from this selected file set, or are absent from this release.

## Integration decision

**NO-GO for Phase F3 integration or pooled training at this time.** Retain the acquired files as an isolated, checksum-verified external dataset and use them only for further provenance investigation. The MAT structure confirms cube-shaped candidates, but there are no verified independent plants, no wavelength calibration in the files, no per-file calibration provenance, exact healthy-array duplicates, and an unexplained orders-of-magnitude numeric scale difference between classes. Do not combine these arrays with TerraSpectra cubes, infer sample independence, or treat array values as calibrated reflectance until the unresolved questions above are answered and validated.
