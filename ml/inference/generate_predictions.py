"""
Generate ML predictions for existing complaints.

Outputs:
    data/processed/complaint_predictions.csv

Uses the exact preprocessing objects saved during model training.
"""

from pathlib import Path

import joblib
import pandas as pd


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "complaints_features.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "models"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "complaint_predictions.csv"
)


# ------------------------------------------------------------
# Load models and preprocessing objects
# ------------------------------------------------------------

severity_model = joblib.load(
    MODEL_DIR / "severity_model.joblib"
)

severity_preprocessor = joblib.load(
    MODEL_DIR / "severity_preprocessor.joblib"
)

severity_target_encoder = joblib.load(
    MODEL_DIR / "severity_target_encoder.joblib"
)

resolution_model = joblib.load(
    MODEL_DIR / "resolution_model.joblib"
)

resolution_preprocessor = joblib.load(
    MODEL_DIR / "resolution_preprocessor.joblib"
)


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

print(
    f"Reading {DATA_FILE}..."
)

df = pd.read_csv(
    DATA_FILE
)

print(
    f"Loaded {len(df)} complaints."
)


# ------------------------------------------------------------
# Severity prediction
# ------------------------------------------------------------

print(
    "Generating severity predictions..."
)

severity_features = pd.DataFrame({
    "category": df["category"],
    "repeat_count": df["repeat_count"].fillna(0),
    "category_30d_count": df["category_30d_count"].fillna(0),
    "ward_30d_count": df["ward_30d_count"].fillna(0),
    "ward_workload": df["ward_workload"].fillna(0),
    "description_length": df["description_length"].fillna(0),
    "hour_of_day": df["hour_of_day"].fillna(0),
})


severity_processed = (
    severity_preprocessor.transform(
        severity_features
    )
)


severity_prediction_encoded = (
    severity_model.predict(
        severity_processed
    )
)


df["predicted_severity"] = (
    severity_target_encoder.inverse_transform(
        severity_prediction_encoded.astype(int)
    )
)


# ------------------------------------------------------------
# Resolution-time prediction
# ------------------------------------------------------------

print(
    "Generating resolution-time predictions..."
)

resolution_features = pd.DataFrame({
    "repeat_count": df["repeat_count"].fillna(0),
    "description_length": df["description_length"].fillna(0),
    "hour_of_day": df["hour_of_day"].fillna(0),
    "day_of_week": df["day_of_week"].fillna(0),
    "month": df["month"].fillna(1),
    "ward_workload": df["ward_workload"].fillna(0),
    "category": df["category"],
    "department": df["department"],
    "severity": df["severity"],
    "ward": df["ward"],
})


resolution_processed = (
    resolution_preprocessor.transform(
        resolution_features
    )
)


resolution_predictions = (
    resolution_model.predict(
        resolution_processed
    )
)


df["predicted_resolution_days"] = (
    resolution_predictions
)


df["predicted_resolution_days"] = (
    df["predicted_resolution_days"]
    .clip(lower=0)
    .round(2)
)


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

output_columns = [
    "complaint_id",
    "predicted_severity",
    "predicted_resolution_days",
]


predictions = df[
    output_columns
].copy()


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


predictions.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print()

print(
    "=" * 60
)

print(
    "PREDICTION GENERATION COMPLETE"
)

print(
    "=" * 60
)

print(
    f"Predictions generated: {len(predictions)}"
)

print(
    f"Output: {OUTPUT_FILE}"
)

print()

print(
    "Predicted severity distribution:"
)

print(
    predictions[
        "predicted_severity"
    ]
    .value_counts()
    .sort_index()
)

print()

print(
    "Predicted resolution time:"
)

print(
    predictions[
        "predicted_resolution_days"
    ].describe()
)