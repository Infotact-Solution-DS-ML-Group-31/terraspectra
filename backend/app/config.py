"""
TerraSpectra Backend Configuration.
Resolves paths to datasets, processed features, reports, and outputs.
"""

from pathlib import Path

# Project root: C:\My projects\terraspectra
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "tomato_botrytis"
METADATA_PATH = RAW_DATA_DIR / "metadata.tsv"
README_PATH = RAW_DATA_DIR / "readme.md"

PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = PROCESSED_DIR / "features"
REPORTS_DIR = PROCESSED_DIR / "reports"
SEGMENTATION_DIR = PROCESSED_DIR / "segmentation"
METADATA_PROCESSED_DIR = PROCESSED_DIR / "metadata"
PCA_DIR = PROCESSED_DIR / "pca"

# Outputs and docs
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

# Valid locally available cubes
LOCAL_CUBE_IDS = ["2436", "2973", "3079"]

API_VERSION = "1.0.0"
APP_NAME = "TerraSpectra Hyperspectral Analytics Platform"
