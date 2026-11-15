
from pathlib import Path
import csv
from collections import Counter

DATA_DIR = Path("data/raw/tomato_botrytis")

# Find the metadata file regardless of its extension.
metadata_files = list(DATA_DIR.glob("metadata.*"))

if not metadata_files:
    raise FileNotFoundError("No metadata file found.")

if len(metadata_files) > 1:
    print("Multiple metadata files found:")
    for path in metadata_files:
        print("-", path.name)
    raise RuntimeError("Keep one authoritative metadata file before proceeding.")

metadata_path = metadata_files[0]

print("Using metadata:", metadata_path.name)

with open(metadata_path, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file, delimiter="\t")
    rows = list(reader)

print("\nTOTAL METADATA RECORDS:", len(rows))

if not rows:
    raise ValueError("Metadata file contains no records.")

print("\nCOLUMNS:")
print(list(rows[0].keys()))

print("\nPATHOGEN COUNTS:")
print(Counter(row["pathogen"] for row in rows))

print("\nDATE RANGE:")
dates = sorted(row["date"] for row in rows if row.get("date"))
print("First date:", dates[0] if dates else "Unavailable")
print("Last date:", dates[-1] if dates else "Unavailable")

print("\nSAMPLE CUBE RECORDS:")

sample_ids = ["2436", "2973", "3079"]

for image_id in sample_ids:
    matches = [
        row for row in rows
        if row["image_id"].strip() == image_id
    ]

    print(f"\nImage ID: {image_id}")

    if not matches:
        print("No matching metadata record found.")
        continue

    for row in matches:
        for key, value in row.items():
            print(f"{key}: {value}")

print("\nLONGITUDINAL OBJECT EXAMPLE:")

if rows:
    first = rows[0]

    identity = (
        first["replicate"],
        first["pathogen"],
        first["sample"],
        first["part"]
    )

    print("Tracking identity:", identity)

    related = [
        row for row in rows
        if (
            row["replicate"],
            row["pathogen"],
            row["sample"],
            row["part"]
        ) == identity
    ]

    related.sort(key=lambda row: row["date"])

    for row in related:
        print(row["image_id"], row["date"], row["pathogen"])

print("\nMetadata inspection completed.")
