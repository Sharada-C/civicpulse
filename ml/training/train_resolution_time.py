"""
Trains and compares regression models for complaint resolution time.

Target:
    resolution_time_days

Usage:
    python ml/training/train_resolution_time.py ^
        --data data/processed/complaints_features.csv
"""

import argparse
import os

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder


# -------------------------------------------------------------------
# Features
# -------------------------------------------------------------------

NUMERIC_FEATURES = [
    "repeat_count",
    "description_length",
    "hour_of_day",
    "day_of_week",
    "month",
    "ward_workload",
]

CATEGORICAL_FEATURES = [
    "category",
    "department",
    "severity",
    "ward",
]

TARGET_COLUMN = "resolution_time_days"


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

MODELS = {
    "linear_regression": LinearRegression(),

    "random_forest": RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        min_samples_leaf=2,
    ),

    "gradient_boosting": GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    ),
}


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main(
    data_path: str,
    out_dir: str = "ml/models",
):
    print(f"Reading {data_path}...")

    df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} complaints.")

    # ---------------------------------------------------------------
    # Keep only complaints with known resolution time
    # ---------------------------------------------------------------

    df = df.dropna(
        subset=[TARGET_COLUMN]
    ).copy()

    print(
        f"Resolved complaints available for training: {len(df)}"
    )

    if len(df) < 20:
        raise ValueError(
            "Not enough resolved complaints to train the model."
        )

    # ---------------------------------------------------------------
    # Features and target
    # ---------------------------------------------------------------

    feature_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    X = df[feature_columns]

    y = df[TARGET_COLUMN]

    # ---------------------------------------------------------------
    # Train/test split
    # ---------------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    print(
        f"Training rows: {len(X_train)}"
    )

    print(
        f"Testing rows: {len(X_test)}"
    )

    # ---------------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Train models
    # ---------------------------------------------------------------

    results = {}

    trained_models = {}

    for name, model in MODELS.items():

        print()
        print("=" * 60)
        print(f"=== {name} ===")
        print("=" * 60)

        model.fit(
            X_train_processed,
            y_train,
        )

        predictions = model.predict(
            X_test_processed
        )

        # -----------------------------------------------------------
        # Metrics
        # -----------------------------------------------------------

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
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        }

        trained_models[name] = model

        print(
            f"MAE :  {mae:.3f} days"
        )

        print(
            f"RMSE:  {rmse:.3f} days"
        )

        print(
            f"R²  :  {r2:.3f}"
        )

    # ---------------------------------------------------------------
    # Model comparison
    #
    # Lower MAE is the primary selection metric.
    # ---------------------------------------------------------------

    best_model_name = min(
        results,
        key=lambda name: results[name]["mae"],
    )

    best_model = trained_models[
        best_model_name
    ]

    best_metrics = results[
        best_model_name
    ]

    # ---------------------------------------------------------------
    # Print comparison
    # ---------------------------------------------------------------

    print()
    print("=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)

    print(
        f"{'Model':25s}"
        f"{'MAE':>10s}"
        f"{'RMSE':>10s}"
        f"{'R²':>10s}"
    )

    print("-" * 60)

    for name, metrics in results.items():

        print(
            f"{name:25s}"
            f"{metrics['mae']:10.3f}"
            f"{metrics['rmse']:10.3f}"
            f"{metrics['r2']:10.3f}"
        )

    print()
    print(
        f"Best model by MAE: "
        f"{best_model_name}"
    )

    print(
        f"MAE:  {best_metrics['mae']:.3f} days"
    )

    print(
        f"RMSE: {best_metrics['rmse']:.3f} days"
    )

    print(
        f"R²:   {best_metrics['r2']:.3f}"
    )

    # ---------------------------------------------------------------
    # Save model + preprocessing pipeline
    # ---------------------------------------------------------------

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    joblib.dump(
        best_model,
        os.path.join(
            out_dir,
            "resolution_model.joblib",
        ),
    )

    joblib.dump(
        preprocessor,
        os.path.join(
            out_dir,
            "resolution_preprocessor.joblib",
        ),
    )

    print()
    print("Saved files:")

    print(
        f"  {out_dir}/resolution_model.joblib"
    )

    print(
        f"  {out_dir}/resolution_preprocessor.joblib"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        required=True,
    )

    parser.add_argument(
        "--out-dir",
        default="ml/models",
    )

    args = parser.parse_args()

    main(
        args.data,
        args.out_dir,
    )