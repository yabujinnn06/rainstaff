"""
Rainstaff v2 - Message Model
In-app messaging between users and branches
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.sql import func

from backend.database import Base


class Message(Base):
    """In-app message model"""
    
    __tablename__ = "messages"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Sender/Receiver
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_username = Column(String(50), nullable=False)
    sender_region = Column(String(50), nullable=False)
    
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = broadcast
    receiver_region = Column(String(50), nullable=True, index=True)  # NULL = all regions
    
    # Content
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(String(10), default="normal", nullable=False)  # low, normal, high, urgent
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Message(id={self.id}, from='{self.sender_username}', to_region='{self.receiver_region}', subject='{self.subject[:30]}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_username": self.sender_username,
            "sender_region": self.sender_region,
            "receiver_id": self.receiver_id,
            "receiver_region": self.receiver_region,
            "subject": self.subject,
            "body": self.body,
            "priority": self.priority,
            "is_read": self.is_read,
            "read_at": self.read_at,
            "created_at": self.created_at,
        }


class Notification(Base):
    """System notification model"""
    
    __tablename__ = "notifications"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Target
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = all
    region = Column(String(50), nullable=True, index=True)  # NULL = all regions
    
    # Content
    type = Column(String(50), nullable=False)  # sync_conflict, data_update, system_message, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)  # Deep link to relevant screen
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(String(50), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(String(50), nullable=True)  # Auto-delete old notifications
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.type}', title='{self.title}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "region": self.region,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "action_url": self.action_url,
            "is_read": self.is_read,
            "read_at": self.read_at,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class Presence(Base):
    """Online presence tracking"""
    
    __tablename__ = "presence"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    username = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    
    # Status
    status = Column(String(20), default="online", nullable=False)  # online, away, busy, offline
    last_activity = Column(String(50), nullable=False)
    
    # Device info
    device_info = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    # Timestamps
    connected_at = Column(String(50), server_default=func.now(), nullable=False)
    updated_at = Column(String(50), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Presence(user='{self.username}', status='{self.status}', region='{self.region}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "region": self.region,
            "status": self.status,
            "last_activity": self.last_activity,
            "device_info": self.device_info,
            "connected_at": self.connected_at,
        }


class SyncLog(Base):
    """Sync history and conflict tracking"""
    
    __tablename__ = "sync_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User/Region
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False, index=True)
    
    # Sync details
    sync_type = Column(String(20), nullable=False)  # push, pull, conflict
    entity_type = Column(String(50), nullable=False)  # employee, timesheet, vehicle, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False)  # success, failed, conflict
    records_affected = Column(Integer, default=0, nullable=False)
    
    # Conflict details (if any)
    conflict_data = Column(Text, nullable=True)  # JSON with local vs remote
    resolution = Column(String(50), nullable=True)  # local_wins, remote_wins, manual
    
    # Timestamps
    started_at = Column(String(50), server_default=func.now(), nullable=False)
    completed_at = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<SyncLog(id={self.id}, region='{self.region}', type='{self.sync_type}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "region": self.region,
            "sync_type": self.sync_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status,
            "records_affected": self.records_affected,
            "conflict_data": self.conflict_data,
            "resolution": self.resolution,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
