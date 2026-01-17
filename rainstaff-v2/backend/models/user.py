"""
Rainstaff v2 - User Model
SQLAlchemy model for user authentication and authorization
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime

from backend.database import Base
from shared.enums import UserRole


class User(Base):
    """User model with role-based access control"""
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Authorization
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    region = Column(String(50), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)  # User ID who created this user
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}', region='{self.region}')>"
    
    def to_dict(self):
        """Convert to dictionary (without sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value,
            "region": self.region,
            "is_active": self.is_active,
            "is_locked": self.is_locked,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
        }
