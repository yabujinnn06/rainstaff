"""
Rainstaff v2 - Messaging View (Fixed)
In-app messaging and notifications - Flet Tab compat fixed
"""

import flet as ft
from loguru import logger
from datetime import datetime
from typing import Optional

from backend.database import get_db
from backend.services.messaging_service import MessagingService, NotificationService, PresenceService
from shared.enums import Permission


class MessagingView:
    """Messaging interface with button-based tabs"""
    
    def __init__(self, app):
        self.app = app
        self.auth = app.auth_context
        self.selected_tab = 0
    
    def build(self) -> ft.Column:
        """Build messaging view"""
        return ft.Column(
            controls=[
                ft.Text("Mesajlar ve Bildirimler", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Manual tab buttons
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Gelen Kutusu", on_click=lambda _: self.switch_and_refresh(0)),
                        ft.ElevatedButton("Gönderilmiş", on_click=lambda _: self.switch_and_refresh(1)),
                        ft.ElevatedButton("Bildirimler", on_click=lambda _: self.switch_and_refresh(2)),
                        ft.ElevatedButton("Çevrimiçi Kullanıcılar", on_click=lambda _: self.switch_and_refresh(3)),
                    ],
                    spacing=10,
                ),
                
                ft.Divider(),
                
                ft.Container(
                    content=self.build_tab_content(),
                    expand=True,
                    padding=20,
                ),
            ],
            expand=True,
        )
    
    def switch_and_refresh(self, tab_index: int):
        """Switch tab and refresh content"""
        self.selected_tab = tab_index
        self.app.page.update()
    
    def build_tab_content(self) -> ft.Control:
        """Build content based on selected tab"""
        if self.selected_tab == 0:
            return self.build_inbox()
        elif self.selected_tab == 1:
            return self.build_sent()
        elif self.selected_tab == 2:
            return self.build_notifications()
        else:
            return self.build_online_users()
    
    def build_inbox(self) -> ft.Column:
        """Build inbox tab"""
        try:
            with get_db() as db:
                messages = MessagingService.get_inbox(self.auth, db, unread_only=False)
                
                if not messages:
                    return ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Gelen kutunuz boş", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                message_list = []
                for msg in messages:
                    message_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Text(msg.subject, size=14, weight=ft.FontWeight.W_500),
                                        ft.Text(f"{msg.sender_username}", size=12, color=ft.Colors.GREY),
                                        ft.Spacer(),
                                        ft.Text(msg.created_at[:16], size=12, color=ft.Colors.GREY),
                                    ],
                                    spacing=10,
                                ),
                                padding=15,
                            ),
                        )
                    )
                
                return ft.Column(message_list, spacing=10, scroll=ft.ScrollMode.AUTO)
        except Exception as e:
            logger.error(f"Error loading inbox: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def build_sent(self) -> ft.Column:
        """Build sent messages tab"""
        try:
            with get_db() as db:
                messages = MessagingService.get_sent_messages(self.auth, db)
                
                if not messages:
                    return ft.Column([
                        ft.Icon(ft.Icons.SEND, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Gönderilen mesaj yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                message_list = []
                for msg in messages:
                    message_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Text(msg.subject, size=14, weight=ft.FontWeight.W_500),
                                        ft.Spacer(),
                                        ft.Text("✓ Gönderildi" if not msg.is_read else "✓✓ Okundu", size=12, color=ft.Colors.GREY),
                                    ],
                                    spacing=10,
                                ),
                                padding=15,
                            ),
                        )
                    )
                
                return ft.Column(message_list, spacing=10, scroll=ft.ScrollMode.AUTO)
        except Exception as e:
            logger.error(f"Error loading sent: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def build_notifications(self) -> ft.Column:
        """Build notifications tab"""
        try:
            with get_db() as db:
                notifications = NotificationService.get_notifications(self.auth, db)
                
                if not notifications:
                    return ft.Column([
                        ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Bildirim yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                notif_list = []
                for notif in notifications:
                    notif_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE),
                                        ft.Column([
                                            ft.Text(notif.title, weight=ft.FontWeight.W_500),
                                            ft.Text(notif.message, size=12, color=ft.Colors.GREY),
                                        ], spacing=5),
                                    ],
                                    spacing=15,
                                ),
                                padding=15,
                            ),
                        )
                    )
                
                return ft.Column(notif_list, spacing=10, scroll=ft.ScrollMode.AUTO)
        except Exception as e:
            logger.error(f"Error loading notifications: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def build_online_users(self) -> ft.Column:
        """Build online users tab"""
        try:
            with get_db() as db:
                users = PresenceService.get_online_users(self.auth, db)
                
                if not users:
                    return ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Çevrimiçi kullanıcı yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                user_list = []
                for user in users:
                    status_color = {
                        "online": ft.Colors.GREEN,
                        "away": ft.Colors.ORANGE,
                        "busy": ft.Colors.RED,
                        "offline": ft.Colors.GREY,
                    }.get(user.status, ft.Colors.GREY)
                    
                    user_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CIRCLE, color=status_color, size=12),
                                        ft.Text(f"{user.username} ({user.region})", size=14),
                                        ft.Spacer(),
                                        ft.IconButton(ft.Icons.MESSAGE, tooltip="Mesaj gönder"),
                                    ],
                                    spacing=10,
                                ),
                                padding=15,
                            ),
                        )
                    )
                
                return ft.Column(user_list, spacing=10, scroll=ft.ScrollMode.AUTO)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def switch_tab(self, index: int):
        """Switch tab"""
        self.selected_tab = index
    
    def delete_message(self, message_id: int):
        """Delete message"""
        logger.info(f"Delete message: {message_id}")
    
    def compose_message(self, target_user_id: Optional[int] = None):
        """Compose new message - TODO"""
        logger.debug("Compose message dialog")
    
    def view_message(self, message_id: int):
        """View full message - TODO"""
        logger.debug(f"View message: {message_id}")
    
    def mark_all_read(self):
        """Mark all messages as read - TODO"""
        logger.debug("Mark all as read")
    
    def dismiss_notification(self, notif_id: int):
        """Dismiss notification - TODO"""
        logger.debug(f"Dismiss notification: {notif_id}")
