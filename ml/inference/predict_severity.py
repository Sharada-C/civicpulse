"""
Thin inference wrapper — imported by backend/app/ml/inference.py.
Loads the serialized model chosen after comparison in training/train_severity.py.
"""
import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "severity_model.pkl"


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model at {MODEL_PATH}. Run ml/training/train_severity.py first."
        )
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict(features: dict) -> str:
    """features must match FEATURE_COLUMNS in train_severity.py"""
    model = load_model()
    import pandas as pd
    row = pd.DataFrame([features])
    return model.predict(row)[0]
