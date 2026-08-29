from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """City-wide KPIs: volume, resolution rate, avg resolution time, backlog."""
    row = db.execute(text("""
        SELECT
            COUNT(*) AS total_complaints,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN status IN ('OPEN', 'IN_PROGRESS') THEN 1 ELSE 0 END) AS backlog,
            ROUND(AVG(resolution_time_days), 2) AS avg_resolution_days
        FROM fact_complaints
    """)).mappings().first()

    if not row or row["total_complaints"] == 0:
        return {"total_complaints": 0, "resolved": 0, "backlog": 0,
                "avg_resolution_days": None, "resolution_rate_pct": None}

    resolution_rate = round(100.0 * row["resolved"] / row["total_complaints"], 1)
    return {**dict(row), "resolution_rate_pct": resolution_rate}


@router.get("/hotspots")
def hotspots(db: Session = Depends(get_db), limit: int = 10):
    """Wards ranked by complaint volume — see sql/analytics/ward_ranking.sql for the full
    growth-aware version. This is the lightweight version used for the dashboard summary card."""
    rows = db.execute(text("""
        SELECT dl.ward_code, dl.ward_name, COUNT(*) AS complaint_count
        FROM fact_complaints fc
        JOIN dim_location dl ON fc.location_key = dl.location_key
        GROUP BY dl.ward_code, dl.ward_name
        ORDER BY complaint_count DESC
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]
