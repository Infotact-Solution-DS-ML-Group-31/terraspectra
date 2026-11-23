# Phase F1 - Dataset Source and Availability Audit

**Audit date:** 2026-11-23
**Scope:** Publicly listed tomato hyperspectral disease sources, access, licensing, sample independence, and scientific compatibility. No large cubes, raw-camera archives, or multi-gigabyte packages were downloaded. No application, processing code, PCA output, or existing data files were changed.

## Executive summary

- The existing Botrytis source is publicly listed with 904 metadata observations and three example NPZ cubes. This matches the repository's existing inventory. The full image set is not included in the repository or public listing; the README says the full data are available on request.
- DataverseLV's related *Alternaria protenta* experiment has 1,000 metadata observations but only three public NPZ cubes. The metadata and README identify 13 plants across five trials. The three cubes map to three different plants, not three repeat images of one plant. The other observations are not downloadable cubes in this record.
- The Zenodo fungal record lists 40 numbered, class-named MATLAB image files (eight for each of four fungi and healthy controls), five feature MAT files, and two MATLAB scripts. Its API and DataCite metadata verify CC BY 4.0. The image MAT file structure and whether the eight class files map to eight independent plants were not verified; they must not be counted as eight biological replicates.
- A second fungal tomato dataset therefore appears to offer eight additional *Botrytis cinerea*-named MAT image files, but no plant-level linkage or sensor calibration metadata sufficient for direct merging. The similarly named Alternaria dataset contains no Botrytis samples.
- The USDA Ag Data Commons bacterial-leaf-spot source is publicly downloadable as one 15.4 GB ZIP (latest page version 2). The research article reports VIS-NIR and NIR hyperspectral imaging, pathogen-population measurements, and daily progression. It is a useful external methodological benchmark, not a fungal or Botrytis training source.
- No new source is rated directly compatible for merging with the existing cubes. **Conditional GO for a limited Phase F2 acquisition and provenance check; NO-GO for merging or model training until plant IDs, time points, spectral axes, calibration, and sample-level labels are validated.**

## Method and evidence

### Sources and queries

Primary repository records and APIs:

