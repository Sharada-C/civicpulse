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
_severity_preprocessor = None
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
    global _severity_preprocessor
    global _severity_target_encoder

    if _severity_model is None:

        _severity_model = _load_model(
            "severity_model.joblib"
        )

        _severity_preprocessor = _load_model(
            "severity_preprocessor.joblib"
        )

        _severity_target_encoder = _load_model(
            "severity_target_encoder.joblib"
        )

    # --------------------------------------------------------
    # Fallback if trained model isn't available
    # --------------------------------------------------------

    if (
        _severity_model is None
        or _severity_preprocessor is None
        or _severity_target_encoder is None
    ):

        if features.get("repeat_count", 0) >= 5:
            return "CRITICAL"

        if features.get("repeat_count", 0) >= 2:
            return "HIGH"

        return "MEDIUM"

    # --------------------------------------------------------
    # Build features
    #
    # These MUST match train_severity.py
    # --------------------------------------------------------

    X = pd.DataFrame(
        [{
            "category": features.get(
                "category",
                "POTHOLE",
            ),

            "repeat_count": features.get(
                "repeat_count",
                0,
            ),

            "category_30d_count": features.get(
                "category_30d_count",
                0,
            ),

            "ward_30d_count": features.get(
                "ward_30d_count",
                0,
            ),

            "ward_workload": features.get(
                "ward_workload",
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
        }]
    )

    # --------------------------------------------------------
    # Apply the SAME preprocessing used during training
    # --------------------------------------------------------

    X_processed = (
        _severity_preprocessor.transform(X)
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    prediction = _severity_model.predict(
        X_processed
    )[0]

    # --------------------------------------------------------
    # Decode target
    # --------------------------------------------------------

    return str(
        _severity_target_encoder.inverse_transform(
            [int(prediction)]
        )[0]
    )


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
