"""
Data quality checks matching README §22:
  - complaint_id unique?
  - coordinates valid?
  - category valid?
  - created_at valid?
  - resolution_time not negative?
  - required fields missing?

Returns (clean_dataframe, report_dict) so the ingestion script can log a report like:
  Valid: 97841 | Duplicates: 1243 | Invalid: 916 | Missing: <n>
"""
import pandas as pd

REQUIRED_FIELDS = [
    "complaint_id",
    "created_at",
    "category",
    "latitude",
    "longitude",
    "ward"
]

VALID_CATEGORIES = {
    "POTHOLE",
    "STREETLIGHT",
    "GARBAGE",
    "WATER_LEAK",
    "DRAINAGE",
    "ILLEGAL_PARKING"
}

VALID_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED"
}

VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL"
}

LAT_BOUNDS = (12.85, 13.10)
LON_BOUNDS = (77.45, 77.75)


def validate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    original_count = len(df)

    # 1. Missing required fields
    missing_mask = df[REQUIRED_FIELDS].isnull().any(axis=1)
    missing_count = int(missing_mask.sum())
    df = df[~missing_mask].copy()

    # 2. Duplicate complaint_id
    duplicate_mask = df.duplicated(subset=["complaint_id"], keep="first")
    duplicate_count = int(duplicate_mask.sum())
    df = df[~duplicate_mask].copy()

    # 3. Category normalization + validity
    df["category"] = df["category"].str.strip().str.upper().str.replace(r"[\s-]+", "_", regex=True)
    invalid_category_mask = ~df["category"].isin(VALID_CATEGORIES)

    invalid_status_mask = pd.Series(False, index=df.index)

    if "status" in df.columns:
        df["status"] = df["status"].str.strip().str.upper()
        invalid_status_mask = ~df["status"].isin(VALID_STATUSES)

    invalid_severity_mask = pd.Series(False, index=df.index)

    if "severity" in df.columns:
        df["severity"] = df["severity"].str.strip().str.upper()
        invalid_severity_mask = ~df["severity"].isin(VALID_SEVERITIES)

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # 4. Coordinate bounds
    invalid_coords_mask = (
        ~df["latitude"].between(*LAT_BOUNDS) | ~df["longitude"].between(*LON_BOUNDS)
    )

    # 5. created_at parses as a valid datetime
    parsed_dates = pd.to_datetime(df["created_at"], errors="coerce")
    invalid_date_mask = parsed_dates.isna()

    # 6. resolution_time not negative (if resolved_at present)
    invalid_resolution_mask = pd.Series(False, index=df.index)
    if "resolved_at" in df.columns:
        resolved = pd.to_datetime(df["resolved_at"], errors="coerce")
        has_resolution = resolved.notna()
        negative = has_resolution & (resolved < parsed_dates)
        invalid_resolution_mask = negative

        invalid_status_resolution_mask = pd.Series(False, index=df.index)

        if "status" in df.columns and "resolved_at" in df.columns:
            resolved = pd.to_datetime(df["resolved_at"], errors="coerce")

            invalid_status_resolution_mask = (
                df["status"].isin(["RESOLVED", "CLOSED"]) & resolved.isna()
            ) | (
                df["status"].isin(["OPEN", "IN_PROGRESS"]) & resolved.notna()
            )

    invalid_mask = (
        invalid_category_mask |
        invalid_coords_mask |
        invalid_date_mask |
        invalid_resolution_mask |
        invalid_status_mask |
        invalid_severity_mask |
        invalid_status_resolution_mask
    )


    
    invalid_count = int(invalid_mask.sum())
    clean_df = df[~invalid_mask].copy()

    report = {
        "received": original_count,
        "valid": len(clean_df),
        "duplicates": duplicate_count,
        "invalid": invalid_count,
        "missing": missing_count,
    }
    return clean_df, report
