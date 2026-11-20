"""
Automated tests for Phase C: Dataset-Wide Biological Data Assessment and ML Feasibility.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from src.data.assess_dataset_suitability import (
    load_and_audit_metadata,
    audit_available_cubes,
    perform_biological_analysis,
    simulate_split_leakage,
    DATASET_INVENTORY_JSON,
    BIOLOGICAL_SUMMARY_JSON,
    ML_FEASIBILITY_JSON
)


def test_metadata_parsing_and_schema():
    """Verify that metadata.tsv loads with expected 904 rows and required columns."""
    df = load_and_audit_metadata()
    assert len(df) == 904
    required_cols = [
        "image_id", "replicate", "pathogen", "sample", "part",
        "date", "imaging_distance", "integration_time", "weather",
        "plant_id", "part_id", "local_cube_available"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"

    # Verify only 1 missing value exists in imaging_distance across the whole table
    assert df["imaging_distance"].isnull().sum() == 1
    assert df["image_id"].isnull().sum() == 0
    assert df["pathogen"].isnull().sum() == 0


def test_duplicate_image_detection():
    """Verify that every image_id is unique and no duplicate records exist."""
    df = load_and_audit_metadata()
    assert df["image_id"].nunique() == 904
    assert df["image_id"].duplicated().sum() == 0


def test_plant_identity_grouping():
    """Verify resolution of biological plant identities (replicate_pathogen_sample)."""
    df = load_and_audit_metadata()
    plant_df = perform_biological_analysis(df)

    # Exactly 49 unique biological plants
    assert len(plant_df) == 49
    assert plant_df["plant_id"].nunique() == 49

    # Exactly 193 distinct organs
    assert df["part_id"].nunique() == 193

    # All plants have >= 4 observations
    assert (plant_df["observation_count"] >= 4).all()
    assert int(plant_df["observation_count"].min()) == 4
    assert int(plant_df["observation_count"].max()) == 39


def test_class_distribution_image_and_plant_level():
    """Verify class balance at both image observation and plant level."""
    df = load_and_audit_metadata()
    plant_df = perform_biological_analysis(df)

    # Image-level counts
    img_counts = df["pathogen"].value_counts().to_dict()
    assert img_counts["B. pseudo"] == 411
    assert img_counts["B. cin."] == 403
    assert img_counts["K"] == 90

    # Plant-level counts
    plant_counts = plant_df["pathogen"].value_counts().to_dict()
    assert plant_counts["B. pseudo"] == 20
    assert plant_counts["B. cin."] == 20
    assert plant_counts["K"] == 9


def test_missing_cube_detection():
    """Verify that exactly 3 cubes exist locally and 901 are missing."""
    cube_records = audit_available_cubes()
    assert len(cube_records) == 3
    local_ids = {c["image_id"] for c in cube_records}
    assert local_ids == {"2436", "2973", "3079"}

    df = load_and_audit_metadata()
    assert df["local_cube_available"].sum() == 3
    assert (df["local_cube_available"] == False).sum() == 901


def test_calibration_availability_classification():
    """Verify that cubes are correctly classified into calibration tiers."""
    cube_records = audit_available_cubes()
    record_map = {c["image_id"]: c for c in cube_records}

    # 2436 has verified ENVI header
    assert "Wavelength-calibrated" in record_map["2436"]["calibration_classification"]
    assert record_map["2436"]["envi_raw_header_available"] is True

    # 2973 and 3079 lack ENVI headers
    assert "Spectral-band indexed only" in record_map["2973"]["calibration_classification"]
    assert record_map["2973"]["envi_raw_header_available"] is False

    assert "Spectral-band indexed only" in record_map["3079"]["calibration_classification"]
    assert record_map["3079"]["envi_raw_header_available"] is False


def test_repeated_plant_split_leakage_detection():
    """Verify that random KFold causes severe leakage, while GroupKFold prevents it."""
    df = load_and_audit_metadata()
    random_leakage, group_leakage = simulate_split_leakage(df)

    # Random split leaks >90% of test plants into train in every fold
    for f in random_leakage:
        assert f["leakage_percentage"] >= 90.0, (
            f"Expected high leakage in random split, got {f['leakage_percentage']}%"
        )

    # GroupKFold must have exactly 0 leaked plants in all folds
    for f in group_leakage:
        assert f["test_plants_leaked_from_train"] == 0
        assert f["leakage_percentage"] == 0.0


def test_generated_reports_integrity():
    """Verify that Phase C JSON reports exist and match analytical values."""
    assert DATASET_INVENTORY_JSON.exists()
    assert BIOLOGICAL_SUMMARY_JSON.exists()
    assert ML_FEASIBILITY_JSON.exists()

    with open(DATASET_INVENTORY_JSON, "r", encoding="utf-8") as f:
        inv = json.load(f)
    assert inv["metadata_records_total"] == 904
    assert inv["locally_available_cubes_count"] == 3
    assert inv["missing_cubes_count"] == 901

    with open(BIOLOGICAL_SUMMARY_JSON, "r", encoding="utf-8") as f:
        bio = json.load(f)
    assert bio["unique_biological_plants_count"] == 49
    assert bio["pathogen_plant_distribution"]["K"] == 9

    with open(ML_FEASIBILITY_JSON, "r", encoding="utf-8") as f:
        ml = json.load(f)
    assert ml["independent_biological_units"] == 49
    assert "binary_disease_classification" in ml["tasks_evaluation"]
    assert ml["tasks_evaluation"]["time_series_disease_risk_forecasting"]["local_feasibility"] == "SCIENTIFICALLY INVALID"
