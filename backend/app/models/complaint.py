from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP, func
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)


class Ward(Base):
    __tablename__ = "wards"

    ward_id = Column(Integer, primary_key=True)
    ward_code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    population = Column(Integer)


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True)
    ward_id = Column(Integer, ForeignKey("wards.ward_id"))
    latitude = Column(Integer, nullable=False)
    longitude = Column(Integer, nullable=False)
    address = Column(Text)

    ward = relationship("Ward")


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    default_department_id = Column(Integer, ForeignKey("departments.department_id"))


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150))
    role = Column(String(20), nullable=False)  # CITIZEN | ANALYST | ADMIN | DEPARTMENT_OFFICER
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(Integer, primary_key=True)
    citizen_id = Column(Integer, ForeignKey("users.user_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    description = Column(Text)
    severity = Column(String(10))  # LOW | MEDIUM | HIGH | CRITICAL
    status = Column(String(20), nullable=False, default="OPEN")
    is_synthetic = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    category = relationship("Category")
    location = relationship("Location")
    department = relationship("Department")
