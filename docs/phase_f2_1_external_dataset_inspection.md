# TerraSpectra - Phase F2.1 External Dataset Inspection

- **Status:** Phase F2.1 scientific inspection complete
- **Source:** Zenodo DOI 10.5281/zenodo.15800414, record version 1
- **License:** CC BY 4.0
**F3 integration status:** NO-GO

## Executive summary

The reproducible inspection evaluated 16 of 16 MAT files.
It found 16 checksum matches and 0 checksum failures/missing files,
16 unambiguous numeric 3D candidates, and 12 unique numeric array contents.
There are 4 exact duplicate groups. Raw-sha256 immutability:
True.

## Inspection methodology

The script read the F2 manifest, resolved exact filenames beneath `data/raw/external/zenodo_15800414/`,
verified MD5/SHA-256, used `scipy.io.whosmat` before loading, loaded candidates one file at a time,
and hashed canonical shape/dtype/C-contiguous bytes. It did not modify raw MAT files or claim calibrated reflectance.

## File integrity

| Filename | Provisional class | MD5 | Dimensions | Dtype | Finite minimum | Finite maximum | Finite mean | Duplicate group |
|---|---|---|---|---|---:|---:|---:|---|
| Botrytis_cinerea_1.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2033.9652200501966 | DG-006 |
| Botrytis_cinerea_2.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 1956.4163843589956 | DG-008 |
| Botrytis_cinerea_3.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2005.5087686668785 | DG-009 |
| Botrytis_cinerea_4.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2049.027142663186 | DG-001 |
| Botrytis_cinerea_5.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 1973.4782802844704 | DG-012 |
| Botrytis_cinerea_6.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2026.7804496144713 | DG-011 |
| Botrytis_cinerea_7.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2112.1520839883024 | DG-002 |
| Botrytis_cinerea_8.mat | Botrytis cinerea | match | [140, 280, 550] | float64 | 0.0 | 4095.0 | 2038.9101414658026 | DG-007 |
| Healthy_1.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7944624794682191 | 0.23539874592476537 | DG-003 |
| Healthy_2.mat | Healthy control | match | [140, 280, 550] | float64 | 8.736218593255994e-05 | 0.7619459339856509 | 0.22414448218893127 | DG-005 |
| Healthy_3.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7792823635349214 | 0.23599498108825842 | DG-004 |
| Healthy_4.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7478300691966614 | 0.21635130300287853 | DG-010 |
| Healthy_5.mat | Healthy control | match | [140, 280, 550] | float64 | 8.736218593255994e-05 | 0.7619459339856509 | 0.22414448218893127 | DG-005 |
| Healthy_6.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7944624794682191 | 0.23539874592476537 | DG-003 |
| Healthy_7.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7792823635349214 | 0.23599498108825842 | DG-004 |
| Healthy_8.mat | Healthy control | match | [140, 280, 550] | float64 | 0.0 | 0.7478300691966614 | 0.21635130300287853 | DG-010 |

## MATLAB structure

All candidate status, MATLAB variable names, dimensions, and types are retained in the machine-readable JSON report.
A third-dimension value of 550 is not treated as a verified wavelength axis. Per-file wavelength vectors are absent.

## Exact duplicate findings

| Group | Filenames | Cube hash |
|---|---|---|
| DG-003 | Healthy_1.mat, Healthy_6.mat | 4ccb5b89b02b095f3bbb17cab36a3a2373ea6a777ea3b9e9ac4f1889b6c0dac8 |
| DG-004 | Healthy_3.mat, Healthy_7.mat | 59374bfdf97e68398220ba08bed530cf3b95623ca9b87ab6da3519caa09e331e |
| DG-005 | Healthy_2.mat, Healthy_5.mat | 7956f8b1cbc61bf5bf6b3bdc3ac9f32f9a31c7cc0b06fe7d04fbc0378b5cfcf0 |
| DG-010 | Healthy_4.mat, Healthy_8.mat | cd40fc386e90afcec5ac209c0f7c2d46d938002063b2b28bcdaf008b463e5bbd |

Exact duplicate groups are array-content duplicates only. They do not establish biological repetitions or independent plants.

