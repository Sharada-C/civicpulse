"""
Loads trained ML models and exposes prediction functions
used by the FastAPI backend.
"""

import os

import joblib
import pandas as pd


_MODEL_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "ml",
        "models",
    )
)


_severity_model = None
_severity_scaler = None
_category_encoder = None
_ward_encoder = None
_severity_target_encoder = None

_resolution_model = None
_resolution_preprocessor = None


def _load_model(filename: str):
    path = os.path.join(_MODEL_DIR, filename)

    if not os.path.exists(path):
        return None

    return joblib.load(path)


# ============================================================
# SEVERITY
# ============================================================

def predict_severity(features: dict) -> str:

    global _severity_model
    global _severity_scaler
    global _category_encoder
    global _ward_encoder
    global _severity_target_encoder

    if _severity_model is None:

        _severity_model = _load_model(
            "severity_model.joblib"
        )

        _severity_scaler = _load_model(
            "severity_scaler.joblib"
        )

        _category_encoder = _load_model(
            "category_encoder.joblib"
        )

        _ward_encoder = _load_model(
            "ward_encoder.joblib"
        )

        _severity_target_encoder = _load_model(
            "severity_target_encoder.joblib"
        )

    # --------------------------------------------------------
    # Fallback if trained model isn't available
    # --------------------------------------------------------

    if _severity_model is None:

        if features.get("repeat_count", 0) >= 5:
            return "CRITICAL"

        if features.get("repeat_count", 0) >= 2:
            return "HIGH"

        return "MEDIUM"

    # --------------------------------------------------------
    # Encode categorical features exactly as training
    # --------------------------------------------------------

    category = features.get(
        "category",
        "POTHOLE",
    )

    ward = features.get(
        "ward_code",
        "W001",
    )

    try:

        category_encoded = (
            _category_encoder.transform(
                [category]
            )[0]
        )

    except ValueError:

        category_encoded = 0

    try:

        ward_encoded = (
            _ward_encoder.transform(
                [ward]
            )[0]
        )

    except ValueError:

        ward_encoded = 0

    # --------------------------------------------------------
    # Build feature vector
    # --------------------------------------------------------

    X = pd.DataFrame(
        [[
            category_encoded,
            ward_encoded,
            features.get("repeat_count", 0),
            features.get("description_length", 0),
            features.get("hour_of_day", 0),
        ]],
        columns=[
            "category_encoded",
            "ward_encoded",
            "repeat_count",
            "description_length",
            "hour_of_day",
        ],
    )

    # --------------------------------------------------------
    # Logistic Regression needs scaling.
    # Other models don't.
    # --------------------------------------------------------

    model_name = type(
        _severity_model
    ).__name__

    if model_name == "LogisticRegression":

        X_input = _severity_scaler.transform(X)

    else:

        X_input = X

    prediction = _severity_model.predict(
        X_input
    )[0]

    # --------------------------------------------------------
    # Decode target
    # --------------------------------------------------------

    if _severity_target_encoder is not None:

        return str(
            _severity_target_encoder.inverse_transform(
                [int(prediction)]
            )[0]
        )

    return str(prediction)


# ============================================================
# RESOLUTION TIME
# ============================================================

def predict_resolution_time(
    features: dict,
) -> float:

    global _resolution_model
    global _resolution_preprocessor

    if _resolution_model is None:

        _resolution_model = _load_model(
            "resolution_model.joblib"
        )

        _resolution_preprocessor = _load_model(
            "resolution_preprocessor.joblib"
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if (
        _resolution_model is None
        or _resolution_preprocessor is None
    ):

        baseline = {
            "LOW": 3.0,
            "MEDIUM": 6.0,
            "HIGH": 10.0,
            "CRITICAL": 15.0,
        }

        return baseline.get(
            features.get(
                "severity",
                "MEDIUM",
            ),
            6.0,
        )

    # --------------------------------------------------------
    # Build feature dataframe
    #
    # These MUST match train_resolution_time.py
    # --------------------------------------------------------

    X = pd.DataFrame(
        [{
            "repeat_count": features.get(
                "repeat_count",
                0,
            ),

            "description_length": features.get(
                "description_length",
                0,
            ),

            "hour_of_day": features.get(
                "hour_of_day",
                0,
            ),

            "day_of_week": features.get(
                "day_of_week",
                0,
            ),

            "month": features.get(
                "month",
                1,
            ),

            "ward_workload": features.get(
                "ward_workload",
                0,
            ),

            "category": features.get(
                "category",
                "POTHOLE",
            ),

            "department": features.get(
                "department",
                "ROADS",
            ),

            "severity": features.get(
                "severity",
                "MEDIUM",
            ),

            "ward": features.get(
                "ward_code",
                "W001",
            ),
        }]
    )

    # --------------------------------------------------------
    # Apply the SAME preprocessing used during training
    # --------------------------------------------------------

    X_processed = (
        _resolution_preprocessor.transform(X)
    )

    prediction = (
        _resolution_model.predict(
            X_processed
        )[0]
    )

    # Resolution time cannot be negative.
    prediction = max(
        0.0,
        float(prediction),
    )

    return round(
        prediction,
        2,
    )
