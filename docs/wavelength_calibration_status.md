
# Wavelength Calibration Status

## Dataset
Tomato Botrytis Hyperspectral Dataset

## Image 2436
- NPZ cube available.
- Original ENVI capture available.
- Dark reference available.
- White reference available.
- ENVI header contains 204 wavelength values.
- Verified wavelength range: 397.32–1003.58 nm.
- Wavelengths are finite and strictly increasing.
- Main capture, dark reference, and white reference wavelength arrays match.
- RGB anchor bands agree with the dataset README.
- Exact pixel-level correspondence between the original raw capture and calibrated NPZ remains unresolved.

## Image 2973
- NPZ cube available.
- Original ENVI capture not present in the downloaded files.
- Dark and white reference files not present.
- Independent wavelength calibration not verified.

## Image 3079
- NPZ cube available.
- Original ENVI capture not present in the downloaded files.
- Dark and white reference files not present.
- Independent wavelength calibration not verified.

## Processing Decision

The verified wavelength vector for image 2436 must not be assigned to images 2973 or 3079 without supporting calibration metadata.

The author-provided NPZ cubes remain the primary data source. No additional calibration is applied to these cubes.

## Required Follow-up

Request the following information from the dataset authors:

1. Original ENVI headers for images 2973 and 3079.
2. Their corresponding dark and white reference captures, if available.
3. Confirmation of the wavelength vector and band ordering used in each NPZ cube.
4. Documentation of the calibration procedure used to produce the NPZ cubes.
