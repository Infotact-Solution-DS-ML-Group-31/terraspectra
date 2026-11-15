
from pathlib import Path
import re
import numpy as np

BASE = Path("data/raw/tomato_botrytis/raw_2436/2436/capture")
NPZ_PATH = Path("data/raw/tomato_botrytis/2436.npz")

def read_header(path):
    text = path.read_text(encoding="utf-8", errors="ignore")

    def get_value(name):
        match = re.search(
            rf"(?im)^\s*{re.escape(name)}\s*=\s*(.+?)\s*$",
            text
        )
        if not match:
            raise ValueError(f"Missing header field: {name}")
        return match.group(1).strip()

    return {
        "samples": int(get_value("samples")),
        "lines": int(get_value("lines")),
        "bands": int(get_value("bands")),
        "data_type": int(get_value("data type")),
        "interleave": get_value("interleave").lower(),
        "byte_order": int(get_value("byte order")),
    }


def load_envi_raw(raw_path, header_path):
    info = read_header(header_path)

    if info["data_type"] != 12:
        raise ValueError("Expected ENVI data type 12 (uint16).")

    if info["byte_order"] != 0:
        raise ValueError("Expected little-endian byte order.")

    if info["interleave"] != "bil":
        raise ValueError("Expected BIL interleave.")

    expected_values = (
        info["lines"] * info["bands"] * info["samples"]
    )

    raw = np.fromfile(raw_path, dtype="<u2")

    if raw.size != expected_values:
        raise ValueError(
            f"Size mismatch in {raw_path.name}: "
            f"expected {expected_values}, got {raw.size}"
        )

    # BIL disk layout: lines, bands, samples.
    # Convert to: height, width, bands.
    cube = raw.reshape(
        info["lines"], info["bands"], info["samples"]
    ).transpose(0, 2, 1)

    return cube, info


def report(name, array):
    values = array.astype(np.float32)

    print(f"\n{name}")
    print("-" * 55)
    print("Shape:", values.shape)
    print("Data type:", array.dtype)
    print("Minimum:", float(np.min(values)))
    print("Maximum:", float(np.max(values)))
    print("Mean:", float(np.mean(values)))
    print("Median:", float(np.median(values)))
    print("Percentiles [1, 50, 99]:",
          np.percentile(values, [1, 50, 99]).tolist())
    print("Zero percentage:",
          float(np.mean(values == 0) * 100))


def main():
    raw, raw_info = load_envi_raw(
        BASE / "2436.raw", BASE / "2436.hdr"
    )

    dark, dark_info = load_envi_raw(
        BASE / "DARKREF_2436.raw",
        BASE / "DARKREF_2436.hdr"
    )

    white, white_info = load_envi_raw(
        BASE / "WHITEREF_2436.raw",
        BASE / "WHITEREF_2436.hdr"
    )

    npz = np.load(NPZ_PATH, allow_pickle=False)
    processed = npz["arr_0"]

    print("=" * 60)
    print("SENSOR AND CALIBRATION FILE INSPECTION")
    print("=" * 60)

    print("\nHeader information:")
    print("Raw:", raw_info)
    print("Dark:", dark_info)
    print("White:", white_info)

    report("ORIGINAL RAW CUBE", raw)
    report("DARK REFERENCE", dark)
    report("WHITE REFERENCE", white)
    report("PROCESSED NPZ CUBE", processed)

    # Reference measurements have one line.
    dark_spectrum = dark[0].astype(np.float32).mean(axis=0)
    white_spectrum = white[0].astype(np.float32).mean(axis=0)

    denominator = white_spectrum - dark_spectrum

    print("\nREFERENCE DIFFERENCE CHECK")
    print("-" * 55)
    print("Minimum white-dark difference:",
          float(denominator.min()))
    print("Maximum white-dark difference:",
          float(denominator.max()))
    print("Bands with non-positive difference:",
          int(np.sum(denominator <= 0)))

    print("\nNo calibration has been applied.")
    print("Inspection completed.")


if __name__ == "__main__":
    main()
