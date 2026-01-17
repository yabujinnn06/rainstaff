"""
Rainstaff v2 - Dashboard View
Main dashboard with navigation and role-based module access
"""

import flet as ft
from loguru import logger

from shared.enums import Permission


class DashboardView:
    """Main dashboard with sidebar navigation"""
    
    def __init__(self, app):
        self.app = app
        self.auth = app.auth_context
        
        # Current view
        self.current_view = "dashboard"
        self.content_area = ft.Container()
    
    def build(self) -> ft.View:
        """Build dashboard view"""
        return ft.View(
            route="/dashboard",
            controls=[
                ft.Row(
                    controls=[
                        # Sidebar
                        self.build_sidebar(),
                        
                        # Main content area
                        ft.Container(
                            content=self.content_area,
                            expand=True,
                            padding=20,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            padding=0,
        )
    
    def build_sidebar(self) -> ft.Container:
        """Build navigation sidebar"""
        nav_items = []
        
        # Dashboard (always visible)
        nav_items.append(self.create_nav_item(
            icon=ft.Icons.DASHBOARD,
            label="Dashboard",
            view_name="dashboard",
        ))
        
        # Messaging (always visible)
        nav_items.append(self.create_nav_item(
            icon=ft.Icons.MESSAGE,
            label="Mesajlar",
            view_name="messaging",
            badge_count=self.get_unread_count(),
        ))
        
        # HR Module
        if self.auth.has_any_permission([Permission.EMPLOYEE_VIEW, Permission.TIMESHEET_VIEW]):
            nav_items.append(ft.Divider(height=1))
            nav_items.append(self.create_nav_item(
                icon=ft.Icons.PEOPLE,
                label="İnsan Kaynakları",
                view_name="employees",
            ))
        
        # Fleet Module
        if self.auth.has_any_permission([Permission.VEHICLE_VIEW, Permission.DRIVER_VIEW]):
            nav_items.append(ft.Divider(height=1))
            nav_items.append(ft.Text("Filo Yönetimi", size=12, color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD))
            
            if self.auth.has_permission(Permission.VEHICLE_VIEW):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.DIRECTIONS_CAR,
                    label="Araçlar",
                    view_name="vehicles",
                ))
            
            if self.auth.has_permission(Permission.DRIVER_VIEW):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.BADGE,
                    label="Sürücüler",
                    view_name="drivers",
                ))
            
            if self.auth.has_permission(Permission.INSPECTION_VIEW):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.CHECKLIST,
                    label="Kontroller",
                    view_name="inspections",
                ))
        
        # Reports
        if self.auth.has_permission(Permission.REPORT_VIEW):
            nav_items.append(ft.Divider(height=1))
            nav_items.append(self.create_nav_item(
                icon=ft.Icons.ASSESSMENT,
                label="Raporlar",
                view_name="reports",
            ))
        
        # System
        if self.auth.has_any_permission([Permission.USER_VIEW, Permission.AUDIT_VIEW, Permission.SETTINGS_EDIT]):
            nav_items.append(ft.Divider(height=1))
            nav_items.append(ft.Text("Sistem", size=12, color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD))
            
            if self.auth.has_permission(Permission.USER_VIEW):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.MANAGE_ACCOUNTS,
                    label="Kullanıcılar",
                    view_name="users",
                ))
            
            if self.auth.has_permission(Permission.AUDIT_VIEW):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.HISTORY,
                    label="Denetim Logları",
                    view_name="audit",
                ))
            
            if self.auth.has_permission(Permission.SETTINGS_EDIT):
                nav_items.append(self.create_nav_item(
                    icon=ft.Icons.SETTINGS,
                    label="Ayarlar",
                    view_name="settings",
                ))
        
        # Logout (always at bottom)
        nav_items.append(ft.Divider(height=1))
        nav_items.append(ft.Container(expand=True))  # Spacer
        nav_items.append(self.create_nav_item(
            icon=ft.Icons.LOGOUT,
            label="Çıkış",
            view_name="logout",
            is_logout=True,
        ))
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.BUSINESS, size=32, color=ft.Colors.BLUE_400),
                                        ft.Text("Rainstaff", size=20, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=10,
                                ),
                                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                ft.Text(
                                    self.auth.username,
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    f"{self.auth.role.value} • {self.auth.region}",
                                    size=12,
                                    color=ft.Colors.GREY_400,
                                ),
                            ],
                        ),
                        padding=20,
                    ),
                    ft.Divider(height=1),
                    
                    # Navigation items
                    ft.Column(
                        controls=nav_items,
                        spacing=5,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            width=280,
            bgcolor=ft.Colors.GREY_900,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_800)),
        )
    
    def create_nav_item(self, icon, label, view_name, is_logout=False, badge_count=0):
        """Create navigation item"""
        is_active = self.current_view == view_name
        
        controls = [
            ft.Icon(icon, size=20),
            ft.Text(label, size=14),
        ]
        
        # Add badge if count > 0
        if badge_count > 0:
            controls.append(
                ft.Container(
                    content=ft.Text(str(badge_count), size=10, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    margin=ft.margin.only(left=5),
                )
            )
        
        return ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=15,
            ),
            padding=15,
            margin=ft.margin.symmetric(horizontal=10, vertical=2),
            bgcolor=ft.Colors.BLUE_900 if is_active else None,
            border_radius=8,
            ink=True,
            on_click=lambda _, v=view_name: self.handle_logout() if is_logout else self.navigate_to(v),
        )
    
    def navigate_to(self, view_name: str):
        """Navigate to view"""
        logger.debug(f"Navigating to: {view_name}")
        self.current_view = view_name
        
        # Load view content
        if view_name == "messaging":
            from frontend.views.messaging import MessagingView
            messaging_view = MessagingView(self.app)
            self.content_area.content = messaging_view.build()
        elif view_name in ["employees", "timesheets"]:
            from frontend.views.hr import HRView
            hr_view = HRView(self.app)
            self.content_area.content = hr_view.build()
        else:
            # Placeholder for other views
            self.content_area.content = ft.Column(
                controls=[
                    ft.Text(
                        f"{view_name.upper()} Modülü",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Bu modül yakında eklenecek...",
                        size=16,
                        color=ft.Colors.GREY_400,
                    ),
                ],
            )
        
        self.app.page.update()
    
    def get_unread_count(self) -> int:
        """Get unread message and notification count"""
        try:
            from backend.database import get_db
            from backend.services.messaging_service import MessagingService, NotificationService
            
            with get_db() as db:
                messages = MessagingService.get_unread_count(self.auth, db)
                notifications = NotificationService.get_unread_count(self.auth, db)
                return messages + notifications
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
        self.content_area.content = ft.Column(
            controls=[
                ft.Text(
                    f"{view_name.upper()} Modülü",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Text(
                    "Bu modül yakında eklenecek...",
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
            ],
        )
        
        self.app.page.update()
    
    def handle_logout(self):
        """Handle logout"""
        self.app.logout()