## Per-band inspection

The source record and accompanying MATLAB script document 550 bands, while no MAT file includes a wavelength vector.
Accordingly, per-file band profiles were generated for the final axis as **provisional 550-band profiles**, with zero-based
indices and no wavelength or calibration claims. CSV units are array units, and no wavelength range is inferred.

## Class-wise numerical comparison

| Filename-derived provisional class | File count | Unique array count | Finite min/max summary | Finite mean summary | Finite std summary |
|---|---:|---:|---|---|---|
| Botrytis cinerea | 8 | 8 | min=0.0; max=4095.0 | {'min': 1956.4163843589956, 'mean': 2024.529808886538, 'max': 2112.1520839883024} | {'min': 1010.5780241894802, 'mean': 1045.5836750620826, 'max': 1091.5354252959505} |
| Healthy control | 8 | 4 | min=0.0; max=0.7944624794682191 | {'min': 0.21635130300287853, 'mean': 0.2279723780512084, 'max': 0.23599498108825842} | {'min': 0.10645805132263876, 'mean': 0.1261935719815266, 'max': 0.137774936511824} |

The table above distinguishes files from unique array contents. The filename-based class labels are provisional:
the BOTRYTIS/healthy labels do not establish verified pathology or control ground truth.

## Existing-versus-external compatibility matrix

| Dimension | Existing TerraSpectra Latvia | External Zenodo tomato HSI |
|---|---|---|
| Crop | Tomato, cultivar Encore F1 | Tomato, Solanum lycopersicum var. 4921 |
| Pathogen | B. cinerea / B. pseudocinerea / control | Filename-derived B. cinerea / healthy |
| Source geography | Latvia | Gorgan, Iran |
| Sensor/instrument | Specim IQ | Hyspim HSI-Vis_Nir-15fps, paper-reported |
| Acquisition protocol | Greenhouse natural sunlight; verified partially | Laboratory halogen/dark-chamber details in paper; per-file products unavailable |
| Array dimensions | 512 x 512 x 204 local NPZ | 140 x 280 x 550 candidate MAT arrays |
| Number of bands | 204 | 550 source-reported and final-axis shape, no per-file vector |
| Wavelength range | 397.32-1003.58 nm verified only for 2436 | 400-950 nm paper-reported; file-verification unavailable |
| Wavelength vector | Available only for 2436 | Unavailable |
| Radiometric calibration | 2436 uncertain in exact reconstruction; 2973/3079 unresolved | Unresolved |
| Numerical scale | float16 NPZ; repository values require source-specific interpretation | Botrytis 0-4095; healthy below 1; scale difference observed |
| Biological sample identity | Metadata-derived 49 plants across 904 records | No verified plant/leaf/scan IDs |
| Independent sample count | 49 plants in metadata; only 3 local cubes | 16 source files; 12 recomputed unique arrays; 0 verified plants |
| Healthy/control labels | Metadata control class; caveats remain | Filename-derived provisional controls |
| Acquisition dates | Verified in metadata | Unverified; variable day tokens are not sample mapping |
| Disease timeline | Metadata repeated observations, severity absent | Paper report differs on days; release mapping absent |
| Disease severity | Unavailable | Unavailable |
| Duplicate arrays | Separate from this inspection | Exact duplicate array groups recomputed |
| License | CC BY 4.0 | CC BY 4.0 |
| Integration status | Existing source still constrained | Suitable only for separate exploratory analysis. |

## Scientific limitations

- 16 source files are not 16 verified biological samples.
- 12 unique array contents are not 12 verified plants.
- Day variable names are not proven time points or plant identities.
- Numeric arrays are not called calibrated reflectance.
- Values must not be treated as cross-dataset spectral measurements without calibration evidence.

## Final integration recommendation

**Suitable only for separate exploratory analysis.** Preserve the current F3 NO-GO status.
Do not merge or train pooled models until sample identity, calibration, wavelength, and label provenance are resolved.

## Reproduction

Run from the repository root:

```powershell
python src/data/inspect_external_zenodo_dataset.py
pytest tests/test_external_dataset_inspection.py
```
