
from pathlib import Path
import re
import numpy as np

CAPTURE_DIR = Path(
    "data/raw/tomato_botrytis/raw_2436/2436/capture"
)

HEADERS = {
    "main": CAPTURE_DIR / "2436.hdr",
    "dark": CAPTURE_DIR / "DARKREF_2436.hdr",
    "white": CAPTURE_DIR / "WHITEREF_2436.hdr",
}


def extract_wavelengths(header_path):
    text = header_path.read_text(encoding="utf-8")

    match = re.search(
        r"wavelength\s*=\s*\{([^}]*)\}",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not match:
        raise ValueError(
            f"Wavelength field not found: {header_path}"
        )

    values = re.findall(
        r"[-+]?\d+(?:\.\d+)?",
        match.group(1)
    )

    return np.array(values, dtype=np.float64)


print("=" * 65)
print("WAVELENGTH HEADER VALIDATION")
print("=" * 65)

wavelength_arrays = {}

for name, path in HEADERS.items():
    if not path.exists():
        raise FileNotFoundError(path)

    wavelengths = extract_wavelengths(path)
    wavelength_arrays[name] = wavelengths

    print(f"\n{name.upper()} HEADER")
    print("File:", path.name)
    print("Wavelength count:", len(wavelengths))
    print("First wavelength:", wavelengths[0], "nm")
    print("Last wavelength:", wavelengths[-1], "nm")
    print("Strictly increasing:", np.all(np.diff(wavelengths) > 0))

main = wavelength_arrays["main"]
dark = wavelength_arrays["dark"]
white = wavelength_arrays["white"]

print("\n" + "=" * 65)
print("CROSS-HEADER COMPARISON")
print("=" * 65)

for name, wavelengths in wavelength_arrays.items():
    print(
        f"{name}: {len(wavelengths)} values; "
        f"matches main exactly: {np.array_equal(main, wavelengths)}"
    )

print("\nExpected bands:", 204)
print("Main header count correct:", len(main) == 204)
print("Dark header count correct:", len(dark) == 204)
print("White header count correct:", len(white) == 204)

if len(main) != 204 or len(dark) != 204 or len(white) != 204:
    print("\nWARNING: Wavelength count mismatch detected.")

if not (
    len(main) == len(dark) == len(white)
    and np.array_equal(main, dark)
    and np.array_equal(main, white)
):
    print("WARNING: Header wavelength arrays do not match.")

print("\nKnown RGB reference checks (ENVI 1-based numbering):")

for band_number, expected in [
    (19, 449.35),
    (53, 548.55),
    (70, 598.60)
]:
    if band_number <= len(main):
        actual = main[band_number - 1]

        print(
            f"Band {band_number}: "
            f"expected={expected}, actual={actual}, "
            f"match={np.isclose(actual, expected, atol=0.01)}"
        )

print("\nValidation completed.")
