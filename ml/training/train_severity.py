"""
Trains and compares Logistic Regression, Random Forest, and XGBoost
for severity classification.

Usage:
    python ml/training/train_severity.py \
        --data data/processed/complaints_features.csv
"""

import argparse
import os

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None
    print(
        "XGBoost unavailable; continuing with Logistic Regression "
        "and Random Forest."
    )


CATEGORICAL_FEATURES = [
    "category",
]

NUMERIC_FEATURES = [
    "repeat_count",
    "category_30d_count",
    "ward_30d_count",
    "ward_workload",
    "description_length",
    "hour_of_day",
]

TARGET_COLUMN = "severity"


def build_models():
    """
    Build the models used for comparison.
    """
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=2000,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
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
    out_dir: str = "ml/models",
):
    print(f"Reading {data_path}...")

    df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} complaints.")

    # ---------------------------------------------------------
    # Features
    # ---------------------------------------------------------

    X = df[
        CATEGORICAL_FEATURES
        + NUMERIC_FEATURES
    ]

    # ---------------------------------------------------------
    # Encode target
    # ---------------------------------------------------------

    target_encoder = LabelEncoder()

    y = target_encoder.fit_transform(
        df[TARGET_COLUMN]
    )

    class_names = target_encoder.classes_

    print("\nSeverity classes:")

    for encoded_value, class_name in enumerate(class_names):
        print(
            f"  {class_name} -> {encoded_value}"
        )

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

    print(
        f"\nTraining rows: {len(X_train)}"
    )

    print(
        f"Testing rows: {len(X_test)}"
    )

    # ---------------------------------------------------------
    # Preprocessing
    #
    # category is one-hot encoded because it is nominal.
    # repeat_count remains numeric.
    # ---------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "category",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    X_train_processed = preprocessor.fit_transform(
        X_train
    )

    X_test_processed = preprocessor.transform(
        X_test
    )

    scaler = StandardScaler(with_mean=False)

    X_train_scaled = scaler.fit_transform(X_train_processed)
    X_test_scaled = scaler.transform(X_test_processed)

    print(
        "\nProcessed feature shape:"
    )

    print(
        f"  Training: {X_train_processed.shape}"
    )

    print(
        f"  Testing : {X_test_processed.shape}"
    )

    # ---------------------------------------------------------
    # Build models
    # ---------------------------------------------------------

    models = build_models()

    results = {}

    # ---------------------------------------------------------
    # Train and evaluate models
    # ---------------------------------------------------------

    for name, model in models.items():

        print(f"\n{'=' * 60}")
        print(f"=== {name} ===")
        print(f"{'=' * 60}")

        if name == "logistic_regression":
            model.fit(
                X_train_scaled,
                y_train,
            )

            preds = model.predict(
                X_test_scaled
            )

        else:
            model.fit(
                X_train_processed,
                y_train,
            )

            preds = model.predict(
                X_test_processed
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

        macro_f1 = report["macro avg"]["f1-score"]

        results[name] = {
            "weighted_f1": weighted_f1,
            "macro_f1": macro_f1,
        }

        print(
            f"Weighted F1: {weighted_f1:.3f}"
        )

        print(
            f"Macro F1:    {macro_f1:.3f}"
        )

    # ---------------------------------------------------------
    # Compare models
    # ---------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "MODEL COMPARISON"
    )

    print(
        "=" * 60
    )

    for name, metrics in results.items():

        print(
            f"{name:25s}"
            f" Weighted F1 = {metrics['weighted_f1']:.3f}"
            f" | Macro F1 = {metrics['macro_f1']:.3f}"
        )

    # ---------------------------------------------------------
    # Select best model
    #
    # Weighted F1 is used as the primary metric.
    # ---------------------------------------------------------

    best_model_name = max(
        results,
        key=lambda name: results[name]["weighted_f1"],
    )

    best_score = results[
        best_model_name
    ]["weighted_f1"]

    print(
        "\n" + "=" * 60
    )

    print(
        f"Best model by weighted F1: "
        f"{best_model_name} ({best_score:.3f})"
    )

    print(
        "=" * 60
    )

    best_model = models[
        best_model_name
    ]

    # ---------------------------------------------------------
    # Create output directory
    # ---------------------------------------------------------

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Save model
    # ---------------------------------------------------------

    joblib.dump(
        best_model,
        os.path.join(
            out_dir,
            "severity_model.joblib",
        ),
    )

    # ---------------------------------------------------------
    # Save preprocessing pipeline
    # ---------------------------------------------------------

    joblib.dump(
        preprocessor,
        os.path.join(
            out_dir,
            "severity_preprocessor.joblib",
        ),
    )

    # ---------------------------------------------------------
    # Save target encoder
    # ---------------------------------------------------------

    joblib.dump(
        target_encoder,
        os.path.join(
            out_dir,
            "severity_target_encoder.joblib",
        ),
    )

    print(
        "\nSaved files:"
    )

    print(
        f"  {out_dir}/severity_model.joblib"
    )

    print(
        f"  {out_dir}/severity_preprocessor.joblib"
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
        args.out_dir,
    )
