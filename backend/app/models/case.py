from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    CHARGE_SHEET_FILED = "charge_sheet_filed"
    COURT_TRIAL = "court_trial"
    CLOSED = "closed"
    ACQUITTED = "acquitted"


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("firs.id"), nullable=False, unique=True)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    investigating_officer_id = Column(UUID(as_uuid=True), ForeignKey("officers.id"), nullable=True)
    
    # Investigation notes
    notes = Column(Text, nullable=True)
    
    # Court tracking
    court_name = Column(String(200), nullable=True)
    court_case_number = Column(String(100), nullable=True)
    next_hearing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    fir = relationship("FIR", back_populates="case")
    investigating_officer = relationship("Officer", foreign_keys=[investigating_officer_id])
