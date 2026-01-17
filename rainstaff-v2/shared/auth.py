"""
Rainstaff v2 - Authentication & Authorization
JWT-based authentication with role-based access control
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps

from shared.config import settings
from shared.enums import UserRole, Permission, ROLE_PERMISSIONS


class AuthToken:
    """JWT token management"""
    
    @staticmethod
    def create_token(user_id: int, username: str, role: UserRole, region: str) -> str:
        """Create JWT token for user"""
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role.value,
            "region": region,
            "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class PasswordHasher:
    """Password hashing with bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class AuthContext:
    """Current user authentication context"""
    
    def __init__(self, user_id: int, username: str, role: UserRole, region: str):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.region = region
        self._permissions = ROLE_PERMISSIONS.get(role, [])
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin or higher"""
        return self.role.level >= UserRole.ADMIN.level
    
    @property
    def is_manager(self) -> bool:
        """Check if user is manager or higher"""
        return self.role.level >= UserRole.MANAGER.level
    
    @property
    def can_view_all_regions(self) -> bool:
        """Check if user can view all regions"""
        return self.is_super_admin or self.region == "ALL"
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self._permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the given permissions"""
        return any(p in self._permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all given permissions"""
        return all(p in self._permissions for p in permissions)
    
    def can_access_region(self, target_region: str) -> bool:
        """Check if user can access target region"""
        if self.can_view_all_regions:
            return True
        return self.region == target_region
    
    def can_manage_user(self, target_role: UserRole) -> bool:
        """Check if user can manage another user with target role"""
        return self.role.can_access_role(target_role)
    
    def get_region_filter(self) -> Optional[str]:
        """Get region filter for queries (None = all regions)"""
        if self.can_view_all_regions:
            return None
        return self.region
    
    @classmethod
    def from_token(cls, token: str) -> Optional["AuthContext"]:
        """Create auth context from JWT token"""
        payload = AuthToken.decode_token(token)
        if not payload:
            return None
        
        return cls(
            user_id=payload["user_id"],
            username=payload["username"],
            role=UserRole(payload["role"]),
            region=payload["region"],
        )


def require_permission(*permissions: Permission):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(auth: AuthContext, *args, **kwargs):
            if not auth.has_all_permissions(list(permissions)):
                raise PermissionError(
                    f"Bu işlem için yetkiniz yok. Gerekli: {[p.value for p in permissions]}"
                )
            return func(auth, *args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: UserRole):
    """Decorator to require specific role level"""
    def decorator(func):
        @wraps(func)
        def wrapper(auth: AuthContext, *args, **kwargs):
            min_level = max(r.level for r in roles)
            if auth.role.level < min_level:
                raise PermissionError(
                    f"Bu işlem için yetkiniz yok. Minimum rol: {roles[0].value}"
                )
            return func(auth, *args, **kwargs)
        return wrapper
    return decorator
