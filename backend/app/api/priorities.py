from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/api/v1/priorities", tags=["priorities"])

_WEIGHTS = {
    "severity": 0.30,
    "frequency": 0.20,
    "growth": 0.15,
    "repeat": 0.15,
    "population": 0.10,
    "delay": 0.10,
}


@router.get("")
def ward_priorities(db: Session = Depends(get_db), limit: int = 10):

    try:
        with open("../sql/analytics/priority_score.sql", encoding="utf-8") as f:
            query = f.read()

        rows = db.execute(
            text(query),
            {"limit": limit}
        ).mappings().all()

        return {
            "weights": _WEIGHTS,
            "rankings": [dict(r) for r in rows]
        }

    except Exception as e:
        return {
            "error": type(e).__name__,
            "message": str(e)
        }
