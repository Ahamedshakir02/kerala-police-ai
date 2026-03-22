from sqlalchemy import Column, String, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class OfficerRole(str, enum.Enum):
    CONSTABLE = "constable"
    SUB_INSPECTOR = "sub_inspector"
    INSPECTOR = "inspector"
    DSP = "dsp"
    SP = "sp"
    ADMIN = "admin"


class Officer(Base):
    __tablename__ = "officers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    station = Column(String(100), nullable=False)
    district = Column(String(50), nullable=False)
    role = Column(SAEnum(OfficerRole), default=OfficerRole.SUB_INSPECTOR, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    phone = Column(String(15), nullable=True)

    firs = relationship("FIR", back_populates="officer", lazy="select")
