"""
Rainstaff v2 - HR Module (Employees & Timesheets)
Puantaj ve çalışan yönetimi
"""

import flet as ft
from loguru import logger
from datetime import datetime, date
from typing import Optional

from backend.database import get_db
from backend.models.employee import Employee
from backend.models.timesheet import Timesheet
from shared.enums import Permission


class HRView:
    """HR module for employee and timesheet management"""
    
    def __init__(self, app):
        self.app = app
        self.auth = app.auth_context
        self.selected_tab = 0  # 0=Employees, 1=Timesheets
    
    def build(self) -> ft.Column:
        """Build HR view with tab navigation"""
        tab_buttons = [
            ("Çalışanlar", 0),
            ("Puantaj", 1),
        ]
        
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
        
        content_container = ft.Container(
            content=self.build_tab_content(),
            expand=True,
            padding=20,
        )
        
        return ft.Column(
            controls=[
                ft.Text("İnsan Kaynakları", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                button_row,
                ft.Divider(),
                content_container,
            ],
            expand=True,
        )
    
    def _switch_tab(self, index: int):
        """Switch tab and rebuild"""
        self.selected_tab = index
        self.app.page.update()
    
    def build_tab_content(self) -> ft.Control:
        """Build content for selected tab"""
        if self.selected_tab == 0:
            return self.build_employees_tab()
        else:
            return self.build_timesheets_tab()
    
    def build_employees_tab(self) -> ft.Column:
        """Build employees management tab"""
        try:
            with get_db() as db:
                # Get employees for current user's region
                region = self.auth.region if self.auth.region != "ALL" else None
                query = db.query(Employee)
                
                if region and not self.auth.has_permission(Permission.VIEW_ALL_REGIONS):
                    query = query.filter(Employee.region == region)
                
                employees = query.all()
                
                if not employees:
                    return ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Çalışan kaydı yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                emp_list = []
                for emp in employees:
                    emp_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE),
                                    title=ft.Text(emp.full_name, weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(f"{emp.position} • {emp.region} • {emp.hire_date}"),
                                    trailing=ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            tooltip="Düzenle",
                                            on_click=lambda _, e=emp: self.edit_employee(e),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            tooltip="Sil",
                                            on_click=lambda _, e=emp: self.delete_employee(e),
                                        ),
                                    ], spacing=0),
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
                                    ft.Icon(ft.Icons.ADD_CIRCLE),
                                    ft.Text("Yeni Çalışan"),
                                ], spacing=6),
                                on_click=lambda _: self.add_employee(),
                            ),
                            ft.Spacer(),
                            ft.Text(f"Toplam: {len(employees)}", size=12, color=ft.Colors.GREY),
                        ]),
                        ft.Divider(),
                        ft.Column(
                            controls=emp_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
        except Exception as e:
            logger.error(f"Error loading employees: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    def build_timesheets_tab(self) -> ft.Column:
        """Build timesheets management tab"""
        try:
            with get_db() as db:
                # Get timesheets for current period
                today = date.today()
                region = self.auth.region if self.auth.region != "ALL" else None
                
                query = db.query(Timesheet).filter(
                    Timesheet.date >= today.replace(day=1)
                )
                
                if region and not self.auth.has_permission(Permission.VIEW_ALL_REGIONS):
                    query = query.join(Employee).filter(Employee.region == region)
                
                timesheets = query.order_by(Timesheet.date.desc()).all()
                
                if not timesheets:
                    return ft.Column([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=100, color=ft.Colors.GREY_600),
                        ft.Text("Bu ay puantaj kaydı yok", size=16, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
                
                ts_list = []
                for ts in timesheets:
                    emp_name = ts.employee.full_name if ts.employee else "?"
                    status_color = ft.Colors.GREEN if ts.checkout_time else ft.Colors.ORANGE
                    status_text = "Çıkış yapıldı" if ts.checkout_time else "Devam ediyor"
                    
                    ts_list.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.SCHEDULE, color=status_color),
                                    title=ft.Text(f"{emp_name} - {ts.date}", weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(
                                        f"{ts.checkin_time} → {ts.checkout_time or 'Devam'} • {status_text}"
                                    ),
                                    trailing=ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT if ts.checkout_time else ft.Icons.LOGOUT,
                                            tooltip="Çıkış" if not ts.checkout_time else "Düzenle",
                                            on_click=lambda _, t=ts: self.checkout_timesheet(t) if not t.checkout_time else self.edit_timesheet(t),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            tooltip="Sil",
                                            on_click=lambda _, t=ts: self.delete_timesheet(t),
                                        ),
                                    ], spacing=0),
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
                                    ft.Icon(ft.Icons.ADD_CIRCLE),
                                    ft.Text("Giriş Kaydı"),
                                ], spacing=6),
                                on_click=lambda _: self.checkin_timesheet(),
                            ),
                            ft.Spacer(),
                            ft.Text(f"Bu ay: {len(timesheets)}", size=12, color=ft.Colors.GREY),
                        ]),
                        ft.Divider(),
                        ft.Column(
                            controls=ts_list,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ],
                    expand=True,
                )
        
        except Exception as e:
            logger.error(f"Error loading timesheets: {e}")
            return ft.Text(f"Hata: {e}", color=ft.Colors.RED)
    
    # Employee methods
    def add_employee(self):
        """Add new employee - TODO: Implement dialog"""
        self.app.show_snackbar("Çalışan ekleme özelliği yakında eklenecek")
    
    def edit_employee(self, employee: Employee):
        """Edit employee - TODO: Implement dialog"""
        self.app.show_snackbar(f"Düzenleme: {employee.full_name}")
    
    def delete_employee(self, employee: Employee):
        """Delete employee - TODO: Implement confirmation"""
        self.app.show_snackbar(f"Silindi: {employee.full_name}")
    
    # Timesheet methods
    def checkin_timesheet(self):
        """Check in for timesheet - TODO: Implement dialog"""
        self.app.show_snackbar("Giriş kaydı başlıyor...")
    
    def checkout_timesheet(self, timesheet: Timesheet):
        """Check out from timesheet"""
        try:
            with get_db() as db:
                ts = db.query(Timesheet).filter(Timesheet.id == timesheet.id).first()
                if ts:
                    ts.checkout_time = datetime.now().strftime("%H:%M")
                    db.commit()
                    logger.info(f"Checkout: {ts.employee.full_name} at {ts.checkout_time}")
                    self.app.show_snackbar(f"Çıkış yapıldı: {ts.checkout_time}")
                    self.app.page.update()
        except Exception as e:
            logger.error(f"Error checking out: {e}")
            self.app.show_snackbar(f"Hata: {e}")
    
    def edit_timesheet(self, timesheet: Timesheet):
        """Edit timesheet - TODO: Implement dialog"""
        self.app.show_snackbar(f"Düzenleme: {timesheet.date}")
    
    def delete_timesheet(self, timesheet: Timesheet):
        """Delete timesheet - TODO: Implement confirmation"""
        self.app.show_snackbar(f"Silindi: {timesheet.date}")
