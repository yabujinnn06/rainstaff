"""
Rainstaff v2 - Vehicle Model
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func

from backend.database import Base
from shared.enums import VehicleStatus


class Vehicle(Base):
    """Vehicle model"""
    
    __tablename__ = "vehicles"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Vehicle Information
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    brand = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String(30), nullable=True)
    vin = Column(String(50), unique=True, nullable=True)  # Vehicle Identification Number
    
    # Maintenance
    current_km = Column(Integer, default=0, nullable=False)
    oil_change_km = Column(Integer, default=0, nullable=False)
    oil_interval_km = Column(Integer, default=14000, nullable=False)
    
    # Insurance & Inspection
    insurance_expiry = Column(String(10), nullable=True)  # YYYY-MM-DD
    inspection_expiry = Column(String(10), nullable=True)  # YYYY-MM-DD
    
    # Status
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.ACTIVE, nullable=False)
    
    # Location
    region = Column(String(50), nullable=False, index=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False)
    updated_at = Column(String(50), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, plate='{self.plate_number}', status='{self.status}', region='{self.region}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "plate_number": self.plate_number,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "color": self.color,
            "vin": self.vin,
            "current_km": self.current_km,
            "oil_change_km": self.oil_change_km,
            "oil_interval_km": self.oil_interval_km,
            "insurance_expiry": self.insurance_expiry,
            "inspection_expiry": self.inspection_expiry,
            "status": self.status.value,
            "region": self.region,
            "notes": self.notes,
            "created_at": self.created_at,
        }
