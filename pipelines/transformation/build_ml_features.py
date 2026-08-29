"""
Builds ML-ready feature datasets from raw synthetic complaint data.

Outputs:
    data/processed/complaints_features.csv
    data/processed/complaints_geo.csv

Historical features are calculated using only complaints that occurred
before the current complaint, preventing future-data leakage.
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

    # ---------------------------------------------------------
    # Datetime
    # ---------------------------------------------------------

    df["created_at"] = pd.to_datetime(
        df["created_at"]
    )

    df["hour_of_day"] = (
        df["created_at"].dt.hour
    )

    df["day_of_week"] = (
        df["created_at"].dt.dayofweek
    )

    df["month"] = (
        df["created_at"].dt.month
    )

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    df["description_length"] = (
        df["description"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    # ---------------------------------------------------------
    # Historical features
    #
    # IMPORTANT:
    # Features are calculated BEFORE adding the current
    # complaint to the historical state.
    # ---------------------------------------------------------

    df = df.sort_values(
        "created_at"
    ).reset_index(drop=True)

    ward_counts = {}
    ward_category_counts = {}

    category_history = {}
    ward_history = {}

    repeat_counts = []
    historical_ward_category_counts = []
    category_30d_counts = []
    ward_30d_counts = []

    for _, row in df.iterrows():

        ward = row["ward"]
        category = row["category"]
        created_at = row["created_at"]

        # -----------------------------------------------------
        # Historical repeat count
        # -----------------------------------------------------

        key = (
            ward,
            category,
        )

        repeat_count = (
            ward_category_counts.get(
                key,
                0,
            )
        )

        repeat_counts.append(
            repeat_count
        )

        # Same value represented explicitly as a separate
        # feature for model interpretability.
        historical_ward_category_counts.append(
            repeat_count
        )

        # -----------------------------------------------------
        # Category complaints in previous 30 days
        # -----------------------------------------------------

        category_events = (
            category_history.get(
                category,
                [],
            )
        )

        category_cutoff = (
            created_at
            - pd.Timedelta(days=30)
        )

        category_recent_count = sum(
            event_time > category_cutoff
            for event_time in category_events
        )

        category_30d_counts.append(
            category_recent_count
        )

        # -----------------------------------------------------
        # Ward complaints in previous 30 days
        # -----------------------------------------------------

        ward_events = (
            ward_history.get(
                ward,
                [],
            )
        )

        ward_recent_count = sum(
            event_time > category_cutoff
            for event_time in ward_events
        )

        ward_30d_counts.append(
            ward_recent_count
        )

        # -----------------------------------------------------
        # Update historical state AFTER computing features
        # -----------------------------------------------------

        ward_category_counts[key] = (
            repeat_count + 1
        )

        category_history.setdefault(
            category,
            [],
        ).append(
            created_at
        )

        ward_history.setdefault(
            ward,
            [],
        ).append(
            created_at
        )

        ward_counts[ward] = (
            ward_counts.get(
                ward,
                0,
            )
            + 1
        )

    df["repeat_count"] = repeat_counts

    df["ward_category_count"] = (
        historical_ward_category_counts
    )

    df["category_30d_count"] = (
        category_30d_counts
    )

    df["ward_30d_count"] = (
        ward_30d_counts
    )

    # ---------------------------------------------------------
    # Ward workload
    #
    # Historical workload at the time of each complaint.
    # ---------------------------------------------------------

    df["ward_workload"] = (
        df.groupby("ward")
        .cumcount()
    )

    # ---------------------------------------------------------
    # Resolution time
    # ---------------------------------------------------------

    df["resolved_at"] = pd.to_datetime(
        df["resolved_at"],
        errors="coerce",
    )

    df["resolution_time_days"] = (
        df["resolved_at"]
        - df["created_at"]
    ).dt.total_seconds() / 86400

    # ---------------------------------------------------------
    # Encoded severity
    # ---------------------------------------------------------

    df["severity_encoded"] = (
        df["severity"]
        .map(SEVERITY_MAP)
    )

    return df


def main():
    print(
        f"Reading {RAW_FILE}..."
    )

    df = pd.read_csv(
        RAW_FILE
    )

    print(
        f"Loaded {len(df)} complaints."
    )

    df = build_features(
        df
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Dataset for supervised ML
    # ---------------------------------------------------------

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
        "ward_category_count",
        "category_30d_count",
        "ward_30d_count",
        "description_length",
        "hour_of_day",
        "day_of_week",
        "month",
        "ward_workload",
        "resolution_time_days",
        "latitude",
        "longitude",
    ]

    features = df[
        feature_columns
    ]

    features.to_csv(
        OUTPUT_DIR / "complaints_features.csv",
        index=False,
    )

    # ---------------------------------------------------------
    # Dataset specifically for DBSCAN
    # ---------------------------------------------------------

    geo_columns = [
        "complaint_id",
        "latitude",
        "longitude",
        "ward",
        "category",
        "severity",
    ]

    geo = df[
        geo_columns
    ]

    geo.to_csv(
        OUTPUT_DIR / "complaints_geo.csv",
        index=False,
    )

    print()
    print(
        "ML feature generation complete."
    )

    print(
        f"Features: "
        f"{OUTPUT_DIR / 'complaints_features.csv'}"
    )

    print(
        f"Geo data: "
        f"{OUTPUT_DIR / 'complaints_geo.csv'}"
    )

    print()

    print(
        "Feature dataset shape:",
        features.shape,
    )

    print(
        "Geo dataset shape:",
        geo.shape,
    )


if __name__ == "__main__":
    main()