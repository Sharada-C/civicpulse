from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.complaint import User
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintOut, Status
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ComplaintService(db)
    return service.create_complaint(payload, citizen_id=user.user_id)


@router.get("", response_model=list[ComplaintOut])
def list_complaints(
    status_filter: Status | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.list_complaints(status_filter, limit, offset)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    service = ComplaintService(db)
    return service.get_complaint(complaint_id)


@router.patch("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ANALYST", "ADMIN", "DEPARTMENT_OFFICER")),
):
    service = ComplaintService(db)
    return service.update_complaint(complaint_id, payload)
