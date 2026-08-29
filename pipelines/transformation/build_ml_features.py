"""
Builds ML-ready feature datasets from the raw synthetic complaints data.

Outputs:
    data/processed/complaints_features.csv
    data/processed/complaints_geo.csv
"""

from pathlib import Path

import pandas as pd


RAW_FILE = Path("data/raw/synthetic_complaints.csv")
OUTPUT_DIR = Path("data/processed")


SEVERITY_MAP = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # -----------------------------
    # Basic datetime features
    # -----------------------------
    df["created_at"] = pd.to_datetime(df["created_at"])

    df["hour_of_day"] = df["created_at"].dt.hour
    df["day_of_week"] = df["created_at"].dt.dayofweek
    df["month"] = df["created_at"].dt.month

    # -----------------------------
    # Description feature
    # -----------------------------
    df["description_length"] = (
        df["description"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    # -----------------------------
    # Historical repeat count
    #
    # A complaint is considered a repeat
    # when the same ward + category has
    # appeared previously.
    # -----------------------------
    df = df.sort_values("created_at")

    df["repeat_count"] = (
        df.groupby(["ward", "category"])
        .cumcount()
    )

    # -----------------------------
    # Ward workload
    #
    # Number of complaints associated
    # with the ward.
    # -----------------------------
    ward_counts = df["ward"].value_counts()

    df["ward_workload"] = (
        df["ward"]
        .map(ward_counts)
        .fillna(0)
        .astype(int)
    )

    # -----------------------------
    # Resolution time
    # -----------------------------
    df["resolved_at"] = pd.to_datetime(
        df["resolved_at"],
        errors="coerce",
    )

    df["resolution_time_days"] = (
        df["resolved_at"] - df["created_at"]
    ).dt.total_seconds() / 86400

    # Keep unresolved complaints as NaN
    # because they don't have an observed
    # resolution duration.
    
    # -----------------------------
    # Encoded severity
    # -----------------------------
    df["severity_encoded"] = (
        df["severity"]
        .map(SEVERITY_MAP)
    )

    return df


def main():
    print(f"Reading {RAW_FILE}...")

    df = pd.read_csv(RAW_FILE)

    print(f"Loaded {len(df)} complaints.")

    df = build_features(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Dataset for supervised ML
    feature_columns = [
        "complaint_id",
        "created_at",
        "category",
        "description",
        "ward",
        "department",
        "severity",
        "status",
        "resolved_at",
        "repeat_count",
        "description_length",
        "hour_of_day",
        "day_of_week",
        "month",
        "ward_workload",
        "resolution_time_days",
        "latitude",
        "longitude",
    ]

    features = df[feature_columns]

    features.to_csv(
        OUTPUT_DIR / "complaints_features.csv",
        index=False,
    )

    # Dataset specifically for DBSCAN
    geo_columns = [
        "complaint_id",
        "latitude",
        "longitude",
        "ward",
        "category",
        "severity",
    ]

    geo = df[geo_columns]

    geo.to_csv(
        OUTPUT_DIR / "complaints_geo.csv",
        index=False,
    )

    print()
    print("ML feature generation complete.")
    print(f"Features: {OUTPUT_DIR / 'complaints_features.csv'}")
    print(f"Geo data: {OUTPUT_DIR / 'complaints_geo.csv'}")
    print()
    print("Feature dataset shape:", features.shape)
    print("Geo dataset shape:", geo.shape)


if __name__ == "__main__":
    main()