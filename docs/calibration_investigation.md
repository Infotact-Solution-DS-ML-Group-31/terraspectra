# Calibration Investigation – Image 2436

## Objective
Investigate the relationship between the original Specim IQ raw capture and the supplied calibrated NPZ cube.

## Dataset characteristics
- Image ID: 2436
- Raw cube dimensions: 512 × 512 × 204
- Raw data type: uint16
- Processed cube dimensions: 512 × 512 × 204
- Processed data type: float16
- Spectral range: 397.32–1003.58 nm

## Tests performed

1. Validated the raw, dark-reference and white-reference ENVI headers.
2. Extracted and verified all 204 wavelength values.
3. Calculated a candidate reflectance cube using per-pixel reference measurements.
4. Compared candidate values with the supplied NPZ cube.
5. Tested eight spatial rotations and reflections.
6. Tested spectral-band correspondence.
7. Tested calibration using per-band averaged reference measurements.
8. Compared the RGB preview with an RGB image generated from the NPZ cube.

## Key findings
- Raw and reference files have valid dimensions and expected data types.
- All reference positions have positive white-minus-dark differences.
- Candidate calibration distributions resemble the NPZ distribution, but pixel-wise Pearson correlation remains very low.
- Per-pixel reference candidate correlation: 0.0196.
- Averaged reference candidate correlation: 0.0179.
- Spatial transformations and spectral-band matching did not resolve the discrepancy.
- The NPZ-derived RGB image visually matches the original preview's spatial structures.
- Image 2436 contains 1,454 extreme NPZ measurements above 2.0.

## Current decision
Use the author-provided calibrated NPZ cube as the primary processed input. Preserve original raw files and reference files without modification.

Do not apply an additional calibration or claim that the exact calibration algorithm has been independently reproduced.

## Outstanding questions
- What exact calibration procedure generated the NPZ cube?
- How are raw and calibrated pixels mapped?
- What explains the low numerical correlation?
- What causes the extreme values in image 2436?

## Next action
Request preprocessing documentation and clarification from the dataset authors.

**Investigation status:** Partially completed. Calibration provenance requires author confirmation.