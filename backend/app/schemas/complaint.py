from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]


class ComplaintCreate(BaseModel):
    category_id: int
    location_id: int
    description: Optional[str] = Field(default=None, max_length=2000)
    is_synthetic: bool = False


class ComplaintUpdate(BaseModel):
    status: Optional[Status] = None
    severity: Optional[Severity] = None
    note: Optional[str] = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: int
    category_id: int
    location_id: int
    department_id: Optional[int]
    description: Optional[str]
    severity: Optional[Severity]
    status: Status
    is_synthetic: bool
    created_at: datetime
    resolved_at: Optional[datetime]
