
from pathlib import Path
import numpy as np

BASE = Path("data/raw/tomato_botrytis/raw_2436/2436/capture")
NPZ_PATH = Path("data/raw/tomato_botrytis/2436.npz")


def load_bil(path, header_path):
    import re

    text = header_path.read_text(encoding="utf-8", errors="ignore")

    def field(name):
        match = re.search(
            rf"(?im)^\s*{re.escape(name)}\s*=\s*(.+?)\s*$",
            text
        )
        if not match:
            raise ValueError(f"Missing header field: {name}")
        return match.group(1).strip()

    samples = int(field("samples"))
    lines = int(field("lines"))
    bands = int(field("bands"))
    data_type = int(field("data type"))
    interleave = field("interleave").lower()
    byte_order = int(field("byte order"))

    if data_type != 12 or interleave != "bil" or byte_order != 0:
        raise ValueError(f"Unexpected ENVI format in {header_path}")

    raw = np.fromfile(path, dtype="<u2")

    expected = samples * lines * bands
    if raw.size != expected:
        raise ValueError(f"Unexpected number of values in {path}")

    return raw.reshape(lines, bands, samples).transpose(0, 2, 1)


def describe(name, array):
    x = np.asarray(array, dtype=np.float32)
    print(f"\n{name}")
    print("-" * 55)
    print("Shape:", x.shape)
    print("Min:", float(np.min(x)))
    print("Max:", float(np.max(x)))
    print("Mean:", float(np.mean(x)))
    print("Median:", float(np.median(x)))
    print("Percentiles [1, 50, 95, 99, 99.9]:",
          np.percentile(x, [1, 50, 95, 99, 99.9]).tolist())
    print("Values > 1:", int(np.sum(x > 1)))
    print("Values > 2:", int(np.sum(x > 2)))


def main():
    raw = load_bil(BASE / "2436.raw", BASE / "2436.hdr")
    dark = load_bil(
        BASE / "DARKREF_2436.raw",
        BASE / "DARKREF_2436.hdr"
    )
    white = load_bil(
        BASE / "WHITEREF_2436.raw",
        BASE / "WHITEREF_2436.hdr"
    )

    processed = np.load(
        NPZ_PATH, allow_pickle=False
    )["arr_0"].astype(np.float32)

    raw = raw.astype(np.float32)
    dark = dark.astype(np.float32)
    white = white.astype(np.float32)

    # References have one line and are broadcast over image rows.
    denominator = white - dark

    invalid = denominator <= 0
    print("=" * 60)
    print("CALIBRATION CANDIDATE COMPARISON")
    print("=" * 60)
    print("Invalid reference positions:", int(invalid.sum()))
    print("Total reference positions:", denominator.size)

    if np.any(invalid):
        raise ValueError(
            "Some white-dark reference positions are non-positive. "
            "Do not calculate candidate reflectance yet."
        )

    candidate = (raw - dark) / denominator

    describe("CANDIDATE REFLECTANCE", candidate)
    describe("EXISTING PROCESSED NPZ", processed)

    # Compare a deterministic sample of corresponding measurements.
    rng = np.random.default_rng(42)
    indices = rng.choice(
        candidate.size,
        size=min(200_000, candidate.size),
        replace=False
    )

    candidate_sample = candidate.ravel()[indices]
    processed_sample = processed.ravel()[indices]

    correlation = np.corrcoef(
        candidate_sample, processed_sample
    )[0, 1]

    difference = processed_sample - candidate_sample

    print("\nSAMPLED COMPARISON")
    print("-" * 55)
    print("Sample count:", len(indices))
    print("Pearson correlation:", float(correlation))
    print("Mean absolute difference:",
          float(np.mean(np.abs(difference))))
    print("Median absolute difference:",
          float(np.median(np.abs(difference))))
    print("Mean signed difference:",
          float(np.mean(difference)))

    print("\nNo files were modified or saved.")
    print("Diagnostic comparison completed.")


if __name__ == "__main__":
    main()
