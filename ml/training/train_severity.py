"""
Trains and compares Logistic Regression, Random Forest, and XGBoost
for severity classification.

Usage:
    python ml/training/train_severity.py --data data/processed/complaints_features.csv
"""

import argparse
import os

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None
    print(
        "XGBoost unavailable; continuing with Logistic Regression "
        "and Random Forest."
    )


FEATURE_COLUMNS = [
    "category_encoded",
    "ward_encoded",
    "repeat_count",
    "description_length",
    "hour_of_day",
]

TARGET_COLUMN = "severity"


def prepare_features(df: pd.DataFrame):
    """
    Encode categorical input features.

    Returns:
        df
        category_encoder
        ward_encoder
    """
    df = df.copy()

    category_encoder = LabelEncoder()
    ward_encoder = LabelEncoder()

    df["category_encoded"] = category_encoder.fit_transform(
        df["category"]
    )

    df["ward_encoded"] = ward_encoder.fit_transform(
        df["ward"]
    )

    return df, category_encoder, ward_encoder


def build_models():
    """
    Build the models used for comparison.
    """
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000
        ),

        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42
        ),
    }

    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric="mlogloss",
        )

    return models


def main(
    data_path: str,
    out_dir: str = "ml/models"
):
    print(f"Reading {data_path}...")

    df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} complaints.")

    # ---------------------------------------------------------
    # Feature preparation
    # ---------------------------------------------------------
    df, category_encoder, ward_encoder = prepare_features(df)

    X = df[FEATURE_COLUMNS]

    # ---------------------------------------------------------
    # Encode TARGET labels
    #
    # XGBoost requires numeric class labels.
    #
    # Example:
    # CRITICAL -> 0
    # HIGH     -> 1
    # LOW      -> 2
    # MEDIUM   -> 3
    # ---------------------------------------------------------
    target_encoder = LabelEncoder()

    y = target_encoder.fit_transform(
        df[TARGET_COLUMN]
    )

    class_names = target_encoder.classes_

    print("\nSeverity classes:")
    for encoded_value, class_name in enumerate(class_names):
        print(f"  {class_name} -> {encoded_value}")

    # ---------------------------------------------------------
    # Train/test split
    # ---------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # ---------------------------------------------------------
    # Scaling for Logistic Regression
    # ---------------------------------------------------------
    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---------------------------------------------------------
    # Build models
    # ---------------------------------------------------------
    models = build_models()

    results = {}

    # ---------------------------------------------------------
    # Train and evaluate each model
    # ---------------------------------------------------------
    for name, model in models.items():

        print(f"\n{'=' * 60}")
        print(f"=== {name} ===")
        print(f"{'=' * 60}")

        if name == "logistic_regression":

            # Logistic Regression works better with scaled features.
            model.fit(
                X_train_scaled,
                y_train
            )

            preds = model.predict(
                X_test_scaled
            )

        else:

            # Random Forest and XGBoost use the original features.
            model.fit(
                X_train,
                y_train
            )

            preds = model.predict(
                X_test
            )

        # -----------------------------------------------------
        # Classification report
        # -----------------------------------------------------
        report = classification_report(
            y_test,
            preds,
            labels=list(range(len(class_names))),
            target_names=class_names,
            output_dict=True,
            zero_division=0,
        )

        print(
            classification_report(
                y_test,
                preds,
                labels=list(range(len(class_names))),
                target_names=class_names,
                zero_division=0,
            )
        )

        weighted_f1 = report["weighted avg"]["f1-score"]

        results[name] = weighted_f1

        print(
            f"Weighted F1: {weighted_f1:.3f}"
        )

    # ---------------------------------------------------------
    # Compare models
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)

    for name, score in results.items():
        print(
            f"{name:25s} Weighted F1 = {score:.3f}"
        )

    # ---------------------------------------------------------
    # Select best model
    # ---------------------------------------------------------
    best_model_name = max(
        results,
        key=results.get
    )

    best_score = results[best_model_name]

    print("\n" + "=" * 60)
    print(
        f"Best model by weighted F1: "
        f"{best_model_name} ({best_score:.3f})"
    )
    print("=" * 60)

    best_model = models[best_model_name]

    # ---------------------------------------------------------
    # Create output directory
    # ---------------------------------------------------------
    os.makedirs(
        out_dir,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # Save model and preprocessing objects
    # ---------------------------------------------------------
    joblib.dump(
        best_model,
        os.path.join(
            out_dir,
            "severity_model.joblib"
        ),
    )

    joblib.dump(
        scaler,
        os.path.join(
            out_dir,
            "severity_scaler.joblib"
        ),
    )

    joblib.dump(
        category_encoder,
        os.path.join(
            out_dir,
            "category_encoder.joblib"
        ),
    )

    joblib.dump(
        ward_encoder,
        os.path.join(
            out_dir,
            "ward_encoder.joblib"
        ),
    )

    joblib.dump(
        target_encoder,
        os.path.join(
            out_dir,
            "severity_target_encoder.joblib"
        ),
    )

    print("\nSaved files:")

    print(
        f"  {out_dir}/severity_model.joblib"
    )

    print(
        f"  {out_dir}/severity_scaler.joblib"
    )

    print(
        f"  {out_dir}/category_encoder.joblib"
    )

    print(
        f"  {out_dir}/ward_encoder.joblib"
    )

    print(
        f"  {out_dir}/severity_target_encoder.joblib"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        required=True,
        help="Path to complaints feature CSV",
    )

    parser.add_argument(
        "--out-dir",
        default="ml/models",
        help="Directory where trained models are saved",
    )

    args = parser.parse_args()

    main(
        args.data,
        args.out_dir
    )