
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/tomato_botrytis")
metadata_path = DATA_DIR / "metadata.tsv"

df = pd.read_csv(metadata_path, sep="\t")

# Convert dates into proper datetime values.
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Each plant object is identified by these four fields.
identity_columns = [
    "replicate",
    "pathogen",
    "sample",
    "part"
]

# Count observations for each individual object.
tracks = (
    df.groupby(identity_columns)
    .agg(
        observation_count=("image_id", "count"),
        first_date=("date", "min"),
        last_date=("date", "max"),
        image_ids=("image_id", lambda x: list(x))
    )
    .reset_index()
)

tracks["duration_days"] = (
    tracks["last_date"] - tracks["first_date"]
).dt.days
print("\n21-DAY FORECAST FEASIBILITY")

print("Maximum observation duration:",
      tracks["duration_days"].max(), "days")

print("Objects tracked for at least 21 days:",
      (tracks["duration_days"] >= 21).sum())

print("Objects tracked for at least 14 days:",
      (tracks["duration_days"] >= 14).sum())

print("Objects tracked for at least 7 days:",
      (tracks["duration_days"] >= 7).sum())

print("\nLongest observation histories:")

print(
    tracks.sort_values("duration_days", ascending=False)
    .head(10)[
        identity_columns +
        ["observation_count", "first_date", "last_date",
         "duration_days"]
    ].to_string(index=False)
)

print("=" * 60)
print("LONGITUDINAL DATASET ANALYSIS")
print("=" * 60)

print("\nTotal unique plant objects:", len(tracks))

print("\nObservation count distribution:")
print(tracks["observation_count"].value_counts().sort_index())

print("\nObjects with at least 2 observations:",
      (tracks["observation_count"] >= 2).sum())

print("\nObjects with at least 5 observations:",
      (tracks["observation_count"] >= 5).sum())

print("\nObjects with at least 10 observations:",
      (tracks["observation_count"] >= 10).sum())

print("\nAverage observations per object:",
      round(tracks["observation_count"].mean(), 2))

print("\nLongitudinal statistics by pathogen:")
print(
    tracks.groupby("pathogen").agg(
        unique_objects=("part", "count"),
        average_observations=("observation_count", "mean"),
        maximum_observations=("observation_count", "max"),
        average_duration_days=("duration_days", "mean")
    ).round(2)
)

print("\nTop 10 most frequently observed objects:")
print(
    tracks.sort_values("observation_count", ascending=False)
    .head(10)[
        identity_columns +
        ["observation_count", "duration_days"]
    ].to_string(index=False)
)

# Save a reusable longitudinal tracking table.
output_path = DATA_DIR / "longitudinal_summary.csv"
tracks.to_csv(output_path, index=False)

print("\nSaved:", output_path)
print("\nAnalysis completed.")
