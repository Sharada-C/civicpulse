from pathlib import Path
import sys

import pandas as pd
from fastapi import APIRouter, Query


# Project root: D:\Projects\civicpulse
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Allow imports from the project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.training.run_dbscan import detect_hotspots, summarize  # noqa: E402  # noqa: E402


router = APIRouter(
    prefix="/api/v1/hotspots",
    tags=["hotspots"],
)


DATA_FILE = PROJECT_ROOT / "data" / "processed" / "complaints_geo.csv"


@router.get("")
def get_hotspots(
    eps_km: float = Query(default=0.75, gt=0),
    min_samples: int = Query(default=8, ge=2),
):
    """
    Detect geographic complaint hotspots using DBSCAN.
    """

    if not DATA_FILE.exists():
        return {
            "error": "Hotspot data file not found",
            "path": str(DATA_FILE),
        }

    df = pd.read_csv(DATA_FILE)

    clustered = detect_hotspots(
        df,
        eps_km=eps_km,
        min_samples=min_samples,
    )

    summary = summarize(clustered)

    noise_count = int(
        (clustered["cluster"] == -1).sum()
    )

    return {
        "parameters": {
            "eps_km": eps_km,
            "min_samples": min_samples,
        },
        "hotspot_count": len(summary),
        "noise_points": noise_count,
        "hotspots": summary.to_dict(
            orient="records"
        ),
    }
