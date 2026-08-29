"""
Grounded query functions used by ai/tools/router.py.

Each function takes typed parameters (never raw user text), runs a
parameterized query against the warehouse, and returns plain data —
no LLM calls happen in this file. These are unit-testable independently
of the AI layer; see backend/tests for the pattern to follow.
"""
from sqlalchemy import text
from app.db.session import SessionLocal  # reuse the backend's DB session


def get_ward_summary(ward_code: str) -> dict:
    query = text("""
        SELECT
            dl.ward_name,
            COUNT(*)                                                    AS complaints,
            SUM(CASE WHEN fc.severity_score >= 0.75 THEN 1 ELSE 0 END)  AS critical,
            SUM(CASE WHEN fc.status = 'OPEN' THEN 1 ELSE 0 END)         AS backlog,
            ROUND(AVG(fc.resolution_time_days), 1)                      AS avg_resolution_days
        FROM fact_complaints fc
        JOIN dim_location dl ON fc.location_key = dl.location_key
        WHERE dl.ward_code = :ward_code
        GROUP BY dl.ward_name
    """)
    with SessionLocal() as db:
        row = db.execute(query, {"ward_code": ward_code}).mappings().first()
    return dict(row) if row else {"error": f"No data for ward {ward_code}"}


def get_top_hotspots(n: int = 5) -> list[dict]:
    query = text("""
        SELECT dl.ward_name, COUNT(*) AS complaint_count
        FROM fact_complaints fc
        JOIN dim_location dl ON fc.location_key = dl.location_key
        GROUP BY dl.ward_name
        ORDER BY complaint_count DESC
        LIMIT :n
    """)
    with SessionLocal() as db:
        rows = db.execute(query, {"n": n}).mappings().all()
    return [dict(r) for r in rows]


def get_department_backlog() -> list[dict]:
    query = text("""
        SELECT dd.department_name, COUNT(*) AS backlog
        FROM fact_complaints fc
        JOIN dim_department dd ON fc.department_key = dd.department_key
        WHERE fc.status = 'OPEN'
        GROUP BY dd.department_name
        ORDER BY backlog DESC
    """)
    with SessionLocal() as db:
        rows = db.execute(query).mappings().all()
    return [dict(r) for r in rows]


def get_category_trend(period: str = "30d") -> list[dict]:
    # Placeholder — implement once dim_date has enough history loaded
    # to compute a genuine period-over-period growth rate.
    return [{"note": f"category_trend for period={period} not yet implemented"}]
