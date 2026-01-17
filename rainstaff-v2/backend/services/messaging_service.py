"""
Rainstaff v2 - Messaging Service
In-app messaging and notifications
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from backend.models.messaging import Message, Notification, Presence
from backend.models.audit import AuditLog
from shared.auth import AuthContext, require_permission
from shared.enums import Permission


class MessagingService:
    """In-app messaging service"""
    
    @staticmethod
    def send_message(
        auth: AuthContext,
        db: Session,
        subject: str,
        body: str,
        receiver_id: Optional[int] = None,
        receiver_region: Optional[str] = None,
        priority: str = "normal"
    ) -> Message:
        """
        Send message to specific user or broadcast to region/all
        """
        message = Message(
            sender_id=auth.user_id,
            sender_username=auth.username,
            sender_region=auth.region,
            receiver_id=receiver_id,
            receiver_region=receiver_region or auth.region,
            subject=subject,
            body=body,
            priority=priority,
        )
        
        db.add(message)
        db.flush()
        
        # Audit log
        target = f"user_{receiver_id}" if receiver_id else f"region_{receiver_region or 'all'}"
        audit = AuditLog(
            user_id=auth.user_id,
            username=auth.username,
            user_role=auth.role.value,
            user_region=auth.region,
            action="send_message",
            entity_type="message",
            entity_id=message.id,
            description=f"Mesaj gönderildi: {subject} → {target}",
        )
        db.add(audit)
        
        logger.info(f"Message sent from {auth.username} to {target}: {subject}")
        return message
    
    @staticmethod
    def get_inbox(
        auth: AuthContext,
        db: Session,
        unread_only: bool = False
    ) -> List[Message]:
        """Get messages for current user"""
        query = db.query(Message).filter(
            or_(
                Message.receiver_id == auth.user_id,  # Direct message
                and_(
                    Message.receiver_id == None,
                    or_(
                        Message.receiver_region == auth.region,  # Broadcast to region
                        Message.receiver_region == None  # Broadcast to all
                    )
                )
            )
        )
        
        if unread_only:
            query = query.filter(Message.is_read == False)
        
        return query.order_by(Message.created_at.desc()).all()
    
    @staticmethod
    def get_sent_messages(auth: AuthContext, db: Session) -> List[Message]:
        """Get messages sent by current user"""
        return db.query(Message).filter(
            Message.sender_id == auth.user_id
        ).order_by(Message.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(auth: AuthContext, db: Session, message_id: int):
        """Mark message as read"""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Mesaj bulunamadı: ID={message_id}")
        
        # Check if user can read this message
        can_read = (
            message.receiver_id == auth.user_id or
            (message.receiver_id is None and (
                message.receiver_region == auth.region or
                message.receiver_region is None or
                auth.can_view_all_regions
            ))
        )
        
        if not can_read:
            raise PermissionError("Bu mesajı okuma yetkiniz yok")
        
        message.is_read = True
        message.read_at = datetime.utcnow().isoformat()
        logger.debug(f"Message {message_id} marked as read by {auth.username}")
    
    @staticmethod
    def get_unread_count(auth: AuthContext, db: Session) -> int:
        """Get unread message count for current user"""
        return db.query(Message).filter(
            and_(
                or_(
                    Message.receiver_id == auth.user_id,
                    and_(
                        Message.receiver_id == None,
                        or_(
                            Message.receiver_region == auth.region,
                            Message.receiver_region == None
                        )
                    )
                ),
                Message.is_read == False
            )
        ).count()


class NotificationService:
    """System notification service"""
    
    @staticmethod
    def create_notification(
        db: Session,
        notification_type: str,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        region: Optional[str] = None,
        action_url: Optional[str] = None,
        expires_in_days: int = 7
    ) -> Notification:
        """Create system notification"""
        expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()
        
        notification = Notification(
            user_id=user_id,
            region=region,
            type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            expires_at=expires_at,
        )
        
        db.add(notification)
        db.flush()
        
        logger.info(f"Notification created: {notification_type} - {title}")
        return notification
    
    @staticmethod
    def get_notifications(
        auth: AuthContext,
        db: Session,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for current user"""
        now = datetime.utcnow().isoformat()
        
        query = db.query(Notification).filter(
            and_(
                or_(
                    Notification.expires_at == None,
                    Notification.expires_at > now
                ),
                or_(
                    Notification.user_id == auth.user_id,
                    and_(
                        Notification.user_id == None,
                        or_(
                            Notification.region == auth.region,
                            Notification.region == None
                        )
                    )
                )
            )
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(auth: AuthContext, db: Session, notification_id: int):
        """Mark notification as read"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return
        
        notification.is_read = True
        notification.read_at = datetime.utcnow().isoformat()
    
    @staticmethod
    def get_unread_count(auth: AuthContext, db: Session) -> int:
        """Get unread notification count"""
        now = datetime.utcnow().isoformat()
        
        return db.query(Notification).filter(
            and_(
                or_(
                    Notification.expires_at == None,
                    Notification.expires_at > now
                ),
                or_(
                    Notification.user_id == auth.user_id,
                    and_(
                        Notification.user_id == None,
                        or_(
                            Notification.region == auth.region,
                            Notification.region == None
                        )
                    )
                ),
                Notification.is_read == False
            )
        ).count()


class PresenceService:
    """Online presence tracking"""
    
    @staticmethod
    def update_presence(
        auth: AuthContext,
        db: Session,
        status: str = "online",
        device_info: Optional[str] = None
    ):
        """Update user online presence"""
        presence = db.query(Presence).filter(Presence.user_id == auth.user_id).first()
        
        if presence:
            presence.status = status
            presence.last_activity = datetime.utcnow().isoformat()
            presence.updated_at = datetime.utcnow().isoformat()
            if device_info:
                presence.device_info = device_info
        else:
            presence = Presence(
                user_id=auth.user_id,
                username=auth.username,
                region=auth.region,
                status=status,
                last_activity=datetime.utcnow().isoformat(),
                device_info=device_info,
            )
            db.add(presence)
        
        db.flush()
    
    @staticmethod
    def get_online_users(auth: AuthContext, db: Session) -> List[Presence]:
        """Get list of online users"""
        # Consider offline if last activity > 5 minutes ago
        cutoff = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        query = db.query(Presence).filter(
            and_(
                Presence.status.in_(["online", "away", "busy"]),
                Presence.last_activity >= cutoff
            )
        )
        
        # Filter by region if not admin
        if not auth.can_view_all_regions:
            query = query.filter(Presence.region == auth.region)
        
        return query.order_by(Presence.username).all()
    
    @staticmethod
    def get_user_status(db: Session, user_id: int) -> Optional[str]:
        """Get specific user's online status"""
        presence = db.query(Presence).filter(Presence.user_id == user_id).first()
        if not presence:
            return "offline"
        
        # Check if recently active
        cutoff = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        if presence.last_activity < cutoff:
            return "offline"
        
        return presence.status
    
    @staticmethod
    def mark_offline(auth: AuthContext, db: Session):
        """Mark user as offline"""
        presence = db.query(Presence).filter(Presence.user_id == auth.user_id).first()
        if presence:
            presence.status = "offline"
            presence.updated_at = datetime.utcnow().isoformat()
