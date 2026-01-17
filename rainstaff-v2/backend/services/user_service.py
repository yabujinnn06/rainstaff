"""
Rainstaff v2 - User Service
Business logic for user management with RBAC
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.models.user import User
from backend.models.audit import AuditLog
from shared.auth import AuthContext, PasswordHasher, require_permission, require_role
from shared.enums import UserRole, Permission
from loguru import logger


class UserService:
    """User management service"""
    
    @staticmethod
    @require_permission(Permission.USER_CREATE)
    def create_user(
        auth: AuthContext,
        db: Session,
        username: str,
        password: str,
        full_name: str,
        role: UserRole,
        region: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """Create new user (requires USER_CREATE permission)"""
        
        # Check if creator can manage target role
        if not auth.can_manage_user(role):
            raise PermissionError(f"Bu rol için kullanıcı oluşturamazsınız: {role.value}")
        
        # Check username uniqueness
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError(f"Kullanıcı adı zaten kullanılıyor: {username}")
        
        # Hash password
        password_hash = PasswordHasher.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            region=region,
            is_active=True,
            is_locked=False,
            failed_login_attempts=0,
            created_by=auth.user_id,
        )
        
        db.add(user)
        db.flush()  # Get ID without committing
        
        # Audit log
        audit = AuditLog(
            user_id=auth.user_id,
            username=auth.username,
            user_role=auth.role.value,
            user_region=auth.region,
            action="create_user",
            entity_type="user",
            entity_id=user.id,
            description=f"Yeni kullanıcı oluşturuldu: {username} ({role.value})",
            new_values=user.to_dict(),
        )
        db.add(audit)
        
        logger.info(f"User {auth.username} created new user: {username} (role={role.value}, region={region})")
        return user
    
    @staticmethod
    @require_permission(Permission.USER_VIEW)
    def get_users(auth: AuthContext, db: Session) -> List[User]:
        """Get all users visible to current user"""
        query = db.query(User)
        
        # Region filter
        region_filter = auth.get_region_filter()
        if region_filter:
            query = query.filter(User.region == region_filter)
        
        return query.order_by(User.full_name).all()
    
    @staticmethod
    @require_permission(Permission.USER_VIEW)
    def get_user_by_id(auth: AuthContext, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID (with region check)"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and not auth.can_access_region(user.region):
            raise PermissionError("Bu kullanıcıyı görüntüleme yetkiniz yok")
        
        return user
    
    @staticmethod
    @require_permission(Permission.USER_EDIT)
    def update_user(
        auth: AuthContext,
        db: Session,
        user_id: int,
        **updates
    ) -> User:
        """Update user (requires USER_EDIT permission)"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"Kullanıcı bulunamadı: ID={user_id}")
        
        # Check if updater can manage target role
        if not auth.can_manage_user(user.role):
            raise PermissionError("Bu kullanıcıyı düzenleme yetkiniz yok")
        
        # Save old values for audit
        old_values = user.to_dict()
        
        # Update fields
        allowed_fields = ["full_name", "email", "phone", "is_active", "region"]
        for field, value in updates.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        # Handle password change
        if "password" in updates and updates["password"]:
            user.password_hash = PasswordHasher.hash_password(updates["password"])
        
        # Handle role change (super admin only)
        if "role" in updates and auth.is_super_admin:
            user.role = UserRole(updates["role"])
        
        user.updated_at = datetime.utcnow()
        
        # Audit log
        audit = AuditLog(
            user_id=auth.user_id,
            username=auth.username,
            user_role=auth.role.value,
            user_region=auth.region,
            action="update_user",
            entity_type="user",
            entity_id=user.id,
            description=f"Kullanıcı güncellendi: {user.username}",
            old_values=old_values,
            new_values=user.to_dict(),
        )
        db.add(audit)
        
        logger.info(f"User {auth.username} updated user: {user.username}")
        return user
    
    @staticmethod
    @require_permission(Permission.USER_DELETE)
    def delete_user(auth: AuthContext, db: Session, user_id: int) -> None:
        """Delete user (requires USER_DELETE permission)"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"Kullanıcı bulunamadı: ID={user_id}")
        
        # Check if deleter can manage target role
        if not auth.can_manage_user(user.role):
            raise PermissionError("Bu kullanıcıyı silme yetkiniz yok")
        
        # Prevent self-deletion
        if user.id == auth.user_id:
            raise ValueError("Kendinizi silemezsiniz")
        
        # Audit log before deletion
        audit = AuditLog(
            user_id=auth.user_id,
            username=auth.username,
            user_role=auth.role.value,
            user_region=auth.region,
            action="delete_user",
            entity_type="user",
            entity_id=user.id,
            description=f"Kullanıcı silindi: {user.username}",
            old_values=user.to_dict(),
        )
        db.add(audit)
        
        db.delete(user)
        logger.warning(f"User {auth.username} deleted user: {user.username}")
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user (no permission check)"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return None
        
        if user.is_locked:
            logger.warning(f"Login attempt for locked account: {username}")
            raise ValueError("Hesabınız kilitlendi. Yöneticinize başvurun.")
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive account: {username}")
            raise ValueError("Hesabınız devre dışı.")
        
        # Verify password
        if not PasswordHasher.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                logger.warning(f"Account locked due to failed attempts: {username}")
            
            db.commit()
            return None
        
        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User logged in: {username}")
        return user
