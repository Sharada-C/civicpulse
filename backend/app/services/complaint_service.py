from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate


class ComplaintService:
    """Business rules live here: the repository knows nothing about validation
    or workflow, only persistence."""

    def __init__(self, db: Session):
        self.repo = ComplaintRepository(db)

    def create_complaint(self, data: ComplaintCreate, citizen_id: int | None):
        return self.repo.create(data, citizen_id)

    def get_complaint(self, complaint_id: int):
        complaint = self.repo.get(complaint_id)
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        return complaint

    def list_complaints(self, status_filter: str | None, limit: int, offset: int):
        return self.repo.list(status=status_filter, limit=limit, offset=offset)

    def update_complaint(self, complaint_id: int, data: ComplaintUpdate):
        complaint = self.get_complaint(complaint_id)

        # Business rule: can't move a CLOSED complaint back to OPEN directly.
        if complaint.status == "CLOSED" and data.status == "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reopen a closed complaint directly; file a new complaint instead.",
            )

        import datetime
        if data.status == "RESOLVED" and complaint.status != "RESOLVED":
            complaint.resolved_at = datetime.datetime.utcnow()

        return self.repo.update(complaint, data)
