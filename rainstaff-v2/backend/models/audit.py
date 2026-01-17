"""
Rainstaff v2 - Audit Log Model
Complete audit trail for all operations
"""

from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.sql import func

from backend.database import Base


class AuditLog(Base):
    """Audit log for all system operations"""
    
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Who
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    user_role = Column(String(20), nullable=False)
    user_region = Column(String(50), nullable=False)
    
    # What
    action = Column(String(100), nullable=False, index=True)  # create_employee, update_vehicle, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # employee, vehicle, user, etc.
    entity_id = Column(Integer, nullable=True, index=True)
    
    # Details
    description = Column(Text, nullable=False)
    old_values = Column(JSON, nullable=True)  # Before change
    new_values = Column(JSON, nullable=True)  # After change
    
    # When
    timestamp = Column(String(50), server_default=func.now(), nullable=False, index=True)
    
    # Where (IP, device info if available)
    ip_address = Column(String(50), nullable=True)
    device_info = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user='{self.username}', action='{self.action}', entity='{self.entity_type}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "user_region": self.user_region,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "timestamp": self.timestamp,
            "ip_address": self.ip_address,
            "device_info": self.device_info,
        }
