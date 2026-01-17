"""
Rainstaff v2 - Driver Model
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, Text
from sqlalchemy.sql import func

from backend.database import Base


class Driver(Base):
    """Driver model"""
    
    __tablename__ = "drivers"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Personal Information
    full_name = Column(String(100), nullable=False, index=True)
    tc_no = Column(String(11), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    
    # License
    license_no = Column(String(50), unique=True, nullable=False)
    license_type = Column(String(10), nullable=False)  # B, C, D, E, etc.
    license_expiry = Column(Date, nullable=True)
    
    # Employment
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Location
    region = Column(String(50), nullable=False, index=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False)
    updated_at = Column(String(50), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Driver(id={self.id}, name='{self.full_name}', license='{self.license_no}', region='{self.region}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "tc_no": self.tc_no,
            "phone": self.phone,
            "license_no": self.license_no,
            "license_type": self.license_type,
            "license_expiry": self.license_expiry.isoformat() if self.license_expiry else None,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "termination_date": self.termination_date.isoformat() if self.termination_date else None,
            "is_active": self.is_active,
            "region": self.region,
            "notes": self.notes,
            "created_at": self.created_at,
        }
