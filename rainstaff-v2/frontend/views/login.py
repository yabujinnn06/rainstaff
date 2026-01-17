"""
Rainstaff v2 - Login View  
Modern enterprise login screen with dark theme
"""

import flet as ft
from loguru import logger

from backend.database import SessionLocal
from backend.services.user_service import UserService
from shared.auth import AuthContext


class LoginView:
    """Login screen"""
    
    def __init__(self, app):
        self.app = app
        self.username_field = ft.TextField(
            label="Kullanıcı Adı",
            prefix_icon=ft.Icons.PERSON,
            autofocus=True,
            on_submit=lambda _: self.do_login(),
        )
        self.password_field = ft.TextField(
            label="Şifre",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            on_submit=lambda _: self.do_login(),
        )
        self.login_button = ft.ElevatedButton(
            "Giriş Yap",
            icon=ft.Icons.LOGIN,
            on_click=lambda _: self.do_login(),
        )
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED_400,
            size=14,
            visible=False,
        )
    
    def build(self) -> ft.View:
        """Build login view"""
        return ft.View(
            route="/login",
            bgcolor=ft.Colors.GREY_900,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.BUSINESS, size=80, color=ft.Colors.BLUE_400),
                            ft.Text("Rainstaff ERP", size=32, weight=ft.FontWeight.BOLD),
                            ft.Text("Kurumsal İK ve Filo Yönetim Sistemi", size=14, color=ft.Colors.GREY_400),
                            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column(
                                        controls=[
                                            ft.Text("Oturum Aç", size=24, weight=ft.FontWeight.W_500),
                                            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                                            self.username_field,
                                            self.password_field,
                                            self.error_text,
                                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                            self.login_button,
                                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                            ft.Text("Varsayılan: admin / admin123", size=12, color=ft.Colors.GREY_500, italic=True),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                        spacing=15,
                                    ),
                                    padding=40,
                                    width=450,
                                ),
                            ),
                            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                            ft.Text("Rainstaff ERP v2.0.0", size=12, color=ft.Colors.GREY_600),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.Alignment(0, 0),  # center
                    expand=True,
                ),
            ],
        )
    
    def do_login(self):
        """Handle login attempt"""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self.show_error("Kullanıcı adı ve şifre gerekli")
            return
        
        self.login_button.disabled = True
        self.login_button.content = ft.Text("Giriş yapılıyor...")
        self.app.page.update()
        
        try:
            # Create session
            db = SessionLocal()
            
            # Authenticate
            user = UserService.authenticate(db, username, password)
            
            # Check result BEFORE closing
            if not user:
                db.close()
                self.show_error("Kullanıcı adı veya şifre hatalı")
                self.login_button.disabled = False
                self.login_button.content = ft.Text("Giriş Yap")
                self.app.page.update()
                return
            
            # IMPORTANT: Extract all data BEFORE closing session
            user_data = {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'region': user.region,
            }
            
            # NOW close session
            db.close()
            
            # Create auth context with extracted data
            self.app.auth_context = AuthContext(
                user_id=user_data['id'],
                username=user_data['username'],
                role=user_data['role'],
                region=user_data['region'],
            )
            
            logger.info(f"User logged in: {user_data['username']} (role={user_data['role'].value}, region={user_data['region']})")
            
            # Navigate to dashboard
            self.app.goto_dashboard()
            
        except Exception as e:
            logger.error(f"Login error: {type(e).__name__}: {e}")
            self.show_error(f"Hata: {str(e)[:50]}")
            self.login_button.disabled = False
            self.login_button.content = ft.Text("Giriş Yap")
            self.app.page.update()
    
    def show_error(self, message: str):
        """Show error message"""
        self.error_text.value = message
        self.error_text.visible = True
        self.app.page.update()
