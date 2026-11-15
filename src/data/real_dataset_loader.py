
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("data/raw/tomato_botrytis")
MASK_DIR = Path("data/processed/quality_masks")

IMAGE_IDS = ["2436", "2973", "3079"]


def load_metadata():
    """Load image metadata from the available metadata file."""

    candidates = [
        DATA_DIR / "metadata.tsv",
        DATA_DIR / "metadata.tab"
    ]

    metadata_path = next(
        (path for path in candidates if path.exists()),
        None
    )

    if metadata_path is None:
        raise FileNotFoundError(
            "Neither metadata.tsv nor metadata.tab was found."
        )

    metadata = pd.read_csv(
        metadata_path,
        sep="\t",
        dtype={"image_id": str}
    )

    metadata["image_id"] = metadata["image_id"].str.strip()

    if "image_id" not in metadata.columns:
        raise ValueError("Metadata is missing the image_id column.")

    return metadata


def load_cube(image_id):
    """Load one hyperspectral cube without modifying raw data."""

    file_path = DATA_DIR / f"{image_id}.npz"

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    with np.load(file_path, allow_pickle=False) as data:
        if "arr_0" not in data:
            raise KeyError(f"arr_0 missing from {file_path}")

        cube = data["arr_0"].astype(np.float32)

    if cube.ndim != 3:
        raise ValueError(
            f"Expected a 3D cube, got shape {cube.shape}"
        )

    if not np.isfinite(cube).all():
        raise ValueError(
            f"Non-finite values detected in image {image_id}"
        )

    return cube


def load_quality_mask(image_id, expected_shape):
    """Load an existing mask, or return None if unavailable."""

    mask_path = MASK_DIR / f"{image_id}_quality_mask.npz"

    if not mask_path.exists():
        return None

    with np.load(mask_path, allow_pickle=False) as data:
        mask = data["quality_mask"].astype(bool)

    if mask.shape != expected_shape:
        raise ValueError(
            f"Mask shape {mask.shape} does not match "
            f"cube shape {expected_shape}"
        )

    return mask


def load_sample_dataset(image_ids=None):
    """Load cubes with matching metadata and optional masks."""

    if image_ids is None:
        image_ids = IMAGE_IDS

    metadata = load_metadata()
    dataset = {}

    for image_id in image_ids:
        cube = load_cube(image_id)

        matching_rows = metadata[
            metadata["image_id"] == str(image_id)
        ]

        if len(matching_rows) != 1:
            raise ValueError(
                f"Expected exactly one metadata row for "
                f"{image_id}, found {len(matching_rows)}"
            )

        quality_mask = load_quality_mask(
            image_id,
            cube.shape
        )

        dataset[image_id] = {
            "cube": cube,
            "metadata": matching_rows.iloc[0].to_dict(),
            "quality_mask": quality_mask
        }

        flagged = (
            int(quality_mask.sum())
            if quality_mask is not None
            else 0
        )

        print(f"\nImage: {image_id}")
        print("Cube shape:", cube.shape)
        print("Cube dtype:", cube.dtype)
        print("Metadata matched: Yes")
        print("Quality mask available:", quality_mask is not None)
        print("Flagged measurements:", flagged)

    return dataset


if __name__ == "__main__":
    print("=" * 60)
    print("TERRASPECTRA REAL DATA LOADER")
    print("=" * 60)

    dataset = load_sample_dataset()

    print("\nSuccessfully loaded images:", len(dataset))
    print("Loader validation completed.")
