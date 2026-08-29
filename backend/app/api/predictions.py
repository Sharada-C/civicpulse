from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ml.inference import predict_resolution_time, predict_severity
from app.schemas.complaint import Severity


router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["predictions"],
)


class SeverityInput(BaseModel):
    category: str
    ward_code: str

    repeat_count: int = Field(
        default=0,
        ge=0,
    )

    category_30d_count: int = Field(
        default=0,
        ge=0,
    )

    ward_30d_count: int = Field(
        default=0,
        ge=0,
    )

    ward_workload: int = Field(
        default=0,
        ge=0,
    )

    description_length: int = Field(
        default=0,
        ge=0,
    )

    hour_of_day: int = Field(
        default=0,
        ge=0,
        le=23,
    )


class ResolutionInput(BaseModel):
    category: str
    department: str
    severity: Severity
    ward_code: str

    repeat_count: int = Field(
        default=0,
        ge=0,
    )

    description_length: int = Field(
        default=0,
        ge=0,
    )

    hour_of_day: int = Field(
        default=0,
        ge=0,
        le=23,
    )

    day_of_week: int = Field(
        default=0,
        ge=0,
        le=6,
    )

    month: int = Field(
        default=1,
        ge=1,
        le=12,
    )

    ward_workload: int = Field(
        default=0,
        ge=0,
    )


@router.post("/severity")
def severity(payload: SeverityInput):
    result = predict_severity(
        payload.model_dump()
    )

    return {
        "predicted_severity": result
    }


@router.post("/resolution-time")
def resolution_time(payload: ResolutionInput):
    days = predict_resolution_time(
        payload.model_dump()
    )

    return {
        "predicted_resolution_days": days
    }
