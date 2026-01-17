"""
Rainstaff v2 - Enums and Constants
Type-safe enumerations for the application
"""

from enum import Enum


class UserRole(str, Enum):
    """User roles with hierarchy"""
    SUPER_ADMIN = "super_admin"  # System owner, all permissions
    ADMIN = "admin"               # Regional admin, reports, user management
    MANAGER = "manager"           # Team lead, approvals, planning
    USER = "user"                 # Data entry, own records
    VIEWER = "viewer"             # Read-only access
    
    @property
    def level(self) -> int:
        """Role hierarchy level (higher = more permissions)"""
        levels = {
            self.SUPER_ADMIN: 100,
            self.ADMIN: 80,
            self.MANAGER: 60,
            self.USER: 40,
            self.VIEWER: 20,
        }
        return levels.get(self, 0)
    
    def can_access_role(self, target_role: "UserRole") -> bool:
        """Check if this role can access/manage target role"""
        return self.level >= target_role.level


class Permission(str, Enum):
    """Granular permissions"""
    # Employee management
    EMPLOYEE_VIEW = "employee:view"
    EMPLOYEE_CREATE = "employee:create"
    EMPLOYEE_EDIT = "employee:edit"
    EMPLOYEE_DELETE = "employee:delete"
    
    # Timesheet management
    TIMESHEET_VIEW = "timesheet:view"
    TIMESHEET_CREATE = "timesheet:create"
    TIMESHEET_EDIT = "timesheet:edit"
    TIMESHEET_DELETE = "timesheet:delete"
    TIMESHEET_APPROVE = "timesheet:approve"
    
    # Vehicle management
    VEHICLE_VIEW = "vehicle:view"
    VEHICLE_CREATE = "vehicle:create"
    VEHICLE_EDIT = "vehicle:edit"
    VEHICLE_DELETE = "vehicle:delete"
    
    # Driver management
    DRIVER_VIEW = "driver:view"
    DRIVER_CREATE = "driver:create"
    DRIVER_EDIT = "driver:edit"
    DRIVER_DELETE = "driver:delete"
    
    # Inspection & Service
    INSPECTION_VIEW = "inspection:view"
    INSPECTION_CREATE = "inspection:create"
    INSPECTION_EDIT = "inspection:edit"
    SERVICE_VIEW = "service:view"
    SERVICE_CREATE = "service:create"
    SERVICE_EDIT = "service:edit"
    
    # Reports
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"
    REPORT_DELETE = "report:delete"
    
    # System management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    SETTINGS_EDIT = "settings:edit"
    AUDIT_VIEW = "audit:view"
    BACKUP_CREATE = "backup:create"
    BACKUP_RESTORE = "backup:restore"


# Role-to-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [p for p in Permission],  # All permissions
    
    UserRole.ADMIN: [
        # Employee
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_EDIT,
        # Timesheet
        Permission.TIMESHEET_VIEW,
        Permission.TIMESHEET_CREATE,
        Permission.TIMESHEET_EDIT,
        Permission.TIMESHEET_APPROVE,
        # Vehicle
        Permission.VEHICLE_VIEW,
        Permission.VEHICLE_CREATE,
        Permission.VEHICLE_EDIT,
        # Driver
        Permission.DRIVER_VIEW,
        Permission.DRIVER_CREATE,
        Permission.DRIVER_EDIT,
        # Inspection & Service
        Permission.INSPECTION_VIEW,
        Permission.INSPECTION_CREATE,
        Permission.INSPECTION_EDIT,
        Permission.SERVICE_VIEW,
        Permission.SERVICE_CREATE,
        Permission.SERVICE_EDIT,
        # Reports
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        # System
        Permission.USER_VIEW,
        Permission.AUDIT_VIEW,
        Permission.BACKUP_CREATE,
    ],
    
    UserRole.MANAGER: [
        # Employee
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_EDIT,
        # Timesheet
        Permission.TIMESHEET_VIEW,
        Permission.TIMESHEET_CREATE,
        Permission.TIMESHEET_EDIT,
        Permission.TIMESHEET_APPROVE,
        # Vehicle
        Permission.VEHICLE_VIEW,
        Permission.VEHICLE_EDIT,
        # Driver
        Permission.DRIVER_VIEW,
        Permission.DRIVER_EDIT,
        # Inspection & Service
        Permission.INSPECTION_VIEW,
        Permission.INSPECTION_CREATE,
        Permission.INSPECTION_EDIT,
        Permission.SERVICE_VIEW,
        Permission.SERVICE_CREATE,
        # Reports
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
    ],
    
    UserRole.USER: [
        # Employee
        Permission.EMPLOYEE_VIEW,
        # Timesheet
        Permission.TIMESHEET_VIEW,
        Permission.TIMESHEET_CREATE,
        Permission.TIMESHEET_EDIT,
        # Vehicle
        Permission.VEHICLE_VIEW,
        # Driver
        Permission.DRIVER_VIEW,
        # Inspection
        Permission.INSPECTION_VIEW,
        Permission.INSPECTION_CREATE,
        # Service
        Permission.SERVICE_VIEW,
        Permission.SERVICE_CREATE,
        # Reports
        Permission.REPORT_VIEW,
    ],
    
    UserRole.VIEWER: [
        Permission.EMPLOYEE_VIEW,
        Permission.TIMESHEET_VIEW,
        Permission.VEHICLE_VIEW,
        Permission.DRIVER_VIEW,
        Permission.INSPECTION_VIEW,
        Permission.SERVICE_VIEW,
        Permission.REPORT_VIEW,
    ],
}


class DayType(str, Enum):
    """Day types for timesheet calculations"""
    WEEKDAY = "weekday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    SPECIAL = "special"  # Public holiday, special event


class VehicleStatus(str, Enum):
    """Vehicle operational status"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class InspectionResult(str, Enum):
    """Vehicle inspection results"""
    PASS = "pass"           # Olumlu
    FAIL = "fail"           # Olumsuz
    WARNING = "warning"     # Uyarı
    UNKNOWN = "unknown"     # Belirsiz
