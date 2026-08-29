# Notebooks

Run EDA here before training anything (see `ml/README.md`). Suggested sequence:

1. `01_eda.ipynb` — category distribution, ward-level volume, seasonality, missingness.
2. `02_severity_model_comparison.ipynb` — visualize the Logistic Regression / Random Forest / XGBoost comparison produced by `ml/training/train_severity.py`.
3. `03_resolution_time_diagnostics.ipynb` — residual plots for the regression model, not just the headline MAE/RMSE/R².
4. `04_hotspot_tuning.ipynb` — sweep `eps_km`/`min_samples` for DBSCAN and visualize resulting clusters on a map (GeoPandas + a basemap) before locking in defaults in `run_dbscan.py`.

Notebooks are gitignored by default except this README — commit specific notebooks deliberately once their output is worth keeping, to avoid bloating the repo with checkpoint noise.
