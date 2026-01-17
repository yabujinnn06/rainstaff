"""
Rainstaff v2 - Messaging View
In-app messaging and notifications (Flet 0.80.2 compatible with button-based tabs)
"""

import flet as ft
from loguru import logger
from datetime import datetime
from typing import Optional

from backend.database import get_db
from backend.services.messaging_service import MessagingService, NotificationService, PresenceService
from shared.enums import Permission


class MessagingView:
    """Messaging interface with button-based tabs (Flet Tab API broken in 0.80.2)"""
    
    def __init__(self, app):
        self.app = app
        self.auth = app.auth_context
        self.selected_tab = 0
    
    def build(self) -> ft.Column:
        """Build messaging view with button tabs"""
        # Define tab labels and indices
        tab_buttons = [
            ("Gelen Kutusu", 0),
            ("Gönderilmiş", 1),
            ("Bildirimler", 2),
            ("Çevrimiçi Kullanıcılar", 3),
        ]
        
        # Create button row - manually manage tab switching
        button_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    content=ft.Text(label),
                    on_click=lambda _, idx=idx: self._switch_tab(idx),
                )
                for label, idx in tab_buttons
            ],
            spacing=10,
            wrap=True,
        )
        
        # Content container
        content_container = ft.Container(
            content=self.build_tab_content(),
            expand=True,
            padding=20,
        )
        
        return ft.Column(
            controls=[
                ft.Text("Mesajlar ve Bildirimler", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                button_row,
                ft.Divider(),
                content_container,
            ],
            expand=True,
        )
    
    def _switch_tab(self, index: int):
        """Switch tab and rebuild content"""
        self.selected_tab = index
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
                    priority_color = {
                        "urgent": ft.Colors.RED,
                        "high": ft.Colors.ORANGE,
                        "normal": ft.Colors.BLUE,
                        "low": ft.Colors.GREY,
                    }.get(msg.priority, ft.Colors.BLUE)
                    
                    message_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(
                                        ft.Icons.CIRCLE,
                                        color=priority_color,
                                        size=12 if msg.is_read else 20,
                                    ),
                                    title=ft.Text(
                                        msg.subject,
                                        weight=ft.FontWeight.BOLD if not msg.is_read else ft.FontWeight.NORMAL,
                                    ),
                                    subtitle=ft.Text(f"{msg.sender_username} ({msg.sender_region}) • {msg.created_at[:16]}"),
                                    trailing=ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        tooltip="Sil",
                                        on_click=lambda _, m=msg: self.delete_message(m.id),
                                    ),
                                    on_click=lambda _, m=msg: self.view_message(m),
                                ),
                                padding=10,
                            ),
                        )
                    )
                
                return ft.Column(
                    controls=[
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.CREATE),
                                    ft.Text("Yeni Mesaj"),
                                ], spacing=6),
                                on_click=lambda _: self.compose_message(),
                            ),
                            ft.TextButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.DONE_ALL),
                                    ft.Text("Tümünü Okundu İşaretle"),
                                ], spacing=6),
                                on_click=lambda _: self.mark_all_read(),
                            ),
                        ]),
                        ft.Divider(),
                        ft.Column(
                            controls=message_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
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
                    target = msg.receiver_id if msg.receiver_id else f"Bölge: {msg.receiver_region or 'Tümü'}"
                    
                    message_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.SEND, color=ft.Colors.BLUE),
                                    title=ft.Text(msg.subject),
                                    subtitle=ft.Text(f"Kime: {target} • {msg.created_at[:16]}"),
                                    trailing=ft.Text(
                                        "✓✓ Okundu" if msg.is_read else "✓ Gönderildi",
                                        size=12,
                                        color=ft.Colors.GREEN if msg.is_read else ft.Colors.GREY,
                                    ),
                                ),
                                padding=10,
                            ),
                        )
                    )
                
                return ft.Column(
                    controls=[
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CREATE),
                                ft.Text("Yeni Mesaj"),
                            ], spacing=6),
                            on_click=lambda _: self.compose_message(),
                        ),
                        ft.Divider(),
                        ft.Column(
                            controls=message_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
        except Exception as e:
            logger.error(f"Error loading sent messages: {e}")
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
                    icon_map = {
                        "sync_conflict": ft.Icons.SYNC_PROBLEM,
                        "data_update": ft.Icons.UPDATE,
                        "system_message": ft.Icons.INFO,
                        "warning": ft.Icons.WARNING,
                        "error": ft.Icons.ERROR,
                    }
                    
                    color_map = {
                        "sync_conflict": ft.Colors.ORANGE,
                        "data_update": ft.Colors.BLUE,
                        "system_message": ft.Colors.GREEN,
                        "warning": ft.Colors.ORANGE,
                        "error": ft.Colors.RED,
                    }
                    
                    notif_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(
                                        icon_map.get(notif.type, ft.Icons.NOTIFICATIONS),
                                        color=color_map.get(notif.type, ft.Colors.BLUE),
                                    ),
                                    title=ft.Text(
                                        notif.title,
                                        weight=ft.FontWeight.BOLD if not notif.is_read else ft.FontWeight.NORMAL,
                                    ),
                                    subtitle=ft.Text(f"{notif.message[:100]}... • {notif.created_at[:16]}"),
                                    trailing=ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        tooltip="Kapat",
                                        on_click=lambda _, n=notif: self.dismiss_notification(n.id),
                                    ),
                                    on_click=lambda _, n=notif: self.view_notification(n),
                                ),
                                padding=10,
                                bgcolor=ft.Colors.BLUE_900 if not notif.is_read else None,
                            ),
                        )
                    )
                
                return ft.Column(
                    controls=[
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CLEAR_ALL),
                                ft.Text("Tümünü Temizle"),
                            ], spacing=6),
                            on_click=lambda _: self.clear_all_notifications(),
                        ),
                        ft.Divider(),
                        ft.Column(
                            controls=notif_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
        except Exception as e:
            logger.error(f"Error loading notifications: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def build_online_users(self) -> ft.Column:
        """Build online users tab"""
        try:
            with get_db() as db:
                online_users = PresenceService.get_online_users(self.auth, db)
                
                if not online_users:
                    return ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Çevrimiçi kullanıcı yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                user_list = []
                for user in online_users:
                    status_colors = {
                        "online": ft.Colors.GREEN,
                        "away": ft.Colors.ORANGE,
                        "busy": ft.Colors.RED,
                        "offline": ft.Colors.GREY,
                    }
                    
                    user_list.append(
                        ft.ListTile(
                            leading=ft.Stack([
                                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=40),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CIRCLE, size=12, color=status_colors.get(user.status, ft.Colors.GREY)),
                                    right=0,
                                    bottom=0,
                                ),
                            ]),
                            title=ft.Text(user.username, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{user.region} • {user.status}"),
                            trailing=ft.IconButton(
                                icon=ft.Icons.MESSAGE,
                                tooltip="Mesaj Gönder",
                                on_click=lambda _, u=user: self.compose_message(target_user_id=u.user_id),
                            ),
                        )
                    )
                
                return ft.Column(
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.CIRCLE, size=12, color=ft.Colors.GREEN),
                            ft.Text(f"{len(online_users)} kullanıcı çevrimiçi"),
                        ]),
                        ft.Divider(),
                        ft.Column(
                            controls=user_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
        except Exception as e:
            logger.error(f"Error loading online users: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def compose_message(self, target_user_id: Optional[int] = None):
        """Open compose message dialog - TODO"""
        self.app.show_snackbar("Mesaj gönderme özelliği yakında eklenecek")
    
    def view_message(self, message):
        """View message details"""
        try:
            with get_db() as db:
                MessagingService.mark_as_read(self.auth, db, message.id)
            self.app.show_snackbar(f"Mesaj: {message.subject}")
            self.app.page.update()
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
    
    def delete_message(self, message_id: int):
        """Delete message - TODO"""
        self.app.show_snackbar("Silme özelliği yakında eklenecek")
    
    def mark_all_read(self):
        """Mark all messages as read - TODO"""
        self.app.show_snackbar("Tümü okundu işaretlendi")
    
    def view_notification(self, notification):
        """View notification details"""
        try:
            with get_db() as db:
                NotificationService.mark_as_read(self.auth, db, notification.id)
            self.app.show_snackbar(notification.title)
            self.app.page.update()
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
    
    def dismiss_notification(self, notification_id: int):
        """Dismiss notification - TODO"""
        self.app.show_snackbar("Bildirim kapatıldı")
    
    def clear_all_notifications(self):
        """Clear all notifications - TODO"""
        self.app.show_snackbar("Tüm bildirimler temizlendi")
