
from pathlib import Path
import re
import csv
import json
import numpy as np

BASE_DIR = Path("data/raw/tomato_botrytis/raw_2436/2436/capture")
OUTPUT_DIR = Path("data/processed/metadata")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_wavelengths(header_path):
    """Extract wavelengths from an ENVI header."""

    text = header_path.read_text(encoding="utf-8")

    match = re.search(
        r"wavelength\s*=\s*\{(.*?)\}",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match is None:
        raise ValueError(
            f"Wavelength field not found: {header_path}"
        )

    values = re.findall(
        r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        match.group(1)
    )

    wavelengths = np.array(values, dtype=np.float64)

    if len(wavelengths) != 204:
        raise ValueError(
            f"Expected 204 wavelengths, found {len(wavelengths)}"
        )

    if not np.all(np.diff(wavelengths) > 0):
        raise ValueError("Wavelengths are not strictly increasing.")

    return wavelengths


header_files = {
    "main": BASE_DIR / "2436.hdr",
    "dark": BASE_DIR / "DARKREF_2436.hdr",
    "white": BASE_DIR / "WHITEREF_2436.hdr"
}

wavelengths = {
    name: extract_wavelengths(path)
    for name, path in header_files.items()
}

reference = wavelengths["main"]

for name, values in wavelengths.items():
    if not np.array_equal(reference, values):
        raise ValueError(
            f"{name} wavelength array does not match main header."
        )

# Save exact wavelength values as CSV.
csv_path = OUTPUT_DIR / "wavelengths_2436.csv"

with open(csv_path, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["band_index", "wavelength_nm"])

    for index, wavelength in enumerate(reference):
        writer.writerow([index, wavelength])

# Save machine-readable JSON metadata.
json_path = OUTPUT_DIR / "spectral_metadata_2436.json"

metadata = {
    "image_id": "2436",
    "sensor": "Specim IQ",
    "spectral_bands": len(reference),
    "wavelength_unit": "nm",
    "wavelength_min": float(reference.min()),
    "wavelength_max": float(reference.max()),
    "wavelength_source": "Original ENVI headers",
    "headers_validated": list(header_files.keys()),
    "wavelengths": reference.tolist()
}

with open(json_path, "w") as file:
    json.dump(metadata, file, indent=4)

print("=" * 60)
print("WAVELENGTH EXTRACTION COMPLETED")
print("=" * 60)

print("Number of bands:", len(reference))
print("Minimum wavelength:", reference.min(), "nm")
print("Maximum wavelength:", reference.max(), "nm")
print("Strictly increasing:", np.all(np.diff(reference) > 0))
print("CSV saved:", csv_path)
print("JSON saved:", json_path)

print("\nRGB reference verification:")

for band, expected in [
    (19, 449.35),
    (53, 548.55),
    (70, 598.60)
]:
    actual = reference[band - 1]

    print(
        f"Band {band}: {actual:.2f} nm "
        f"(expected {expected:.2f} nm)"
    )

print("\nExtraction successful.")
