from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate


class ComplaintRepository:
    """Pure data access. No business rules here — those belong in services/."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ComplaintCreate, citizen_id: int | None) -> Complaint:
        complaint = Complaint(
            citizen_id=citizen_id,
            category_id=data.category_id,
            location_id=data.location_id,
            description=data.description,
            is_synthetic=data.is_synthetic,
            status="OPEN",
        )
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get(self, complaint_id: int) -> Complaint | None:
        return self.db.get(Complaint, complaint_id)

    def list(self, status: str | None = None, limit: int = 50, offset: int = 0) -> list[Complaint]:
        query = self.db.query(Complaint)
        if status:
            query = query.filter(Complaint.status == status)
        return query.order_by(Complaint.created_at.desc()).offset(offset).limit(limit).all()

    def update(self, complaint: Complaint, data: ComplaintUpdate) -> Complaint:
        if data.status is not None:
            complaint.status = data.status
        if data.severity is not None:
            complaint.severity = data.severity
        self.db.commit()
        self.db.refresh(complaint)
        return complaint
