
from pathlib import Path
import numpy as np
import csv

DATA_DIR = Path("data/raw/tomato_botrytis")

files = ["2436.npz", "2973.npz", "3079.npz"]

print("=" * 60)
print("TOMATO BOTRYTIS DATASET INSPECTION")
print("=" * 60)

for filename in files:
    file_path = DATA_DIR / filename

    print(f"\nFILE: {filename}")

    if not file_path.exists():
        print("ERROR: File not found!")
        continue

    try:
        with np.load(file_path, allow_pickle=False) as data:
            print("Available arrays:", data.files)

            for key in data.files:
                array = data[key]

                print(f"\nArray: {key}")
                print("Shape:", array.shape)
                print("Dimensions:", array.ndim)
                print("Data type:", array.dtype)

                if np.issubdtype(array.dtype, np.number):
                    finite_values = array[np.isfinite(array)]

                    if finite_values.size:
                        print("Minimum:", finite_values.min())
                        print("Maximum:", finite_values.max())
                        print("Mean:", finite_values.mean())
                    else:
                        print("No finite numeric values found.")

    except Exception as error:
        print("Inspection error:", error)

metadata_path = DATA_DIR / "metadata.tsv"

print("\n" + "=" * 60)
print("METADATA INSPECTION")
print("=" * 60)

if metadata_path.exists():
    with open(metadata_path, "r", encoding="utf-8-sig") as file:
        reader = csv.reader(file, delimiter="\t")

        for index, row in enumerate(reader):
            print(row)

            if index >= 4:
                break
else:
    print("metadata.tsv not found.")

print("\nInspection completed.")

