"""
Rainstaff v2 - Timesheet Model
Puantaj (attendance/timesheet) records
"""

from sqlalchemy import Column, Integer, String, Date, Float, Boolean, Text, ForeignKey
from sqlalchemy.sql import func

from backend.database import Base


class Timesheet(Base):
    """Timesheet/Attendance model"""
    
    __tablename__ = "timesheets"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Employee reference
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date
    work_date = Column(Date, nullable=False, index=True)
    
    # Times
    clock_in = Column(String(5), nullable=False)  # HH:MM
    clock_out = Column(String(5), nullable=False)  # HH:MM
    break_minutes = Column(Integer, default=0, nullable=False)
    
    # Calculated hours
    worked_hours = Column(Float, default=0.0, nullable=False)
    scheduled_hours = Column(Float, default=0.0, nullable=False)
    overtime_hours = Column(Float, default=0.0, nullable=False)
    night_hours = Column(Float, default=0.0, nullable=False)
    overnight_hours = Column(Float, default=0.0, nullable=False)
    
    # Special day
    is_special_day = Column(Boolean, default=False, nullable=False)
    special_normal_hours = Column(Float, default=0.0, nullable=False)
    special_overtime_hours = Column(Float, default=0.0, nullable=False)
    special_night_hours = Column(Float, default=0.0, nullable=False)
    
    # Approval
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, nullable=True)  # User ID
    approved_at = Column(String(50), nullable=True)
    
    # Location
    region = Column(String(50), nullable=False, index=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False)
    updated_at = Column(String(50), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Timesheet(id={self.id}, employee_id={self.employee_id}, date='{self.work_date}', hours={self.worked_hours})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "work_date": self.work_date.isoformat(),
            "clock_in": self.clock_in,
            "clock_out": self.clock_out,
            "break_minutes": self.break_minutes,
            "worked_hours": self.worked_hours,
            "scheduled_hours": self.scheduled_hours,
            "overtime_hours": self.overtime_hours,
            "night_hours": self.night_hours,
            "overnight_hours": self.overnight_hours,
            "is_special_day": self.is_special_day,
            "special_normal_hours": self.special_normal_hours,
            "special_overtime_hours": self.special_overtime_hours,
            "special_night_hours": self.special_night_hours,
            "is_approved": self.is_approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "region": self.region,
            "notes": self.notes,
            "created_at": self.created_at,
        }
