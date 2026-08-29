from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas.complaint import Severity

from app.ml.inference import predict_severity, predict_resolution_time

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


class SeverityInput(BaseModel):
    category: str
    ward_code: str
    repeat_count: int = Field(default=0, ge=0)
    description_length: int = Field(default=0, ge=0)


class ResolutionInput(BaseModel):
    category: str
    department: str
    severity: Severity
    ward_code: str


@router.post("/severity")
def severity(payload: SeverityInput):
    result = predict_severity(payload.model_dump())
    return {"predicted_severity": result}


@router.post("/resolution-time")
def resolution_time(payload: ResolutionInput):
    days = predict_resolution_time(payload.model_dump())
    return {"predicted_resolution_days": days}
