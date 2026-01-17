"""
Rainstaff v2 - Employee Model
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, Text
from sqlalchemy.sql import func
from datetime import datetime

from backend.database import Base


class Employee(Base):
    """Employee model"""
    
    __tablename__ = "employees"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Personal Information
    full_name = Column(String(100), nullable=False, index=True)
    tc_no = Column(String(11), unique=True, nullable=True)  # Turkish ID number
    birth_date = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    
    # Employment
    employee_no = Column(String(50), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Location
    region = Column(String(50), nullable=False, index=True)
    
    # Shift Template (if any)
    shift_template_id = Column(Integer, nullable=True)  # FK to shift_templates
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False)
    updated_at = Column(String(50), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.full_name}', no='{self.employee_no}', region='{self.region}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "tc_no": self.tc_no,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "phone": self.phone,
            "email": self.email,
            "employee_no": self.employee_no,
            "department": self.department,
            "position": self.position,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "termination_date": self.termination_date.isoformat() if self.termination_date else None,
            "is_active": self.is_active,
            "region": self.region,
            "notes": self.notes,
            "created_at": self.created_at,
        }