- Existing Botrytis dataset: [DataverseLV DOI 10.71782/DATA/MPCTZC](https://doi.org/10.71782/DATA/MPCTZC); [Dataverse API record](https://dv.dataverse.lv/api/datasets/:persistentId/?persistentId=doi%3A10.71782%2FDATA%2FMPCTZC); [DataCite metadata](https://api.datacite.org/dois/10.71782%2FDATA%2FMPCTZC).
- Alternaria dataset: [DataverseLV DOI 10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ); [Dataverse API record](https://dv.dataverse.lv/api/datasets/:persistentId/?persistentId=doi%3A10.71782%2FDATA%2FMODVMZ); [DataCite metadata](https://api.datacite.org/dois/10.71782%2FDATA%2FMODVMZ).
- Fungal HSI dataset: [Zenodo DOI 10.5281/zenodo.15800414](https://doi.org/10.5281/zenodo.15800414); [Zenodo record API](https://zenodo.org/api/records/15800414); [Zenodo file manifest](https://zenodo.org/api/records/15800414/files); [DataCite metadata](https://api.datacite.org/dois/10.5281%2Fzenodo.15800414); [related Heliyon paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462246/).
- Bacterial leaf spot: [Ag Data Commons landing page](https://data.nal.usda.gov/dataset/early-detection-bacterial-spot-disease-tomato-hyperspectral-imaging); [current Figshare/Ag Data Commons record](https://agdatacommons.nal.usda.gov/articles/dataset/Data_from_b_Hyperspectral_Imaging_Analysis_for_Early_Detection_of_Tomato_Bacterial_Leaf_Spot_Disease_b_/26046328); [DataCite version 1 metadata](https://api.datacite.org/dois/10.15482%2Fusda.adc%2F26046328.v1); [related Scientific Reports article](https://www.nature.com/articles/s41598-024-78650-6).

The two Dataverse record pages and their `dataverse.lv` API host returned access errors in the browser fetcher. The records were successfully read from the official `dv.dataverse.lv` API. Only the small metadata tables and READMEs were downloaded to temporary storage outside the repository; the temporary files were removed after inspection. Zenodo, DataCite, Ag Data Commons, OpenAlex, and the cited papers were used for discovery and source verification. Search terms included tomato hyperspectral disease, tomato leaf hyperspectral disease, and tomato hyperspectral dataset. RGB-only PlantVillage material was excluded.

This is a bounded repository and literature search, not an exhaustive systematic review. A Zenodo search hit for tomato-sepal hyperspectral segmentation was screened: [Zenodo 10.5281/zenodo.4896828](https://zenodo.org/records/4896828) contains a conference-abstract PDF only, not a cube dataset. A further relevant point-spectroscopy record is assessed below.

### Counting rules

- An observation row, image file, scan, leaf, pixel, or band is not automatically an independent plant.
- "Public cube count" below means a publicly listed, cube/image-data artifact. For the Zenodo MAT files it is a candidate count inferred from the class-named files and the authors' small MATLAB script; MAT contents were not opened.
- A reported count of leaves or experimental pots is not treated as an independent-plant count unless the source identifies distinct plants.
- No large HSI cubes, camera ZIP archives, or the 15.4 GB Ag Data Commons archive were downloaded.

## Existing project baseline

The current project inventory reports 904 source metadata records, 904 unique image IDs, three local NPZ cubes, and 901 cubes absent locally. The processed project metadata adds derived `plant_id`, `part_id`, and local-availability fields; the original public metadata table has nine columns. Repository analysis derives 49 biological plants from the experiment and finds all three local cubes belong to *B. pseudocinerea*. These counts agree with the Dataverse README and current file manifest.

The existing local cubes are 512 x 512 x 204 float16. Only image 2436 has a locally verified ENVI wavelength vector (397.32-1003.58 nm) and dark/white reference files. Do not copy its wavelengths to 2973 or 3079. The existing [wavelength calibration note](wavelength_calibration_status.md) and [calibration investigation](calibration_investigation.md) document unresolved processing provenance; the candidate reflectance reconstruction for 2436 correlated poorly with the supplied NPZ.

| Existing file | Public listing | Local project state / calibration evidence |
|---|---|---|
| `2436.npz` | Listed | Present; 204 bands; wavelength vector verified for this capture only; local raw/header/references available |
| `2973.npz` | Listed | Present; 204 bands; wavelength vector not locally verified |
| `3079.npz` | Listed | Present; 204 bands; wavelength vector not locally verified |
| Full set of 904 raw/cube observations | Not all listed | README says full dataset is available on request |

The current project files used for this comparison are [dataset_inventory.json](../data/processed/reports/dataset_inventory.json), [dataset_metadata_inventory.csv](../data/processed/reports/dataset_metadata_inventory.csv), [biological_sample_summary.json](../data/processed/reports/biological_sample_summary.json), and [dataset_suitability_assessment.md](dataset_suitability_assessment.md). These files were read only.

## Source A - Existing tomato Botrytis experiment

**Record title:** Hyperspectral imaging (HS) of tomato leaves inoculated with *Botrytis cinerea* and *Botrytis pseudocinerea*
**Repository/DOI:** DataverseLV, [10.71782/DATA/MPCTZC](https://doi.org/10.71782/DATA/MPCTZC)
**License:** CC BY 4.0, confirmed in the current README and DataCite record. Attribute the authors and cite the DOI.

### Current public file inventory

The current Dataverse API lists nine files. Sizes below are the API's byte counts.

| File | Bytes | Contents / status |
|---|---:|---|
| `metadata.tab` | 51,675 | 904 observations; 9 original metadata columns |
| `readme.md` | 5,450 | Methods, camera, sample identifiers, and license |
| `rgb.zip` | 251,976,113 | RGB images |
| `2436.npz` | 62,573,947 | Example calibrated cube |
| `2973.npz` | 67,688,775 | Example calibrated cube |
| `3079.npz` | 75,314,786 | Example calibrated cube |
| `2436.zip` | 38,979,396 | Example raw camera archive |
| `2973.zip` | 54,059,464 | Example raw camera archive |
| `3079.zip` | 54,165,719 | Example raw camera archive |

The canonical metadata filename is currently `metadata.tab` (TSV content), not `metadata.tsv`. The README states that only example raw captures and calibrated cubes are public due to storage limits; the complete 904-image set is available upon request.

### Biology and acquisition

- Crop/cultivar: tomato, *Encore F1*.
- Pathogens: *B. cinerea*, *B. pseudocinerea*, and uninfected control (`K`).
- Public metadata: `image_id`, `replicate`, `pathogen`, `sample`, `part`, `date`, `imaging_distance`, `integration_time`, `weather`. The processed local inventory derives `plant_id` from replicate/pathogen/sample.
- Public metadata spans 2025-12-10 through 2026-06-08, across 34 imaging dates and five replicates. The README says replicate 5 is incomplete. Repository analysis counts 49 plants from all observations.
- All three listed cubes map to distinct *B. pseudocinerea* plants: 2436 (replicate 1, sample 4, part 3/2, 2025-12-18); 2973 (replicate 3, sample 4, part 4/4, 2026-03-05); 3079 (replicate 4, sample 3, stem part ST-2, 2026-04-02). They are three separate image observations from three plants, not three time points of one plant.
- Acquisition: Specim IQ, natural greenhouse sunlight, black background, white reference in the image. README reports raw cubes as 512 x 204 x 512 uint16, reference captures as 204 x 512 uint16, and calibrated NPZ cubes as 512 x 512 x 204 float16. RGB uses bands 70/53/19, reported as 598.60/548.55/449.35 nm.
- Wavelength range is locally verified only for 2436 (397.32-1003.58 nm). Other two local NPZ files lack their headers and references. Public raw ZIPs are listed but were not opened in F1.
- Date, weather, camera distance, and integration time are recorded, but date is not a documented days-post-inoculation or severity label. Data have repeated organ observations per plant.

**Assessment:** Existing baseline, rating **A - Directly compatible** with itself. No additional biological samples are added by re-counting the existing three cubes.

## Source B - Tomato *Alternaria protenta* experiment

**Record title:** Hyperspectral imaging (HS) of tomato leaves inoculated with *Alternaria protenta*
**Repository/DOI:** DataverseLV, [10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ)
**License:** CC BY 4.0, confirmed in the current README and DataCite record. Attribute the authors and cite the DOI.

### Current public file inventory

| File | Bytes | Contents / status |
|---|---:|---|
| `metadata.tab` | 58,140 | 1,000 observation rows; 9 columns |
| `readme.md` | 5,296 | Experiment and schema description |
| `rgb.zip` | 288,999,868 | RGB images |
| `1797.npz` | 68,008,284 | Example calibrated cube |
| `1827.npz` | 66,098,654 | Example calibrated cube |
| `1855.npz` | 67,691,714 | Example calibrated cube |
| `1797.zip` | 47,126,377 | Example raw camera archive |
| `1827.zip` | 48,558,287 | Example raw camera archive |
| `1855.zip` | 49,757,561 | Example raw camera archive |

The README says only a few raw captures and cubes are publicly uploaded and the full set is available on request. The 1,000 rows must not be interpreted as 1,000 downloadable cubes.

### Schema, plants, and relationship to the three cubes

The 9 original metadata fields are `image_id`, `trial`, `plant`, `leaf`, `part`, `date`, `imaging_distance`, `integration_time`, and `weather`. This is not schema-identical to Source A: Source B has no standalone pathogen column, uses `trial` instead of `replicate`, and combines isolate/control and plant identity in `plant` (for example `028/II`, `065/I`, `K/I`). `leaf` is distinct from Source A's `sample`. The schemas can be normalized, but this requires a documented parsing rule that preserves isolate and individual-plant identity.

The README identifies five trials, two *A. protenta* isolates (`028` and `065`), and controls (`K`). Directly counting unique `plant` identifiers in the 1,000-row TSV gives 13 plants: five per isolate and three controls. The 1,000 rows are repeated plant/leaf/part/date observations. The three cube rows all come from trial 4 and identify three different plants:

| Cube | Trial | Plant (isolate / plant ID) | Leaf / part | Date |
|---|---:|---|---|---|
| `1797.npz` | 4 | `065/I` | 2 / G | 2025-07-07 |
| `1827.npz` | 4 | `028/IV` | 2 / 2 | 2025-07-10 |
| `1855.npz` | 4 | `028/II` | 1 / 8 | 2025-07-14 |

Thus, three public cubes correspond to three distinct plants; each plant has many other catalog observations. The file set does not include 1,000 public cubes.

### Spectral and calibration comparability

- The README says the experiment used tomato cultivar *Encore*, five trials, greenhouse natural sunlight, black background, white reference, and the Specim IQ camera. It describes raw cube/reference dimensions and calibrated cube dimensions matching Source A (512 x 512 x 204 float16 for NPZ), and the same RGB band indices/wavelength anchors.
- The README says raw camera headers contain the wavelength information, and raw camera folders contain dark and white reference captures. Three raw ZIP archives are public. Their contents and the three NPZ headers were not inspected in F1, so a verified wavelength vector/range, reflectance conversion, and per-cube calibration cannot be claimed.
- The README has internal unit/range conflicts. It reports camera distance as 13-48 mm in the collection summary, while the metadata schema says cm and TSV values span 11-100. It describes integration time as 15-100 seconds, while the table labels the field seconds and values in the TSV span 4-220. Do not silently convert either field; request author clarification.
- Source A and B have strong camera/crop/cultivation similarities, but separate acquisition periods and experiments. Equal cube dimensions and RGB anchors do not prove equal radiometric processing or complete wavelength calibration.

**Assessment:** **B - Conditionally compatible.** Useful as a separate *A. protenta* experiment or external fungal-disease validation. It is not Botrytis and must not be relabeled as Botrytis. Only three additional plants have public cubes.

## Source C - Zenodo tomato fungal disease HSI

**Record:** [Javidan_Tomato_Disease_Dataset_HSI, DOI 10.5281/zenodo.15800414](https://doi.org/10.5281/zenodo.15800414)
**Related paper:** [Javidan et al., Heliyon (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462246/). Paper methods below are reported methodology, not confirmation of the contents of each downloadable MAT file.

### File inventory and actual public availability

The Zenodo API currently lists 47 downloadable files totaling 6,048,070,769 bytes (about 6.05 GB decimal):

- 40 class-named image MAT candidates: `Alternaria_alternata_1.mat` through `_8.mat`; `Alternaria_solani_1.mat` through `_8.mat`; `Botrytis_cinerea_1.mat` through `_8.mat`; `Fusarium_oxysporum_1.mat` through `_8.mat`; and `Healthy_1.mat` through `_8.mat`.
- Five feature MAT files: `Alternaria_alternata_features.mat`, `Alternaria_solani_features.mat`, `Botrytis_cinerea_features.mat`, `Fusarium_oxysporum_features.mat`, and `Healthy_features.mat`.
- MATLAB scripts: `Feature_Extraction_EfficientNet.m` and `Simillaritycheck_Manhatan_and_Cosine.m`.

The record description explicitly says hyperspectral images and separately extracted features are included. Small MATLAB scripts were read, but none of the large MAT files were downloaded or opened. The feature extraction script expects `imgData.image` with 550 bands and writes `finalFeatures` and `finalLabels`; these are code expectations, not verified internal variables for the published MAT files. The manifest is sufficient to count 40 original-image candidate files, not to verify their array layout or independent-plant content.

### Study, sample units, labels, and acquisition

- Crop/cultivar: tomato, *Solanum lycopersicum* var. 4921, grown in a greenhouse in Gorgan, Iran. The paper reports 20 +/- 2 C and 80% humidity.
- Disease classes: *A. alternata*, *A. solani*, *B. cinerea*, *F. oxysporum*, and healthy controls.
- The paper describes 25 pots per disease and 25 control pots (125 experimental pots in total), inoculation with 5 x 10^6 spores/mL, and daily imaging on days 1, 3, 5, 7, 9, and 11. It also reports 100 HSI and 100 RGB images per class and sampling day. These are paper-level experimental counts; the record does not provide a plant-ID table or mapping from the 40 numbered image files to pots, leaves, or time points. Pots/images are not assumed to be independent plants in the released files.
- The Zenodo description says image samples on days 1, 3, 5, and 7, differing from the paper's six imaging days. The file naming does not resolve this discrepancy.
- The paper describes pathogen isolation/purification, morphology/spore identification, and pathogenicity tests before inoculation. The release does not provide sample-linked laboratory assay results; the per-file label appears to be class/inoculation grouping rather than a verified individual-cube assay. No molecular verification is established by the accessed source material.
- The paper reports a Hyspim HSI-Vis_Nir-15fps system, 400-950 nm, laboratory imaging with halogen illumination, a dark chamber/background, fixed 25 cm camera distance, and a white reference captured every 10 minutes. The exact reflectance algorithm and per-cube wavelength vector are not exposed in the record. The MATLAB script says 550 bands, which was not confirmed from headers.
- Spatial dimensions, scans per plant, biological plant count represented by the released MAT files, and per-file disease severity are unknown.

### Derived features and leakage risk

The five precomputed feature MAT files are derived data, not independent cube samples. The accompanying extraction script selects the first 20 images in each group and the similarity script randomly selects train/test examples within each class (including a described 3-train/1-test per-class task). Neither script groups by plant, leaf, or repeated time point. The extraction script's 20-per-class expectation is also not reconciled with the manifest's eight numbered image MAT files per class. These scripts do not prove how the supplied feature files were made or that an actual published result leaked, but their random image-level evaluation is not adequate evidence of plant-independent performance. Do not use the packaged features/splits for new evaluation without source-level provenance; derive features from validated cubes and split by independent plant.

**License:** Zenodo API and DataCite identify CC BY 4.0. This resolves the unclear license display noted on the human-readable record. Attribution and DOI citation are required. No additional permission is indicated for the data, but the article's own terms should not be confused with the dataset license.

**Assessment:** **B - Conditionally compatible.** This is the most promising candidate for *additional Botrytis-labeled material*: eight public `Botrytis_cinerea_*.mat` image candidates plus healthy controls. However, it is a different cultivar, country, imaging setup, and spectral sampling from TerraSpectra; the public files do not establish eight independent plants. Consider a separate external test or a distinct experiment, not a pooled training set until the author supplies plant/time/calibration metadata.

## Source D - Tomato bacterial leaf spot HSI

**Record:** Ag Data Commons, [Early Detection of Tomato Bacterial Leaf Spot Disease](https://data.nal.usda.gov/dataset/early-detection-bacterial-spot-disease-tomato-hyperspectral-imaging); dataset DOI [10.15482/USDA.ADC/26046328](https://doi.org/10.15482/USDA.ADC/26046328).
**Paper:** [Zhang, Vinatzer & Li, Scientific Reports (2024)](https://www.nature.com/articles/s41598-024-78650-6).

### Public file and licensing

The current Ag Data Commons record (version 2) lists one public file, `tomato_leaf.zip`, 15.4 GB, MD5 `77bbf35ab67b8893e66fd68c660905ea`. The archive was not downloaded, and its internal file names/formats and cube count are therefore unknown. The DataCite entry for version 1 reports 16,531,945,854 bytes; acquire only a specifically versioned package and verify its checksum in F2. The current record identifies the dataset as public and CC BY 4.0. Crossref reports CC BY-NC-ND 4.0 for the journal article; this is a separate article license and not the dataset license.

### Paper-reported data and acquisition

- Crop: tomato; cultivar is not identified in the accessed record summary. Disease is bacterial leaf spot caused by *Xanthomonas perforans*, not a fungal disease.
- The study reports 36 images containing 228 leaves. This is not a count of 228 independent plants; plant/experimental-unit count and the archive's file-to-leaf mapping were not established in F1.
- The article reports pathogen populations measured from leaves (CFU/cm^2), disease severity ratings, and seven consecutive days of observations. Thus the paper has substantially stronger biological ground truth than a visual symptom label alone. The released archive's sample-level join keys and assay coverage must still be inspected before treating every file as independently verified.
- The paper reports a Resonon benchtop system: PIKA-L / VIS-NIR and PIKA-NIR320 / NIR-SWIR. The paper describes approximately 300 VIS-NIR bands (reported header span 385.63-1027.18 nm) and 168 NIR bands (890.68-1719.81 nm), both scanned for leaves. These are separate sensors/ranges, not one uniform TerraSpectra spectral axis. The article also reports BIL cubes and per-scan headers.
- Reflectance mode uses dark correction and response correction with a reference tile; artificial halogen illumination and black/white backgrounds were used. This is a more documented calibration path than currently established for every TerraSpectra cube, but is a different sensor and controlled acquisition.
- The current repository record exposes a ZIP rather than a sample-level table or a browsable manifest. F1 did not verify disease labels, cube counts, header linkage, exact plant-level identifiers, or whether the reported 228 leaf samples are all individually represented.

**Assessment:** **B - Conditionally compatible** as an external bacterial disease/methodological benchmark only. It must remain outside fungal/Botrytis labels and requires a separate data-loading path and study-specific evaluation.

## Additional relevant source screened

### Tomato bacterial point-spectroscopy record (restricted)

[Zenodo record 10.5281/zenodo.10498473](https://doi.org/10.5281/zenodo.10498473), "Hyperspectral spectroscopic transmittance data collected in-vivo healthy and diseased tomato leaflets in controlled conditions - dataset II," reports nine tomato plants: three controls, three inoculated with *Pseudomonas syringae* pv. *tomato*, and three with *Xanthomonas euvesicatoria*. It describes nine point measurements per plant using a Hamamatsu C11697MB spectrometer (200-1100 nm, 0.6 nm resolution), not HSI image cubes. Zenodo currently marks the record restricted and lists zero files. Its metadata states GPL-3.0-or-later, but access and the scope of the license require clarification. No public raw cubes are available. **Rating: D - Unusable currently** for TerraSpectra cube integration.

### Tomato-sepal hyperspectral paper hit (not a dataset)

[Zenodo 10.5281/zenodo.4896828](https://zenodo.org/records/4896828) is a public conference abstract PDF (116,836 bytes) about tomato-sepal segmentation, not an HSI image collection. Its CC BY 4.0 record license applies to the abstract artifact, not to any absent cube dataset. Sensor, wavelength range, and samples are not provided. **Rating: C - Methodological reference only.**

## Compatibility matrix

| Source | Crop / pathogen relevance | Technical and biological fit | Rating |
|---|---|---|---|
| A - Existing Botrytis | Tomato; *B. cinerea*, *B. pseudocinerea*, control | Current baseline; 3 local examples, repeated observations across 49 plants; only one cube's wavelengths locally verified | **A - Directly compatible** with itself |
| B - Alternaria | Tomato; *A. protenta* (isolates 028/065) | Same Specim IQ family, cube shape and greenhouse style; three public cubes map to three distinct plants, but a different experiment/pathogen and B calibration/units are unresolved | **B - Conditionally compatible** as a separate disease/external fungal test |
| C - Zenodo fungi | Tomato; four fungi including *B. cinerea* and healthy | 40 candidate image MAT files, 8 Botrytis-named; different cultivar/sensor/setup, uncertain plant mapping and feature/split provenance | **B - Conditionally compatible** as separate/external test |
| D - Bacterial leaf spot | Tomato; *X. perforans* | Strong paper-reported validation/time series and BIL/header data, but 15.4 GB ZIP, different sensors, bacterial label | **B - Conditionally compatible** as external methodological benchmark |
| Zenodo dataset II | Tomato; two bacterial pathogens | Nine plants with point transmittance spectra; no public files, not cubes | **D - Unusable currently** |
| Zenodo sepal record | Tomato; fungal risk context only | Abstract PDF only; no image data | **C - Methodological reference only** |

No new candidate meets **A - Directly compatible** for direct integration with current Botrytis cubes.

## Scientific risks and unresolved questions

1. **Pathogen identity:** *B. cinerea*, *B. pseudocinerea*, *A. protenta*, *A. alternata*, *A. solani*, *F. oxysporum*, and *X. perforans* are not interchangeable labels. Preserve distinct taxonomy and experimental source.
2. **Biological independence:** Source A has 49 plants behind 904 observations; Source B has 13 plants behind 1,000 observations. Their three public cubes each map to separate plants, but multiple catalog rows are repeated observations. Source C's eight class files do not establish eight plants. Source D's 228 leaves do not establish 228 plants.
3. **Time and severity:** Source A/B have dates but no documented days-post-inoculation or numerical severity in the public README. Source C paper and repository disagree on the available time points. Source D paper has seven-day progression and ratings, but archive linkage is unverified.
4. **Spectral compatibility:** Specim IQ's 204 bands do not align automatically with Source C's claimed 550 bands or Source D's separate 300/168-band cameras. Never transfer one cube's wavelength vector to another.
5. **Calibration and illumination:** Source A/B use natural greenhouse sunlight and white references; Source C reports controlled halogen illumination/reference snapshots; Source D uses dark/response correction and a reference tile. These produce experiment-specific radiometry and likely domain shift. The A/B README unit conflicts and Source A's undocumented NPZ processing need author follow-up.
6. **Spatial layout:** A/B document 512 x 512 x 204 arrays. C's released array dimensions are unknown. D's paper describes BIL image cubes, but archive contents and shapes were not inspected. Do not resample or concatenate without checking files and headers.
7. **Leakage:** Plant/leaf/time repeats in A/B and unknown repeats in C/D make image-level random splitting unsafe. All splits and reporting must be grouped by plant (and ideally trial) and metrics must not treat pixels/bands as biological replicates. Source C's bundled feature workflow has no documented plant-level grouping.
8. **Version/provenance:** Ag Data Commons' current page is version 2 while the accessed DataCite versioned DOI describes version 1 and a different package size. Preserve exact version and checksum in F2.
9. **Label evidence:** Source C reports inoculation and pathogen isolation/pathogenicity methods but no sample-linked molecular or culture result in the released manifest. Source D has stronger paper-reported CFU validation, but file-level assay joins need confirmation.
10. **Data scale and format:** Source C is about 6.05 GB of MATLAB files and would require variable/dimension/wavelength inspection. Source D is one 15.4 GB ZIP with no preview. Both require bounded staged storage and checksums.

## Acquisition priority and Phase F2 gate

1. **First for additional Botrytis-labeled material: Source C.** It is the only new open record found with *B. cinerea*-named original-image candidates and healthy controls. F2 should start with the 8 `Botrytis_cinerea_*.mat` and 8 `Healthy_*.mat` files only (combined listed size 2,254,793,632 bytes), subject to preserving their source labels and excluding packaged features from evaluation. This is a candidate-data pilot, not a claim of 16 independent plants.
2. **Second for same-sensor technical comparison: Source B.** The 3 public `1797.npz`, `1827.npz`, `1855.npz` plus `metadata.tab` and `readme.md` are small enough for a separate, carefully labeled *A. protenta* comparison. Acquire `1797.zip`, `1827.zip`, and `1855.zip` only if header/reference inspection is needed. This does not add Botrytis examples.
3. **Source D:** defer the 15.4 GB package unless Phase F2 explicitly includes an external bacterial benchmark. If acquired, use the current version 2 file/checksum and retain bacterial labels in a separate experiment.
4. **Source E:** do not attempt to retrieve data without an access grant and license-scope confirmation. It is point spectroscopy, not a cube collection.

Before any integration, obtain plant/leaf identifiers and MAT variable names for Source C; resolve its time-point and image-count discrepancy; verify every cube's dimensions, wavelength vector, band ordering, units, and reflectance method; link files to biological plants and labels; confirm assay and disease-severity provenance; and define plant-grouped train/validation/test partitions before feature extraction.

**Phase F2 recommendation:** **GO** for limited, checksummed acquisition and metadata/provenance validation. **NO-GO** for merging into TerraSpectra's Botrytis training pool or training/evaluating a combined model until all gates above pass. Keep every source and pathogen distinct in storage and analysis.
