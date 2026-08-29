"""
Hotspot detection via DBSCAN over complaint (lat, long).

Unsupervised — chosen over k-means because civic hotspots aren't circular
and we don't want to pre-specify a cluster count.

Usage:
    python -m ml.training.run_dbscan --data data/processed/complaints_geo.csv
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


def detect_hotspots(df: pd.DataFrame, eps_km: float = 0.75, min_samples: int = 8) -> pd.DataFrame:
    """
    eps_km: neighborhood radius in kilometers (converted to radians for haversine metric).
    min_samples: minimum complaints to form a dense cluster.
    """
    coords = np.radians(df[["latitude", "longitude"]].values)
    earth_radius_km = 6371.0
    eps_rad = eps_km / earth_radius_km

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine")
    df = df.copy()
    df["cluster"] = db.fit_predict(coords)  # -1 == noise, not part of any hotspot
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    clustered = df[df["cluster"] != -1]
    summary = (
        clustered.groupby("cluster")
        .agg(
            complaint_count=("cluster", "size"),
            centroid_lat=("latitude", "mean"),
            centroid_long=("longitude", "mean"),
        )
        .sort_values("complaint_count", ascending=False)
        .reset_index()
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--eps-km", type=float, default=0.75)
    parser.add_argument("--min-samples", type=int, default=8)
    args = parser.parse_args()

    data = pd.read_csv(args.data)
    clustered = detect_hotspots(data, eps_km=args.eps_km, min_samples=args.min_samples)
    summary = summarize(clustered)

    print(summary.to_string(index=False))
    print(f"\nNoise points (not part of any hotspot): {(clustered['cluster'] == -1).sum()}")
