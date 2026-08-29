"""
Evaluate CivicPulse ML models against simple baselines.

Outputs:
    ml/models/model_metrics.json

Metrics:
    Severity:
        accuracy
        weighted_precision
        weighted_recall
        weighted_f1

    Resolution time:
        MAE
        RMSE
        R2

The evaluation uses the same feature preparation and model
configurations as the training scripts.
"""

import json
import os

import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from ml.training.train_severity import (
    FEATURE_COLUMNS,
    TARGET_COLUMN as SEVERITY_TARGET,
    build_models,
    prepare_features,
)

from ml.training.train_resolution_time import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    MODELS as RESOLUTION_MODELS,
    TARGET_COLUMN as RESOLUTION_TARGET,
)

from sklearn.compose import ColumnTransformer


DATA_FILE = "data/processed/complaints_features.csv"
OUTPUT_FILE = "ml/models/model_metrics.json"


def evaluate_severity(df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("SEVERITY MODEL EVALUATION")
    print("=" * 60)

    df, category_encoder, ward_encoder = prepare_features(df)

    X = df[FEATURE_COLUMNS]

    from sklearn.preprocessing import LabelEncoder

    target_encoder = LabelEncoder()
    y = target_encoder.fit_transform(df[SEVERITY_TARGET])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    models = build_models()

    results = {}

    # ---------------------------------------------------------
    # Baseline
    # ---------------------------------------------------------

    baseline = DummyClassifier(
        strategy="most_frequent"
    )

    baseline.fit(X_train, y_train)

    baseline_predictions = baseline.predict(X_test)

    baseline_report = classification_report(
        y_test,
        baseline_predictions,
        output_dict=True,
        zero_division=0,
    )

    results["baseline_most_frequent"] = {
        "accuracy": round(
            accuracy_score(y_test, baseline_predictions),
            4,
        ),
        "weighted_precision": round(
            baseline_report["weighted avg"]["precision"],
            4,
        ),
        "weighted_recall": round(
            baseline_report["weighted avg"]["recall"],
            4,
        ),
        "weighted_f1": round(
            baseline_report["weighted avg"]["f1-score"],
            4,
        ),
    }

    # ---------------------------------------------------------
    # ML models
    # ---------------------------------------------------------

    for name, model in models.items():

        print(f"\nEvaluating {name}...")

        if name == "logistic_regression":

            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()

            X_train_processed = scaler.fit_transform(X_train)
            X_test_processed = scaler.transform(X_test)

        else:
            X_train_processed = X_train
            X_test_processed = X_test

        model.fit(
            X_train_processed,
            y_train,
        )

        predictions = model.predict(
            X_test_processed
        )

        report = classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        )

        results[name] = {
            "accuracy": round(
                accuracy_score(y_test, predictions),
                4,
            ),
            "weighted_precision": round(
                report["weighted avg"]["precision"],
                4,
            ),
            "weighted_recall": round(
                report["weighted avg"]["recall"],
                4,
            ),
            "weighted_f1": round(
                report["weighted avg"]["f1-score"],
                4,
            ),
        }

    return results


def evaluate_resolution(df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("RESOLUTION-TIME MODEL EVALUATION")
    print("=" * 60)

    df = df.dropna(
        subset=[RESOLUTION_TARGET]
    ).copy()

    feature_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    X = df[feature_columns]
    y = df[RESOLUTION_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    results = {}

    # ---------------------------------------------------------
    # Baseline: predict training-set mean
    # ---------------------------------------------------------

    baseline = DummyRegressor(
        strategy="mean"
    )

    baseline.fit(
        X_train,
        y_train,
    )

    baseline_predictions = baseline.predict(
        X_test
    )

    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions,
    )

    baseline_rmse = mean_squared_error(
        y_test,
        baseline_predictions,
    ) ** 0.5

    baseline_r2 = r2_score(
        y_test,
        baseline_predictions,
    )

    results["baseline_mean"] = {
        "mae": round(baseline_mae, 4),
        "rmse": round(baseline_rmse, 4),
        "r2": round(baseline_r2, 4),
    }

    # ---------------------------------------------------------
    # ML models
    # ---------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
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

    for name, model_template in RESOLUTION_MODELS.items():

        print(f"\nEvaluating {name}...")

        # Create a fresh model so models are independent.
        model = model_template.__class__(
            **model_template.get_params()
        )

        model.fit(
            X_train_processed,
            y_train,
        )

        predictions = model.predict(
            X_test_processed
        )

        mae = mean_absolute_error(
            y_test,
            predictions,
        )

        rmse = mean_squared_error(
            y_test,
            predictions,
        ) ** 0.5

        r2 = r2_score(
            y_test,
            predictions,
        )

        results[name] = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
        }

    return results


def main():
    print(f"Reading {DATA_FILE}...")

    df = pd.read_csv(DATA_FILE)

    print(f"Loaded {len(df)} complaints.")

    severity_results = evaluate_severity(
        df.copy()
    )

    resolution_results = evaluate_resolution(
        df.copy()
    )

    metrics = {
        "dataset": DATA_FILE,
        "dataset_rows": len(df),
        "severity": severity_results,
        "resolution_time": resolution_results,
    }

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)

    print("\nSeverity:")
    for name, metrics_data in severity_results.items():
        print(
            f"{name:30s}"
            f"F1 = {metrics_data['weighted_f1']:.4f}"
        )

    print("\nResolution Time:")
    for name, metrics_data in resolution_results.items():
        print(
            f"{name:30s}"
            f"MAE = {metrics_data['mae']:.4f}"
        )

    print(f"\nSaved metrics to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()