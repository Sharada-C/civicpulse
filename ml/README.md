# ML — CivicPulse

Three components. Nothing here is trained yet — these are the scaffolds and the intended methodology.

## 1. Severity classification (`training/train_severity.py`)

- **Input:** category, description (basic NLP features), location, historical complaint count for that location/category, time-of-year, repeat count.
- **Output:** LOW / MEDIUM / HIGH / CRITICAL.
- **Models compared, not assumed:** Logistic Regression (baseline/interpretability) → Random Forest → XGBoost. Log accuracy/F1/confusion matrix for all three in `notebooks/` before picking one for `inference/`.

## 2. Resolution-time regression (`training/train_resolution_time.py`)

- **Input:** category, department, severity, location, current departmental workload.
- **Output:** predicted resolution time in days.
- **Metrics:** MAE, RMSE, R² — report all three, since MAE alone can hide systematic bias.

## 3. Hotspot detection (`training/run_dbscan.py`)

- **Unsupervised.** DBSCAN over (latitude, longitude), because civic hotspots are not circular and DBSCAN doesn't assume a fixed cluster count or shape, unlike k-means.
- Output: cluster assignments + noise points; combine with complaint volume/severity/growth for the Priority Engine (see `sql/analytics/priority_score.sql`).

## Directory layout

```
ml/
├── notebooks/    exploratory analysis + model comparison, one notebook per model
├── training/     training scripts that produce a serialized model in models/
├── models/       versioned serialized models (.pkl / .json) — gitignored except a small demo model
└── inference/    thin prediction functions imported by backend/app/ml/inference.py
```

## Before training anything

Do the EDA first (README §10-11 in the original blueprint) — which categories dominate, which wards cluster, seasonal patterns — so feature choices are justified rather than guessed. Put that analysis in `notebooks/01_eda.ipynb`.
