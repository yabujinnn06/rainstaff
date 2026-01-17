"""
Rainstaff v2 - Flet Application
Modern enterprise ERP UI with Flet/Flutter
"""

import flet as ft
from loguru import logger

from shared.config import settings
from frontend.views.login import LoginView


class RainstaffApp:
    """Main Flet application controller"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.auth_context = None
        
        # Configure page
        self.page.title = settings.app_name
        self.page.window_width = 1400
        self.page.window_height = 900
        self.page.window_min_width = 1024
        self.page.window_min_height = 720
        self.page.padding = 0
        self.page.spacing = 0
        
        # Dark theme (enterprise minimal)
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
            use_material3=True,
        )
        
        # Navigation handler
        self.page.on_route_change = self.route_change
    
    def initialize(self):
        """Initialize application"""
        logger.info("Initializing Rainstaff application...")
        
        # Show login screen
        self.goto_login()
    
    def goto_login(self):
        """Navigate to login screen"""
        self.page.views.clear()
        login_view = LoginView(self)
        self.page.views.append(login_view.build())
        self.page.update()
    
    def goto_dashboard(self):
        """Navigate to dashboard after successful login"""
        from frontend.views.dashboard import DashboardView
        
        self.page.views.clear()
        dashboard_view = DashboardView(self)
        self.page.views.append(dashboard_view.build())
        self.page.update()
    
    def route_change(self, route):
        """Handle route changes"""
        logger.debug(f"Route changed to: {route}")
    
    def logout(self):
        """Logout current user"""
        logger.info(f"User logged out: {self.auth_context.username if self.auth_context else 'Unknown'}")
        self.auth_context = None
        self.goto_login()
    
    def show_snackbar(self, message: str, error: bool = False):
        """Show snackbar notification"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_900 if error else ft.Colors.GREEN_900,
        )
        self.page.snack_bar.open = True
        self.page.update()
