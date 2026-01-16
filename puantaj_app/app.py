import os
import csv
import zipfile
from datetime import datetime, date, time, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

import calc
from openpyxl import load_workbook
from tkcalendar import DateEntry

import db
import report

try:
    import winsound
except ImportError:
    winsound = None
try:
    import requests
except ImportError:
    requests = None

DATE_FMT = "YYYY-MM-DD"
TIME_FMT = "HH:MM"
KEEPALIVE_SECONDS = 300
REGIONS = ["Ankara", "Izmir", "Bursa", "Istanbul"]
DEFAULT_OIL_INTERVAL_KM = 14000
DEFAULT_OIL_SOON_KM = 2000

VEHICLE_CHECKLIST = [
    ("body_dent", "Govde ezik/cizik"),
    ("paint_damage", "Boya hasari"),
    ("interior_clean", "Ic temizligi"),
    ("smoke_smell", "Sigara kokusu"),
    ("tire_condition", "Lastik durumu"),
    ("lights", "Far/stop/sinyal"),
    ("glass", "Camlar"),
    ("warning_lamps", "Ikaz lambalari"),
    ("water_level", "Su seviyesi"),
]

EMP_HEADER_ALIASES = {
    "full_name": ["ad soyad", "adsoyad", "calisan", "calisan adi", "name", "full_name"],
    "identity_no": ["tckn", "tc", "tc kimlik", "identity", "identity_no"],
    "department": ["departman", "department"],
    "title": ["unvan", "title"],
}

TS_HEADER_ALIASES = {
    "employee": ["calisan", "ad soyad", "employee", "full_name", "name"],
    "work_date": ["tarih", "date", "work_date"],
    "start_time": ["giris", "start", "start_time"],
    "end_time": ["cikis", "end", "end_time"],
    "break_minutes": ["mola", "mola dk", "mola dakika", "break", "break_minutes"],
    "is_special": ["ozel gun", "ozel", "resmi tatil", "special", "is_special"],
    "notes": ["not", "notes", "aciklama"],
}


def ensure_app_dirs():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)


def parse_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def normalize_date(value):
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("Tarih formati gecersiz. Ornek: 2026-01-05 veya 05.01.2026")


def normalize_time(value):
    if value is None:
        raise ValueError("Saat bos olamaz.")
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, (int, float)) and 0 <= value < 1:
        total_minutes = int(round(value * 24 * 60))
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    text = str(value).strip()
    if not text:
        raise ValueError("Saat bos olamaz.")
    text = text.replace(".", ":")
    if text.isdigit() and len(text) in (3, 4):
        if len(text) == 3:
            text = "0" + text
        return f"{text[:2]}:{text[2:]}"
    if ":" in text:
        parts = text.split(":")
        if len(parts) >= 2:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    raise ValueError("Saat formati gecersiz. Ornek: 09:30")


def normalize_time_in_var(textvariable):
    raw = textvariable.get().strip()
    if not raw:
        return
    try:
        textvariable.set(normalize_time(raw))
    except ValueError:
        pass


def parse_bool(value):
    text = str(value or "").strip().lower()
    return text in {"1", "true", "evet", "yes", "y", "t"}


def parse_month(value):
    text = (value or "").strip()
    if len(text) != 7 or text[4] != "-":
        raise ValueError("Ay formati gecersiz. Ornek: 2026-01")
    year = int(text[:4])
    month = int(text[5:7])
    if month < 1 or month > 12:
        raise ValueError("Ay formati gecersiz. Ornek: 2026-01")
    return year, month


def days_until(date_text):
    if not date_text:
        return None
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (dt - datetime.now().date()).days


def week_start_from_date(date_text):
    dt = datetime.strptime(date_text, "%Y-%m-%d").date()
    start = dt - timedelta(days=dt.weekday())
    return start.strftime("%Y-%m-%d")


def week_end_from_start(week_start):
    dt = datetime.strptime(week_start, "%Y-%m-%d").date()
    end = dt + timedelta(days=6)
    return end.strftime("%Y-%m-%d")


def normalize_vehicle_status(value):
    text = str(value or "").strip()
    mapping = {
        "OK": "Olumlu",
        "Issue": "Olumsuz",
        "NA": "Bilinmiyor",
        "Olumlu": "Olumlu",
        "Olumsuz": "Olumsuz",
        "Bilinmiyor": "Bilinmiyor",
    }
    return mapping.get(text, text or "-")


def normalize_date_value(value):
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if value is None:
        raise ValueError("Tarih bos olamaz.")
    return normalize_date(str(value))


def normalize_time_value(value):
    return normalize_time(value)


def normalize_header(value):
    text = str(value or "").strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def build_header_aliases(raw_map):
    return {key: {normalize_header(a) for a in aliases} for key, aliases in raw_map.items()}


EMP_HEADER_MAP = build_header_aliases(EMP_HEADER_ALIASES)
TS_HEADER_MAP = build_header_aliases(TS_HEADER_ALIASES)


def map_headers(header_row, header_map):
    mapping = {}
    for idx, value in enumerate(header_row):
        key = normalize_header(value)
        for target, aliases in header_map.items():
            if key in aliases:
                mapping[target] = idx
    return mapping


def load_tabular_file(path):
    ext = os.path.splitext(path)[1].lower()
    rows = []
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.get_dialect("excel")
            reader = csv.reader(handle, dialect)
            for row in reader:
                rows.append(row)
    else:
        wb = load_workbook(path, data_only=True)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
    return [row for row in rows if any(cell is not None and str(cell).strip() for cell in row)]


def create_labeled_entry(parent, label, textvariable, width=24):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Entry(frame, textvariable=textvariable, width=width).pack(side=tk.LEFT)
    return frame


def create_labeled_date(parent, label, textvariable, width=12):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 8))
    date_entry = DateEntry(frame, textvariable=textvariable, width=width, date_pattern="yyyy-mm-dd")
    date_entry.pack(side=tk.LEFT)
    return frame, date_entry


def create_time_entry(parent, label, textvariable, width=8):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 8))
    entry = ttk.Entry(frame, textvariable=textvariable, width=width)
    entry.pack(side=tk.LEFT)
    return frame


def set_time_vars(time_value, textvariable):
    try:
        normalized = normalize_time(time_value)
    except ValueError:
        return
    textvariable.set(normalized)


def clear_date_entry(entry):
    try:
        entry.delete(0, tk.END)
    except Exception:
        pass


def ensure_logo_asset(path):
    if os.path.isfile(path):
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    width, height = 320, 80
    img = Image.new("RGB", (width, height), "#e7eef6")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 8, width - 8, height - 8], radius=18, fill="#cfe1f2")
    # Minimalist rain drop icon
    drop_x, drop_y = 28, 18
    draw.polygon(
        [(drop_x + 16, drop_y), (drop_x, drop_y + 24), (drop_x + 16, drop_y + 46), (drop_x + 32, drop_y + 24)],
        fill="#2f6fed",
        outline="#2a5fd1",
    )
    draw.ellipse([drop_x + 6, drop_y + 24, drop_x + 26, drop_y + 44], fill="#2f6fed", outline="#2a5fd1")
    draw.ellipse([drop_x + 14, drop_y + 10, drop_x + 20, drop_y + 16], fill="#bfe0ff")
    text = "RAINSTAFF"
    try:
        font = ImageFont.truetype("Consola.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    draw.text((84, 22), text, fill="#0f2438", font=font)
    try:
        sub_font = ImageFont.truetype("Consola.ttf", 14)
    except Exception:
        sub_font = ImageFont.load_default()
    draw.text((86, 48), "PUANTAJ", fill="#425466", font=sub_font)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def load_logo_image(path, target_height=48):
    try:
        from PIL import Image, ImageTk
    except Exception:
        Image = None
        ImageTk = None

    if Image and ImageTk:
        try:
            img = Image.open(path)
            ratio = target_height / float(img.height)
            target_width = int(img.width * ratio)
            img = img.resize((target_width, target_height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None
    try:
        return tk.PhotoImage(file=path)
    except Exception:
        return None


class PuantajApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rainstaff")
        self.geometry("1100x720")
        self.minsize(980, 640)

        self.current_user = None
        self.current_region = None
        self.is_admin = False

        self.settings = db.get_all_settings()
        self.admin_region_var = tk.StringVar(value=self.settings.get("admin_entry_region", "Ankara"))
        self.employee_map = {}
        self.employee_details = {}
        self.vehicle_map = {}
        self.driver_map = {}
        self.fault_map = {}
        self.service_visit_map = {}
        self.shift_template_map = {}
        self.status_var = tk.StringVar()
        self.ts_original = None
        self.ts_editing_id = None
        self.vehicle_original_plate = None
        self._tab_loaded = {}

        if not self._login_prompt():
            self.destroy()
            return

        self._configure_style()
        self._build_ui()
        self._load_tab_data(self.tab_employees)
        self._start_keepalive()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_keepalive(self):
        self._keepalive_stop = threading.Event()
        thread = threading.Thread(target=self._keepalive_worker, daemon=True)
        thread.start()

    def _keepalive_worker(self):
        while not self._keepalive_stop.wait(KEEPALIVE_SECONDS):
            if requests is None:
                continue
            settings = db.get_all_settings()
            enabled = settings.get("sync_enabled") == "1"
            sync_url = settings.get("sync_url", "").strip()
            token = settings.get("sync_token", "").strip()
            if not enabled or not sync_url:
                continue
            try:
                headers = {"X-API-KEY": token} if token else {}
                url = sync_url.rstrip("/") + "/health"
                requests.get(url, headers=headers, timeout=6)
            except Exception:
                pass

    def _on_close(self):
        if hasattr(self, "_keepalive_stop"):
            self._keepalive_stop.set()
        self.destroy()

    def _login_prompt(self):
        dialog = tk.Toplevel(self)
        dialog.title("Giris")
        dialog.geometry("320x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        username_var = tk.StringVar()
        password_var = tk.StringVar()

        tk.Label(dialog, text="Kullanici Adi").pack(pady=(16, 4))
        tk.Entry(dialog, textvariable=username_var).pack()
        tk.Label(dialog, text="Sifre").pack(pady=(8, 4))
        tk.Entry(dialog, textvariable=password_var, show="*").pack()

        status_var = tk.StringVar()
        tk.Label(dialog, textvariable=status_var, fg="#b94a48").pack(pady=(6, 0))

        success = {"ok": False}

        def attempt_login():
            user = db.verify_user(username_var.get().strip(), password_var.get().strip())
            if not user:
                status_var.set("Giris hatali.")
                return
            self.current_user = user["username"]
            self.is_admin = user["role"] == "admin"
            self.current_region = user["region"] if not self.is_admin else "ALL"
            success["ok"] = True
            dialog.destroy()

        btn = tk.Button(dialog, text="Giris", command=attempt_login)
        btn.pack(pady=12)
        dialog.bind("<Return>", lambda _e: attempt_login())

        self.wait_window(dialog)
        return success["ok"]

    def _view_region(self):
        return None if self.is_admin else self.current_region

    def _entry_region(self):
        if self.is_admin:
            value = self.admin_region_var.get().strip()
            return value or "Ankara"
        return self.current_region

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        accent = "#2f6fed"
        soft = "#EAF2FB"
        gray = "#5f6a72"
        card = "#f5f7fb"
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2C3E50", background=soft)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#4A90E2", background=soft)
        style.configure("Section.TLabelframe", padding=(12, 10))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=gray)
        style.configure("Accent.TButton", padding=(10, 6), background=accent, foreground="white")
        style.configure("TButton", padding=(8, 4))
        style.configure("Treeview", rowheight=26, fieldbackground=card, background="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#dfe7f3")
        style.configure("TFrame", background=soft)
        style.configure("TLabel", background=soft)
        style.configure("TNotebook", background=soft, tabmargins=(6, 6, 6, 0))
        style.configure("TNotebook.Tab", padding=(12, 6))
        style.configure("TEntry", padding=(6, 4))
        style.configure("TCombobox", padding=(6, 4))
        style.map(
            "Accent.TButton",
            background=[("active", "#1e58d6")],
            foreground=[("active", "white")],
        )

    def _build_ui(self):
        header = tk.Frame(self, bg="#EAF2FB", height=120)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "rainstaff_logo_1.png")
        self._logo_image = load_logo_image(logo_path, target_height=104)
        if self._logo_image:
            logo_label = tk.Label(header, image=self._logo_image, bg="#EAF2FB")
            logo_label.place(x=20, y=8)

        divider = tk.Frame(self, bg="#d9dfe7", height=1)
        divider.pack(fill=tk.X)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_employees = ttk.Frame(self.notebook)
        self.tab_timesheets = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_admin = ttk.Frame(self.notebook)
        self.tab_vehicles = ttk.Frame(self.notebook)
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_service = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_employees, text="Calisanlar")
        self.notebook.add(self.tab_timesheets, text="Puantaj")
        self.notebook.add(self.tab_reports, text="Rapor")
        self.notebook.add(self.tab_settings, text="Ayarlar")
        self.notebook.add(self.tab_admin, text="Yonetici")
        self.notebook.add(self.tab_vehicles, text="Araclar")
        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_service, text="Servis/Ariza")

        self.tab_employees_body = self._make_tab_scrollable(self.tab_employees)
        self.tab_timesheets_body = self._make_tab_scrollable(self.tab_timesheets)
        self.tab_reports_body = self._make_tab_scrollable(self.tab_reports)
        self.tab_settings_body = self._make_tab_scrollable(self.tab_settings)
        self.tab_admin_body = self._make_tab_scrollable(self.tab_admin)
        self.tab_vehicles_body = self._make_tab_scrollable(self.tab_vehicles)
        self.tab_dashboard_body = self._make_tab_scrollable(self.tab_dashboard)
        self.tab_service_body = self._make_tab_scrollable(self.tab_service)

        self._build_employees_tab()
        self._build_timesheets_tab()
        self._build_reports_tab()
        self._build_settings_tab()
        self._build_admin_tab()
        self._build_vehicles_tab()
        self._build_dashboard_tab()
        self._build_service_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W, foreground="#2b6cb0")
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.status_var.set("Hazir")

    def _on_tab_changed(self, _event):
        current = self.notebook.nametowidget(self.notebook.select())
        self._load_tab_data(current)

    def _load_tab_data(self, tab):
        if self._tab_loaded.get(tab):
            return
        if tab is self.tab_employees:
            self.refresh_employees()
        elif tab is self.tab_timesheets:
            self.refresh_employees()
            self.refresh_timesheets()
        elif tab is self.tab_reports:
            self.refresh_report_archive()
        elif tab is self.tab_settings:
            self.refresh_shift_templates()
        elif tab is self.tab_admin:
            self.refresh_admin_summary()
        elif tab is self.tab_vehicles:
            self.refresh_vehicles()
            self.refresh_drivers()
            self.refresh_faults()
            self.refresh_service_visits()
        elif tab is self.tab_dashboard:
            self.refresh_vehicle_dashboard()
        elif tab is self.tab_service:
            self.refresh_service_visits()
        self._tab_loaded[tab] = True

    def _make_tab_scrollable(self, tab):
        canvas = tk.Canvas(tab, highlightthickness=0)
        vscroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        hscroll = ttk.Scrollbar(tab, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")

        content = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(window_id, width=e.width),
        )
        content.bind("<Enter>", lambda _e: self._bind_canvas_mousewheel(canvas))
        content.bind("<Leave>", lambda _e: self._unbind_canvas_mousewheel(canvas))
        return content

    def _bind_canvas_mousewheel(self, canvas):
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _unbind_canvas_mousewheel(self, canvas):
        canvas.unbind_all("<MouseWheel>")

    def trigger_sync(self, reason="manual", force=False):
        if force and hasattr(self, "sync_enabled_var"):
            enabled = self.sync_enabled_var.get()
            sync_url = self.sync_url_var.get().strip()
            token = self.sync_token_var.get().strip()
        else:
            self.settings = db.get_all_settings()
            enabled = self.settings.get("sync_enabled") == "1"
            sync_url = self.settings.get("sync_url", "").strip()
            token = self.settings.get("sync_token", "").strip()
        if not enabled:
            self.status_var.set("Senkron kapali")
            return
        if requests is None:
            self.status_var.set("Senkron icin requests kurulu degil")
            return
        if not sync_url:
            self.status_var.set("Senkron URL bos")
            return
        self.status_var.set("Senkron basladi...")
        thread = threading.Thread(target=self._sync_worker, args=(sync_url, token, reason), daemon=True)
        thread.start()

    def _sync_worker(self, sync_url, token, reason):
        try:
            with open(db.DB_PATH, "rb") as handle:
                files = {"db": ("puantaj.db", handle, "application/octet-stream")}
                headers = {"X-API-KEY": token, "X-REASON": reason}
                url = sync_url.rstrip("/") + "/sync"
                resp = requests.post(url, headers=headers, files=files, timeout=10)
            if resp.status_code != 200:
                msg = f"Senkron hatasi: {resp.status_code}"
            else:
                msg = "Senkron basarili"
        except Exception:
            msg = "Senkron hatasi"
        self.after(0, lambda: self._notify_sync_result(msg, reason))

    def manual_sync(self):
        if not self.sync_enabled_var.get():
            messagebox.showwarning("Uyari", "Senkron kapali. Ayarlardan acin.")
            return
        self.trigger_sync("manual", force=True)

    def _notify_sync_result(self, message, reason):
        self.status_var.set(message)
        if reason == "manual":
            messagebox.showinfo("Senkron", message)

    # Employees tab
    def _build_employees_tab(self):
        form = ttk.LabelFrame(self.tab_employees_body, text="Calisan Bilgisi", style="Section.TLabelframe")
        form.pack(fill=tk.X, padx=6, pady=6)

        self.emp_id_var = tk.StringVar()
        self.emp_name_var = tk.StringVar()
        self.emp_identity_var = tk.StringVar()
        self.emp_department_var = tk.StringVar()
        self.emp_title_var = tk.StringVar()

        row1 = ttk.Frame(form)
        row1.pack(fill=tk.X, pady=4)
        create_labeled_entry(row1, "Ad Soyad", self.emp_name_var, 30).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row1, "TCKN", self.emp_identity_var, 18).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row1, "Departman", self.emp_department_var, 18).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row1, "Unvan", self.emp_title_var, 18).pack(side=tk.LEFT, padx=6)

        btn_row = ttk.Frame(form)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="Kaydet", style="Accent.TButton", command=self.add_or_update_employee).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btn_row, text="Sil", command=self.delete_employee).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Temizle", command=self.clear_employee_form).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Excel/CSV Iceri Aktar", command=self.import_employees).pack(side=tk.LEFT, padx=6)

        list_frame = ttk.Frame(self.tab_employees_body)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        columns = ("id", "name", "identity", "department", "title")
        self.employee_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.employee_tree.heading("id", text="ID")
        self.employee_tree.heading("name", text="Ad Soyad")
        self.employee_tree.heading("identity", text="TCKN")
        self.employee_tree.heading("department", text="Departman")
        self.employee_tree.heading("title", text="Unvan")
        self.employee_tree.column("id", width=60, anchor=tk.CENTER)
        self.employee_tree.column("name", width=220)
        self.employee_tree.column("identity", width=140)
        self.employee_tree.column("department", width=160)
        self.employee_tree.column("title", width=160)
        self.employee_tree.tag_configure("odd", background="#f5f7fb")
        emp_xscroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.employee_tree.xview)
        emp_yscroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.employee_tree.yview)
        self.employee_tree.configure(xscrollcommand=emp_xscroll.set, yscrollcommand=emp_yscroll.set)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.employee_tree.grid(row=0, column=0, sticky="nsew")
        emp_yscroll.grid(row=0, column=1, sticky="ns")
        emp_xscroll.grid(row=1, column=0, sticky="ew")
        self.employee_tree.bind("<<TreeviewSelect>>", self.on_employee_select)

    def refresh_employees(self):
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
        self.employee_map = {}
        self.employee_details = {}
        for emp in db.list_employees(region=self._view_region()):
            emp_id, name, identity_no, department, title = emp
            tag = "odd" if len(self.employee_tree.get_children()) % 2 else "even"
            self.employee_tree.insert("", tk.END, values=emp, tags=(tag,))
            self.employee_map[name] = emp_id
            self.employee_details[name] = {
                "department": department or "",
                "title": title or "",
                "identity_no": identity_no or "",
            }
        self._refresh_employee_comboboxes()

    def _refresh_employee_comboboxes(self):
        values = ["Tum Calisanlar"] + sorted(self.employee_map.keys())
        if hasattr(self, "ts_employee_combo"):
            self.ts_employee_combo["values"] = values
        if hasattr(self, "ts_filter_combo"):
            self.ts_filter_combo["values"] = values
        if hasattr(self, "report_employee_combo"):
            self.report_employee_combo["values"] = values
        if hasattr(self, "admin_employee_combo"):
            self.admin_employee_combo["values"] = values
        if hasattr(self, "admin_department_combo"):
            departments = sorted({d["department"] for d in self.employee_details.values() if d["department"]})
            self.admin_department_combo["values"] = ["Tum Departmanlar"] + departments
        if hasattr(self, "admin_title_combo"):
            titles = sorted({d["title"] for d in self.employee_details.values() if d["title"]})
            self.admin_title_combo["values"] = ["Tum Unvanlar"] + titles

    def clear_employee_form(self):
        self.emp_id_var.set("")
        self.emp_name_var.set("")
        self.emp_identity_var.set("")
        self.emp_department_var.set("")
        self.emp_title_var.set("")

    def on_employee_select(self, _event=None):
        selected = self.employee_tree.selection()
        if not selected:
            return
        values = self.employee_tree.item(selected[0], "values")
        self.emp_id_var.set(values[0])
        self.emp_name_var.set(values[1])
        self.emp_identity_var.set(values[2])
        self.emp_department_var.set(values[3])
        self.emp_title_var.set(values[4])

    def add_or_update_employee(self):
        name = self.emp_name_var.get().strip()
        if not name:
            messagebox.showwarning("Uyari", "Ad Soyad zorunlu.")
            return
        identity_no = self.emp_identity_var.get().strip()
        department = self.emp_department_var.get().strip()
        title = self.emp_title_var.get().strip()

        emp_id = self.emp_id_var.get().strip()
        if emp_id:
            db.update_employee(
                parse_int(emp_id),
                name,
                identity_no,
                department,
                title,
                self._entry_region(),
            )
        else:
            db.add_employee(name, identity_no, department, title, self._entry_region())
        self.refresh_employees()
        self.clear_employee_form()
        self.trigger_sync("employee")

    def delete_employee(self):
        emp_id = self.emp_id_var.get().strip()
        if not emp_id:
            messagebox.showwarning("Uyari", "Silmek icin calisan secin.")
            return
        if messagebox.askyesno("Onay", "Calisani silmek istiyor musunuz?"):
            db.delete_employee(parse_int(emp_id))
            self.refresh_employees()
            self.clear_employee_form()
            self.trigger_sync("employee_delete")

    def notify(self, message, sound=True, duration_ms=2500):
        self.status_var.set(message)
        if sound and winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
        self.after(duration_ms, lambda: self.status_var.set(""))

    # Timesheets tab
    def _build_timesheets_tab(self):
        form = ttk.LabelFrame(self.tab_timesheets_body, text="Puantaj Girisi", style="Section.TLabelframe")
        form.pack(fill=tk.X, padx=6, pady=6)

        self.ts_id_var = tk.StringVar()
        self.ts_employee_var = tk.StringVar()
        self.ts_date_var = tk.StringVar()
        self.ts_start_var = tk.StringVar(value="09:00")
        self.ts_end_var = tk.StringVar(value="18:00")
        self.ts_break_var = tk.StringVar(value="60")
        self.ts_notes_var = tk.StringVar()
        self.ts_template_var = tk.StringVar()
        self.ts_special_var = tk.IntVar(value=0)

        row1 = ttk.Frame(form)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Calisan").pack(side=tk.LEFT, padx=(0, 8))
        self.ts_employee_combo = ttk.Combobox(row1, textvariable=self.ts_employee_var, width=28, state="readonly")
        self.ts_employee_combo.pack(side=tk.LEFT)
        date_frame, self.ts_date_entry = create_labeled_date(row1, "Tarih", self.ts_date_var, 12)
        date_frame.pack(side=tk.LEFT, padx=6)
        start_frame = create_time_entry(row1, "Giris", self.ts_start_var, 8)
        start_frame.pack(side=tk.LEFT, padx=6)
        end_frame = create_time_entry(row1, "Cikis", self.ts_end_var, 8)
        end_frame.pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row1, "Mola dk", self.ts_break_var, 8).pack(side=tk.LEFT, padx=6)
        for child in start_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.bind("<FocusOut>", lambda _e: normalize_time_in_var(self.ts_start_var))
        for child in end_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.bind("<FocusOut>", lambda _e: normalize_time_in_var(self.ts_end_var))

        row2 = ttk.Frame(form)
        row2.pack(fill=tk.X, pady=4)
        create_labeled_entry(row2, "Not", self.ts_notes_var, 60).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(row2, text="Ozel Gun", variable=self.ts_special_var).pack(side=tk.LEFT, padx=6)

        row3 = ttk.Frame(form)
        row3.pack(fill=tk.X, pady=4)
        ttk.Label(row3, text="Sablon").pack(side=tk.LEFT, padx=(0, 8))
        self.ts_template_combo = ttk.Combobox(row3, textvariable=self.ts_template_var, width=28, state="readonly")
        self.ts_template_combo.pack(side=tk.LEFT)
        ttk.Button(row3, text="Uygula", command=self.apply_shift_template).pack(side=tk.LEFT, padx=6)

        btn_row = ttk.Frame(form)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="Kaydet", style="Accent.TButton", command=self.add_or_update_timesheet).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btn_row, text="Sil", command=self.delete_timesheet).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Temizle", command=self.clear_timesheet_form).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Excel/CSV Iceri Aktar", command=self.import_timesheets).pack(side=tk.LEFT, padx=6)

        filter_frame = ttk.LabelFrame(self.tab_timesheets_body, text="Filtre", style="Section.TLabelframe")
        filter_frame.pack(fill=tk.X, padx=6, pady=6)
        self.ts_filter_employee = tk.StringVar(value="Tum Calisanlar")
        self.ts_filter_start = tk.StringVar()
        self.ts_filter_end = tk.StringVar()

        ttk.Label(filter_frame, text="Calisan").pack(side=tk.LEFT, padx=(0, 8))
        self.ts_filter_combo = ttk.Combobox(filter_frame, textvariable=self.ts_filter_employee, width=28, state="readonly")
        self.ts_filter_combo.pack(side=tk.LEFT)
        start_frame, self.ts_filter_start_entry = create_labeled_date(
            filter_frame, "Baslangic", self.ts_filter_start, 12
        )
        start_frame.pack(side=tk.LEFT, padx=6)
        end_frame, self.ts_filter_end_entry = create_labeled_date(filter_frame, "Bitis", self.ts_filter_end, 12)
        end_frame.pack(side=tk.LEFT, padx=6)
        ttk.Button(filter_frame, text="Filtrele", command=self.refresh_timesheets).pack(side=tk.LEFT, padx=6)
        ttk.Button(filter_frame, text="Temizle", command=self.clear_timesheet_filter).pack(side=tk.LEFT)
        clear_date_entry(self.ts_filter_start_entry)
        clear_date_entry(self.ts_filter_end_entry)

        list_frame = ttk.Frame(self.tab_timesheets_body)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        columns = (
            "id",
            "employee",
            "date",
            "start",
            "end",
            "break",
            "worked",
            "scheduled",
            "overtime",
            "night",
            "overnight",
            "special",
            "special_normal",
            "special_overtime",
            "special_night",
            "notes",
        )
        self.timesheet_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.timesheet_tree.heading("id", text="ID")
        self.timesheet_tree.heading("employee", text="Calisan")
        self.timesheet_tree.heading("date", text="Tarih")
        self.timesheet_tree.heading("start", text="Giris")
        self.timesheet_tree.heading("end", text="Cikis")
        self.timesheet_tree.heading("break", text="Mola")
        self.timesheet_tree.heading("worked", text="Calisilan")
        self.timesheet_tree.heading("scheduled", text="Plan")
        self.timesheet_tree.heading("overtime", text="Fazla Mesai")
        self.timesheet_tree.heading("night", text="Gece")
        self.timesheet_tree.heading("overnight", text="Geceye Tasan")
        self.timesheet_tree.heading("special", text="Ozel Gun")
        self.timesheet_tree.heading("special_normal", text="Ozel Gun Normal")
        self.timesheet_tree.heading("special_overtime", text="Ozel Gun Fazla")
        self.timesheet_tree.heading("special_night", text="Ozel Gun Gece")
        self.timesheet_tree.heading("notes", text="Not")
        self.timesheet_tree.column("id", width=60, anchor=tk.CENTER)
        self.timesheet_tree.column("employee", width=220)
        self.timesheet_tree.column("date", width=100)
        self.timesheet_tree.column("start", width=80)
        self.timesheet_tree.column("end", width=80)
        self.timesheet_tree.column("break", width=80)
        self.timesheet_tree.column("worked", width=90)
        self.timesheet_tree.column("scheduled", width=90)
        self.timesheet_tree.column("overtime", width=90)
        self.timesheet_tree.column("night", width=90)
        self.timesheet_tree.column("overnight", width=100)
        self.timesheet_tree.column("special", width=80)
        self.timesheet_tree.column("special_normal", width=110)
        self.timesheet_tree.column("special_overtime", width=110)
        self.timesheet_tree.column("special_night", width=110)
        self.timesheet_tree.column("notes", width=180)
        self.timesheet_tree.tag_configure("odd", background="#f5f7fb")
        ts_xscroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.timesheet_tree.xview)
        ts_yscroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.timesheet_tree.yview)
        self.timesheet_tree.configure(xscrollcommand=ts_xscroll.set, yscrollcommand=ts_yscroll.set)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.timesheet_tree.grid(row=0, column=0, sticky="nsew")
        ts_yscroll.grid(row=0, column=1, sticky="ns")
        ts_xscroll.grid(row=1, column=0, sticky="ew")
        self.timesheet_tree.bind("<<TreeviewSelect>>", self.on_timesheet_select)
        self.timesheet_tree.bind("<Button-3>", self.on_timesheet_right_click)

        self.ts_menu = tk.Menu(self, tearoff=0)
        self.ts_menu.add_command(label="Duzenle", command=self.edit_selected_timesheet)
        self.ts_menu.add_command(label="Sil", command=self.delete_timesheet)

    def clear_timesheet_form(self):
        self.ts_id_var.set("")
        self.ts_employee_var.set("")
        self.ts_date_var.set("")
        self.ts_start_var.set("09:00")
        self.ts_end_var.set("18:00")
        self.ts_break_var.set("60")
        self.ts_notes_var.set("")
        self.ts_template_var.set("")
        self.ts_special_var.set(0)
        self.ts_original = None
        self.ts_editing_id = None

    def clear_timesheet_filter(self):
        self.ts_filter_employee.set("Tum Calisanlar")
        self.ts_filter_start.set("")
        self.ts_filter_end.set("")
        clear_date_entry(self.ts_filter_start_entry)
        clear_date_entry(self.ts_filter_end_entry)
        self.refresh_timesheets()

    def on_timesheet_select(self, _event=None):
        return

    def on_timesheet_right_click(self, event):
        row_id = self.timesheet_tree.identify_row(event.y)
        if row_id:
            self.timesheet_tree.selection_set(row_id)
            self.ts_menu.tk_popup(event.x_root, event.y_root)

    def edit_selected_timesheet(self):
        selected = self.timesheet_tree.selection()
        if not selected:
            return
        values = self.timesheet_tree.item(selected[0], "values")
        self.ts_editing_id = values[0]
        self.ts_id_var.set(values[0])
        self.ts_employee_var.set(values[1])
        self.ts_date_var.set(values[2])
        set_time_vars(values[3], self.ts_start_var)
        set_time_vars(values[4], self.ts_end_var)
        self.ts_break_var.set(values[5])
        self.ts_special_var.set(1 if values[11] == "Evet" else 0)
        self.ts_notes_var.set(values[15])
        self.ts_original = (values[1], values[2], values[3], values[4])

    def refresh_timesheets(self):
        for item in self.timesheet_tree.get_children():
            self.timesheet_tree.delete(item)

        employee_name = self.ts_filter_employee.get()
        employee_id = None
        if employee_name and employee_name != "Tum Calisanlar":
            employee_id = self.employee_map.get(employee_name)
        start_date = self.ts_filter_start.get().strip() or None
        end_date = self.ts_filter_end.get().strip() or None
        try:
            if start_date:
                start_date = normalize_date(start_date)
            if end_date:
                end_date = normalize_date(end_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return

        records = db.list_timesheets(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            region=self._view_region(),
        )
        for ts in records:
            ts_id, _emp_id, name, work_date, start_time, end_time, break_minutes, is_special, notes = ts
            try:
                (
                    worked,
                    scheduled,
                    overtime,
                    night_hours,
                    overnight_hours,
                    spec_norm,
                    spec_ot,
                    spec_night,
                ) = calc.calc_day_hours(
                    work_date,
                    start_time,
                    end_time,
                    break_minutes,
                    self.settings,
                    is_special,
                )
            except Exception:
                worked = scheduled = overtime = ""
                night_hours = overnight_hours = ""
                spec_norm = spec_ot = spec_night = ""
            tag = "odd" if len(self.timesheet_tree.get_children()) % 2 else "even"
            self.timesheet_tree.insert(
                "",
                tk.END,
                values=(
                    ts_id,
                    name,
                    work_date,
                    start_time,
                    end_time,
                    break_minutes,
                    worked,
                    scheduled,
                    overtime,
                    night_hours,
                    overnight_hours,
                    "Evet" if is_special else "Hayir",
                    spec_norm,
                    spec_ot,
                    spec_night,
                    notes or "",
                ),
                tags=(tag,),
            )

        if hasattr(self, "ts_filter_combo"):
            self.ts_filter_combo["values"] = ["Tum Calisanlar"] + sorted(self.employee_map.keys())

    def add_or_update_timesheet(self):
        name = self.ts_employee_var.get().strip()
        if not name:
            messagebox.showwarning("Uyari", "Calisan secin.")
            return
        employee_id = self.employee_map.get(name)
        if not employee_id:
            messagebox.showwarning("Uyari", "Calisan bulunamadi.")
            return
        work_date = self.ts_date_var.get().strip()
        if not work_date:
            messagebox.showwarning("Uyari", "Tarih zorunlu.")
            return
        try:
            work_date = normalize_date(work_date)
            start_time = normalize_time(self.ts_start_var.get())
            end_time = normalize_time(self.ts_end_var.get())
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        break_minutes = parse_int(self.ts_break_var.get(), 0)
        notes = self.ts_notes_var.get().strip()
        is_special = 1 if self.ts_special_var.get() else 0

        ts_id = self.ts_editing_id
        if ts_id:
            db.update_timesheet(
                parse_int(ts_id),
                employee_id,
                work_date,
                start_time,
                end_time,
                break_minutes,
                is_special,
                notes,
                self._entry_region(),
            )
        else:
            db.add_timesheet(
                employee_id,
                work_date,
                start_time,
                end_time,
                break_minutes,
                is_special,
                notes,
                self._entry_region(),
            )
        self.refresh_timesheets()
        self.clear_timesheet_form()
        self.trigger_sync("timesheet")
        self.notify("Puantaj kaydedildi.")

    def delete_timesheet(self):
        ts_id = self.ts_editing_id
        if not ts_id:
            selected = self.timesheet_tree.selection()
            if selected:
                values = self.timesheet_tree.item(selected[0], "values")
                ts_id = values[0]
        if not ts_id:
            messagebox.showwarning("Uyari", "Silmek icin puantaj secin.")
            return
        if messagebox.askyesno("Onay", "Puantaj kaydini silmek istiyor musunuz?"):
            db.delete_timesheet(parse_int(ts_id))
            self.refresh_timesheets()
            self.clear_timesheet_form()
            self.notify("Puantaj silindi.")
            self.trigger_sync("timesheet_delete")

    def refresh_shift_templates(self):
        templates = db.list_shift_templates()
        self.shift_template_map = {tpl[1]: tpl for tpl in templates}
        if hasattr(self, "ts_template_combo"):
            self.ts_template_combo["values"] = sorted(self.shift_template_map.keys())
            if not self.ts_template_var.get() and templates:
                self.ts_template_var.set(templates[0][1])
                self.apply_shift_template()
        if hasattr(self, "template_tree"):
            for item in self.template_tree.get_children():
                self.template_tree.delete(item)
            for tpl in templates:
                tag = "odd" if len(self.template_tree.get_children()) % 2 else "even"
                self.template_tree.insert("", tk.END, values=tpl, tags=(tag,))

    def apply_shift_template(self):
        name = self.ts_template_var.get().strip()
        if not name or name not in self.shift_template_map:
            messagebox.showwarning("Uyari", "Sablon secin.")
            return
        _tpl_id, _name, start_time, end_time, break_minutes = self.shift_template_map[name]
        set_time_vars(start_time, self.ts_start_var)
        set_time_vars(end_time, self.ts_end_var)
        self.ts_break_var.set(str(break_minutes))

    def save_shift_template(self):
        name = self.st_name_var.get().strip()
        if not name:
            messagebox.showwarning("Uyari", "Sablon adi zorunlu.")
            return
        try:
            start_time = normalize_time(self.st_start_var.get())
            end_time = normalize_time(self.st_end_var.get())
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        break_minutes = parse_int(self.st_break_var.get(), 0)
        db.upsert_shift_template(name, start_time, end_time, break_minutes)
        self.refresh_shift_templates()
        self.clear_shift_template_form()

    def delete_shift_template(self):
        tpl_id = self.st_id_var.get().strip()
        if not tpl_id:
            messagebox.showwarning("Uyari", "Silmek icin sablon secin.")
            return
        if messagebox.askyesno("Onay", "Sablonu silmek istiyor musunuz?"):
            db.delete_shift_template(parse_int(tpl_id))
            self.refresh_shift_templates()
            self.clear_shift_template_form()

    def clear_shift_template_form(self):
        self.st_id_var.set("")
        self.st_name_var.set("")
        self.st_start_var.set("09:00")
        self.st_end_var.set("18:00")
        self.st_break_var.set("60")

    def on_template_select(self, _event=None):
        selected = self.template_tree.selection()
        if not selected:
            return
        values = self.template_tree.item(selected[0], "values")
        self.st_id_var.set(values[0])
        self.st_name_var.set(values[1])
        set_time_vars(values[2], self.st_start_var)
        set_time_vars(values[3], self.st_end_var)
        self.st_break_var.set(values[4])

    def import_employees(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV", "*.xlsx;*.csv"), ("Excel", "*.xlsx"), ("CSV", "*.csv"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            rows = load_tabular_file(path)
        except Exception as exc:
            messagebox.showerror("Hata", f"Dosya okunamadi: {exc}")
            return
        if not rows:
            messagebox.showinfo("Bilgi", "Dosyada veri bulunamadi.")
            return

        header_map = map_headers(rows[0], EMP_HEADER_MAP)
        start_idx = 1 if "full_name" in header_map else 0
        existing_names = set(self.employee_map.keys())
        imported = 0
        skipped = 0
        for row in rows[start_idx:]:
            def cell(idx):
                return row[idx] if idx is not None and idx < len(row) else ""

            if "full_name" in header_map:
                name = str(cell(header_map.get("full_name"))).strip()
                identity_no = str(cell(header_map.get("identity_no"))).strip()
                department = str(cell(header_map.get("department"))).strip()
                title = str(cell(header_map.get("title"))).strip()
            else:
                name = str(cell(0)).strip()
                identity_no = str(cell(1)).strip() if len(row) > 1 else ""
                department = str(cell(2)).strip() if len(row) > 2 else ""
                title = str(cell(3)).strip() if len(row) > 3 else ""

            if not name or name in existing_names:
                skipped += 1
                continue
            db.add_employee(name, identity_no, department, title, self._entry_region())
            existing_names.add(name)
            imported += 1

        self.refresh_employees()
        messagebox.showinfo("Bilgi", f"Iceri aktarma tamamlandi. Eklenen: {imported}, Atlanan: {skipped}")

    def import_timesheets(self):
        if not self.employee_map:
            messagebox.showwarning("Uyari", "Once calisan ekleyin.")
            return
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV", "*.xlsx;*.csv"), ("Excel", "*.xlsx"), ("CSV", "*.csv"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            rows = load_tabular_file(path)
        except Exception as exc:
            messagebox.showerror("Hata", f"Dosya okunamadi: {exc}")
            return
        if not rows:
            messagebox.showinfo("Bilgi", "Dosyada veri bulunamadi.")
            return

        header_map = map_headers(rows[0], TS_HEADER_MAP)
        start_idx = 1 if "employee" in header_map else 0
        imported = 0
        skipped = 0
        missing_employee = 0

        for row in rows[start_idx:]:
            def cell(idx):
                return row[idx] if idx is not None and idx < len(row) else ""

            if "employee" in header_map:
                employee_name = str(cell(header_map.get("employee"))).strip()
                work_date = cell(header_map.get("work_date"))
                start_time = cell(header_map.get("start_time"))
                end_time = cell(header_map.get("end_time"))
                break_minutes = cell(header_map.get("break_minutes"))
                is_special = cell(header_map.get("is_special"))
                notes = str(cell(header_map.get("notes"))).strip()
            else:
                employee_name = str(cell(0)).strip()
                work_date = cell(1)
                start_time = cell(2)
                end_time = cell(3)
                break_minutes = cell(4) if len(row) > 4 else 0
                is_special = cell(5) if len(row) > 5 else 0
                notes = str(cell(6)).strip() if len(row) > 6 else ""

            if not employee_name:
                skipped += 1
                continue
            employee_id = self.employee_map.get(employee_name)
            if not employee_id:
                missing_employee += 1
                continue
            try:
                work_date = normalize_date_value(work_date)
                start_time = normalize_time_value(start_time)
                end_time = normalize_time_value(end_time)
            except ValueError:
                skipped += 1
                continue
            break_minutes = parse_int(break_minutes, 0)
            is_special = 1 if parse_bool(is_special) else 0

            db.add_timesheet(
                employee_id,
                work_date,
                start_time,
                end_time,
                break_minutes,
                is_special,
                notes,
                self._entry_region(),
            )
            imported += 1

        self.refresh_timesheets()
        messagebox.showinfo(
            "Bilgi",
            f"Iceri aktarma tamamlandi. Eklenen: {imported}, Atlanan: {skipped}, Calisan bulunamadi: {missing_employee}",
        )

    # Reports tab
    def _build_reports_tab(self):
        frame = ttk.LabelFrame(self.tab_reports_body, text="Excel Raporu", style="Section.TLabelframe")
        frame.pack(fill=tk.X, padx=6, pady=6)

        self.report_employee_var = tk.StringVar(value="Tum Calisanlar")
        self.report_start_var = tk.StringVar()
        self.report_end_var = tk.StringVar()
        self.report_use_dates = tk.BooleanVar(value=False)

        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="Calisan").pack(side=tk.LEFT, padx=(0, 8))
        self.report_employee_combo = ttk.Combobox(row1, textvariable=self.report_employee_var, width=28, state="readonly")
        self.report_employee_combo.pack(side=tk.LEFT)
        report_start_frame, self.report_start_entry = create_labeled_date(
            row1, "Baslangic", self.report_start_var, 12
        )
        report_start_frame.pack(side=tk.LEFT, padx=6)
        report_end_frame, self.report_end_entry = create_labeled_date(
            row1, "Bitis", self.report_end_var, 12
        )
        report_end_frame.pack(side=tk.LEFT, padx=6)
        ttk.Button(row1, text="Rapor Olustur", style="Accent.TButton", command=self.export_report).pack(
            side=tk.LEFT, padx=6
        )
        clear_date_entry(self.report_start_entry)
        clear_date_entry(self.report_end_entry)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=(0, 6))
        ttk.Checkbutton(row2, text="Tarih filtresi kullan", variable=self.report_use_dates).pack(
            side=tk.LEFT, padx=6
        )

        viewer = ttk.LabelFrame(self.tab_reports_body, text="Rapor Goruntule", style="Section.TLabelframe")
        viewer.pack(fill=tk.X, padx=6, pady=6)
        ttk.Button(viewer, text="XLSX Sec ve Goruntule", command=self.pick_and_preview_report).pack(
            side=tk.LEFT, padx=6, pady=6
        )

        archive = ttk.LabelFrame(self.tab_reports_body, text="Rapor Arsivi", style="Section.TLabelframe")
        archive.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.report_tree = ttk.Treeview(
            archive,
            columns=("id", "file", "created", "employee", "range"),
            show="headings",
            height=8,
        )
        self.report_tree.heading("id", text="ID")
        self.report_tree.heading("file", text="Dosya")
        self.report_tree.heading("created", text="Tarih")
        self.report_tree.heading("employee", text="Calisan")
        self.report_tree.heading("range", text="Aralik")
        self.report_tree.column("id", width=60, anchor=tk.CENTER)
        self.report_tree.column("file", width=360)
        self.report_tree.column("created", width=140)
        self.report_tree.column("employee", width=180)
        self.report_tree.column("range", width=180)
        report_xscroll = ttk.Scrollbar(archive, orient=tk.HORIZONTAL, command=self.report_tree.xview)
        report_yscroll = ttk.Scrollbar(archive, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(xscrollcommand=report_xscroll.set, yscrollcommand=report_yscroll.set)
        archive.columnconfigure(0, weight=1)
        archive.rowconfigure(0, weight=1)
        self.report_tree.grid(row=0, column=0, sticky="nsew")
        report_yscroll.grid(row=0, column=1, sticky="ns")
        report_xscroll.grid(row=1, column=0, sticky="ew")

        archive.rowconfigure(0, weight=1)
        archive.columnconfigure(0, weight=1)

        btn_row = ttk.Frame(archive)
        btn_row.grid(row=2, column=0, sticky="ew", pady=6)
        ttk.Button(btn_row, text="Arsivi Yenile", command=self.refresh_report_archive).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Seciliyi Goruntule", command=self.preview_selected_report).pack(
            side=tk.LEFT, padx=6
        )

        note = ttk.Label(
            frame,
            text=f"Tarih formatlari: {DATE_FMT} / Saat formatlari: {TIME_FMT}",
            foreground="#444444",
        )
        note.pack(anchor=tk.W, padx=6, pady=(0, 6))

    def export_report(self):
        employee_name = self.report_employee_var.get().strip()
        employee_id = None
        if employee_name and employee_name != "Tum Calisanlar":
            employee_id = self.employee_map.get(employee_name)
        start_date = self.report_start_var.get().strip() or None
        end_date = self.report_end_var.get().strip() or None
        try:
            if self.report_use_dates.get():
                if start_date:
                    start_date = normalize_date(start_date)
                if end_date:
                    end_date = normalize_date(end_date)
            else:
                start_date = None
                end_date = None
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return

        records = db.list_timesheets(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            region=self._view_region(),
        )
        if not records:
            messagebox.showinfo("Bilgi", "Rapor icin veri bulunamadi.")
            return

        if employee_name and employee_name != "Tum Calisanlar":
            employee_slug = employee_name.replace(" ", "_")
        else:
            employee_slug = "tum_calisanlar"
        filename = f"puantaj_raporu_{employee_slug}_{start_date or 'tum'}_{end_date or 'tum'}.xlsx"
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=filename,
        )
        if not output_path:
            return

        date_text = f"Tarih Araligi: {start_date or '-'} - {end_date or '-'}"
        try:
            report.export_report(output_path, records, db.get_all_settings(), date_text)
        except ValueError as exc:
            messagebox.showerror("Hata", str(exc))
            return
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.add_report_log(output_path, created_at, employee_name, start_date, end_date)
        self.refresh_report_archive()
        messagebox.showinfo("Basarili", f"Rapor kaydedildi: {output_path}")

    def refresh_report_archive(self):
        if not hasattr(self, "report_tree"):
            return
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for rep in db.list_report_logs():
            rep_id, file_path, created_at, employee, start_date, end_date = rep
            range_text = f"{start_date or '-'} - {end_date or '-'}"
            values = (rep_id, file_path, created_at, employee or "Tum Calisanlar", range_text)
            self.report_tree.insert("", tk.END, values=values)

    def pick_and_preview_report(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        self.preview_report(path)

    def preview_selected_report(self):
        selected = self.report_tree.selection()
        if not selected:
            messagebox.showwarning("Uyari", "Once rapor secin.")
            return
        values = self.report_tree.item(selected[0], "values")
        path = values[1]
        self.preview_report(path)

    def preview_report(self, path):
        if not path or not os.path.isfile(path):
            messagebox.showwarning("Uyari", "Dosya bulunamadi.")
            return
        try:
            wb = load_workbook(path, data_only=True)
            ws = wb.active
        except Exception as exc:
            messagebox.showerror("Hata", f"Dosya acilamadi: {exc}")
            return

        preview = tk.Toplevel(self)
        preview.title(f"Rapor Goruntule - {os.path.basename(path)}")
        preview.geometry("1100x700")

        frame = ttk.Frame(preview)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        max_cols = min(ws.max_column, 25)
        max_rows = min(ws.max_row, 200)
        headers = [ws.cell(row=1, column=c).value or f"C{c}" for c in range(1, max_cols + 1)]
        tree = ttk.Treeview(frame, columns=list(range(max_cols)), show="headings")
        for idx, header in enumerate(headers):
            tree.heading(idx, text=str(header))
            tree.column(idx, width=120)
        tree.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=xscroll.set)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        for r in range(2, max_rows + 1):
            row_vals = []
            for c in range(1, max_cols + 1):
                val = ws.cell(row=r, column=c).value
                row_vals.append("" if val is None else val)
            tree.insert("", tk.END, values=row_vals)

    def refresh_admin_summary(self):
        if not hasattr(self, "admin_tree"):
            return
        for item in self.admin_tree.get_children():
            self.admin_tree.delete(item)
        if hasattr(self, "admin_alert_tree"):
            for item in self.admin_alert_tree.get_children():
                self.admin_alert_tree.delete(item)
        if hasattr(self, "admin_anomaly_tree"):
            for item in self.admin_anomaly_tree.get_children():
                self.admin_anomaly_tree.delete(item)

        employee_name = self.admin_employee_var.get().strip()
        employee_id = None
        if employee_name and employee_name != "Tum Calisanlar":
            employee_id = self.employee_map.get(employee_name)
        department_filter = self.admin_department_var.get().strip()
        title_filter = self.admin_title_var.get().strip()
        search_text = self.admin_search_var.get().strip().lower()
        start_date = self.admin_start_var.get().strip() or None
        end_date = self.admin_end_var.get().strip() or None
        try:
            if start_date:
                start_date = normalize_date(start_date)
            if end_date:
                end_date = normalize_date(end_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return

        records = db.list_timesheets(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            region=self._view_region(),
        )
        totals = {}
        daily_overtime = {}
        dept_overtime = {}
        alerts = []
        work_days = {}
        for _ts_id, _emp_id, name, work_date, start_time, end_time, break_minutes, is_special, _notes in records:
            details = self.employee_details.get(name, {})
            department = details.get("department", "")
            title = details.get("title", "")
            if department_filter and department_filter != "Tum Departmanlar" and department != department_filter:
                continue
            if title_filter and title_filter != "Tum Unvanlar" and title != title_filter:
                continue
            if search_text:
                hay = " ".join([name, department, title, str(_notes or "")]).lower()
                if search_text not in hay:
                    continue

            (
                worked,
                _scheduled,
                overtime,
                night_hours,
                overnight_hours,
                spec_norm,
                spec_ot,
                spec_night,
            ) = calc.calc_day_hours(
                work_date,
                start_time,
                end_time,
                break_minutes,
                self.settings,
                is_special,
            )
            if name not in totals:
                totals[name] = {
                    "worked": 0.0,
                    "overtime": 0.0,
                    "night": 0.0,
                    "overnight": 0.0,
                    "special": 0.0,
                }
            totals[name]["worked"] += worked
            totals[name]["overtime"] += overtime
            totals[name]["night"] += night_hours
            totals[name]["overnight"] += overnight_hours
            totals[name]["special"] += spec_norm + spec_ot + spec_night

            daily_overtime[work_date] = daily_overtime.get(work_date, 0.0) + overtime
            dept_key = department or "Bilinmeyen"
            dept_overtime[dept_key] = dept_overtime.get(dept_key, 0.0) + overtime

            try:
                gross_hours = calc.hours_between(calc.parse_time(start_time), calc.parse_time(end_time))
            except Exception:
                gross_hours = 0.0
            if gross_hours >= 12:
                alerts.append((work_date, name, "Uzun Mesai", f"{gross_hours:.1f}s"))
            if overnight_hours > 0:
                alerts.append((work_date, name, "Geceye Tasan", f"{overnight_hours:.1f}s"))
            if is_special:
                alerts.append((work_date, name, "Ozel Gun", f"{worked:.1f}s"))

            work_days.setdefault(name, set()).add(work_date)

        total_worked = sum(v["worked"] for v in totals.values())
        total_overtime = sum(v["overtime"] for v in totals.values())
        total_night = sum(v["night"] for v in totals.values())
        total_overnight = sum(v["overnight"] for v in totals.values())
        total_special = sum(v["special"] for v in totals.values())

        self.admin_stats["total_records"].set(str(len(records)))
        self.admin_stats["total_employees"].set(str(len(totals)))
        self.admin_stats["total_worked"].set(f"{total_worked:.2f}")
        self.admin_stats["total_overtime"].set(f"{total_overtime:.2f}")
        self.admin_stats["total_night"].set(f"{total_night:.2f}")
        self.admin_stats["total_overnight"].set(f"{total_overnight:.2f}")
        self.admin_stats["total_special"].set(f"{total_special:.2f}")
        avg_ot = (total_overtime / len(totals)) if totals else 0.0
        self.admin_stats["avg_overtime"].set(f"{avg_ot:.2f}")
        max_daily = max(daily_overtime.values()) if daily_overtime else 0.0
        self.admin_stats["max_daily"].set(f"{max_daily:.2f}")

        for name, data in sorted(totals.items(), key=lambda x: x[0]):
            self.admin_tree.insert(
                "",
                tk.END,
                values=(
                    name,
                    round(data["worked"], 2),
                    round(data["overtime"], 2),
                    round(data["night"], 2),
                    round(data["overnight"], 2),
                    round(data["special"], 2),
                ),
            )

        if hasattr(self, "admin_alert_tree"):
            for work_date, name, issue, value in alerts[:200]:
                self.admin_alert_tree.insert("", tk.END, values=(work_date, name, issue, value))

        if hasattr(self, "admin_anomaly_tree"):
            anomalies = self._build_consecutive_day_anomalies(work_days)
            for name, period, issue in anomalies:
                self.admin_anomaly_tree.insert("", tk.END, values=(name, period, issue))

    def _build_consecutive_day_anomalies(self, work_days):
        anomalies = []
        for name, dates in work_days.items():
            try:
                sorted_dates = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in dates)
            except Exception:
                continue
            streak = 1
            start = sorted_dates[0] if sorted_dates else None
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                    streak += 1
                else:
                    if streak >= 6 and start:
                        anomalies.append((name, f"{start} - {sorted_dates[i-1]}", f"{streak} gun ust uste"))
                    streak = 1
                    start = sorted_dates[i]
            if streak >= 6 and start:
                anomalies.append((name, f"{start} - {sorted_dates[-1]}", f"{streak} gun ust uste"))
        return anomalies


    def package_monthly_reports(self):
        month_text = self.admin_month_var.get().strip()
        try:
            parse_month(month_text)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        logs = db.list_report_logs()
        files = [r[1] for r in logs if r[2].startswith(month_text)]
        files = [f for f in files if os.path.isfile(f)]
        if not files:
            messagebox.showinfo("Bilgi", "Secilen ay icin rapor bulunamadi.")
            return
        output_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP", "*.zip")],
            initialfile=f"raporlar_{month_text}.zip",
        )
        if not output_path:
            return
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    zf.write(file_path, arcname=os.path.basename(file_path))
        except Exception as exc:
            messagebox.showerror("Hata", f"Zip olusturulamadi: {exc}")
            return
        messagebox.showinfo("Basarili", f"Zip kaydedildi: {output_path}")

    def refresh_vehicles(self):
        if not hasattr(self, "vehicle_tree"):
            return
        for item in self.vehicle_tree.get_children():
            self.vehicle_tree.delete(item)
        self.vehicle_map = {}
        for vehicle in db.list_vehicles(region=self._view_region()):
            (
                vehicle_id,
                plate,
                brand,
                model,
                year,
                km,
                inspection_date,
                insurance_date,
                maintenance_date,
                oil_change_date,
                oil_change_km,
                oil_interval_km,
                _notes,
            ) = vehicle
            oil_status = "-"
            interval_km = oil_interval_km or DEFAULT_OIL_INTERVAL_KM
            if interval_km and oil_change_km is not None and km is not None:
                remaining = interval_km - (km - oil_change_km)
                oil_status = "Geldi" if remaining <= 0 else f"{remaining} km"
            self.vehicle_tree.insert(
                "",
                tk.END,
                values=(
                    vehicle_id,
                    plate,
                    brand,
                    model,
                    year,
                    km,
                    inspection_date,
                    insurance_date,
                    maintenance_date,
                    oil_status,
                ),
            )
            self.vehicle_map[plate] = vehicle_id
        if hasattr(self, "inspect_vehicle_combo"):
            self.inspect_vehicle_combo["values"] = sorted(self.vehicle_map.keys())
        if hasattr(self, "fault_vehicle_combo"):
            self.fault_vehicle_combo["values"] = sorted(self.vehicle_map.keys())
        if hasattr(self, "service_vehicle_combo"):
            self.service_vehicle_combo["values"] = sorted(self.vehicle_map.keys())

    def refresh_drivers(self):
        if not hasattr(self, "driver_tree"):
            return
        for item in self.driver_tree.get_children():
            self.driver_tree.delete(item)
        self.driver_map = {}
        for driver in db.list_drivers(region=self._view_region()):
            driver_id, name, license_class, license_expiry, phone, _notes = driver
            self.driver_tree.insert("", tk.END, values=(driver_id, name, license_class, license_expiry, phone))
            self.driver_map[name] = driver_id
        if hasattr(self, "inspect_driver_combo"):
            self.inspect_driver_combo["values"] = sorted(self.driver_map.keys())

    def refresh_faults(self):
        if hasattr(self, "fault_tree"):
            for item in self.fault_tree.get_children():
                self.fault_tree.delete(item)
        self.fault_map = {}
        self.fault_display_by_id = {}
        for fault in db.list_vehicle_faults(region=self._view_region()):
            fault_id, vehicle_id, plate, title, desc, opened_date, closed_date, status = fault
            if hasattr(self, "fault_tree"):
                self.fault_tree.insert(
                    "",
                    tk.END,
                    values=(fault_id, plate, title, status, opened_date or "", closed_date or ""),
                )
            display = f"{plate} - {title} (#{fault_id})"
            self.fault_map[display] = fault_id
            self.fault_display_by_id[fault_id] = display
        if hasattr(self, "inspect_fault_combo"):
            values = [""] + list(self.fault_map.keys())
            self.inspect_fault_combo["values"] = values
        if hasattr(self, "service_fault_combo"):
            values = [""] + list(self.fault_map.keys())
            self.service_fault_combo["values"] = values

    def refresh_service_visits(self):
        if not hasattr(self, "service_tree"):
            return
        for item in self.service_tree.get_children():
            self.service_tree.delete(item)
        self.service_visit_map = {}
        for visit in db.list_vehicle_service_visits(region=self._view_region()):
            (
                visit_id,
                _vehicle_id,
                plate,
                _fault_id,
                fault_title,
                start_date,
                end_date,
                reason,
                cost,
                _notes,
            ) = visit
            self.service_tree.insert(
                "",
                tk.END,
                values=(
                    visit_id,
                    plate,
                    fault_title or "",
                    start_date,
                    end_date or ("Sanayide" if end_date is None or end_date == "" else ""),
                    f"{cost:.2f}" if cost is not None else "",
                    reason or "",
                ),
            )
            self.service_visit_map[visit_id] = visit

    def clear_fault_form(self):
        self.fault_id_var.set("")
        self.fault_vehicle_var.set("")
        self.fault_title_var.set("")
        self.fault_desc_var.set("")
        self.fault_open_var.set("")
        self.fault_close_var.set("")
        self.fault_status_var.set("Acik")
        if hasattr(self, "fault_open_entry"):
            clear_date_entry(self.fault_open_entry)
        if hasattr(self, "fault_close_entry"):
            clear_date_entry(self.fault_close_entry)

    def add_or_update_fault(self):
        plate = self.fault_vehicle_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        title = self.fault_title_var.get().strip()
        if not title:
            messagebox.showwarning("Uyari", "Baslik zorunlu.")
            return
        opened_date = self.fault_open_var.get().strip()
        closed_date = self.fault_close_var.get().strip()
        if opened_date:
            try:
                opened_date = normalize_date(opened_date)
            except ValueError as exc:
                messagebox.showwarning("Uyari", str(exc))
                return
        if closed_date:
            try:
                closed_date = normalize_date(closed_date)
            except ValueError as exc:
                messagebox.showwarning("Uyari", str(exc))
                return
        status = self.fault_status_var.get().strip() or "Acik"
        desc = self.fault_desc_var.get().strip()
        fault_id = parse_int(self.fault_id_var.get())
        if fault_id:
            db.update_vehicle_fault(
                fault_id,
                vehicle_id,
                title,
                desc,
                opened_date,
                closed_date,
                status,
                self._entry_region(),
            )
        else:
            db.add_vehicle_fault(
                vehicle_id,
                title,
                desc,
                opened_date,
                closed_date,
                status,
                self._entry_region(),
            )
        self.refresh_faults()
        self.refresh_vehicle_dashboard()
        self.clear_fault_form()
        messagebox.showinfo("Basarili", "Ariza kaydi kaydedildi.")
        self.trigger_sync("fault")

    def delete_fault(self):
        fault_id = parse_int(self.fault_id_var.get())
        if not fault_id:
            selected = self.fault_tree.selection() if hasattr(self, "fault_tree") else None
            if selected:
                values = self.fault_tree.item(selected[0], "values")
                fault_id = parse_int(values[0])
        if not fault_id:
            messagebox.showwarning("Uyari", "Silinecek ariza secin.")
            return
        if not messagebox.askyesno("Onay", "Ariza kaydi silinsin mi?"):
            return
        db.delete_vehicle_fault(fault_id)
        self.refresh_faults()
        self.refresh_vehicle_dashboard()
        self.clear_fault_form()
        self.trigger_sync("fault_delete")

    def on_fault_select(self, _event=None):
        selected = self.fault_tree.selection()
        if not selected:
            return
        values = self.fault_tree.item(selected[0], "values")
        fault_id = parse_int(values[0])
        fault = db.get_vehicle_fault(fault_id)
        if not fault:
            return
        (
            _fid,
            vehicle_id,
            title,
            desc,
            opened_date,
            closed_date,
            status,
        ) = fault
        plate = None
        for plate_name, vid in self.vehicle_map.items():
            if vid == vehicle_id:
                plate = plate_name
                break
        if plate:
            self.fault_vehicle_var.set(plate)
        self.fault_id_var.set(fault_id)
        self.fault_title_var.set(title or "")
        self.fault_desc_var.set(desc or "")
        self.fault_open_var.set(opened_date or "")
        self.fault_close_var.set(closed_date or "")
        self.fault_status_var.set(status or "Acik")

    def clear_service_visit_form(self):
        self.service_id_var.set("")
        self.service_vehicle_var.set("")
        self.service_fault_var.set("")
        self.service_start_var.set("")
        self.service_end_var.set("")
        self.service_reason_var.set("")
        self.service_cost_var.set("")
        self.service_notes_var.set("")
        self.service_in_shop_var.set(False)
        self._toggle_service_end_date()
        if hasattr(self, "service_start_entry"):
            clear_date_entry(self.service_start_entry)
        if hasattr(self, "service_end_entry"):
            clear_date_entry(self.service_end_entry)

    def add_or_update_service_visit(self):
        plate = self.service_vehicle_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        fault_display = self.service_fault_var.get().strip()
        fault_id = self.fault_map.get(fault_display) if fault_display else None
        start_date = self.service_start_var.get().strip()
        if not start_date:
            messagebox.showwarning("Uyari", "Gidis tarihi zorunlu.")
            return
        try:
            start_date = normalize_date(start_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        end_date = self.service_end_var.get().strip()
        if self.service_in_shop_var.get():
            end_date = ""
        elif end_date:
            try:
                end_date = normalize_date(end_date)
            except ValueError as exc:
                messagebox.showwarning("Uyari", str(exc))
                return
        reason = self.service_reason_var.get().strip()
        notes = self.service_notes_var.get().strip()
        cost = self.service_cost_var.get().strip()
        cost_val = None if cost == "" else parse_float(cost, 0.0)
        visit_id = parse_int(self.service_id_var.get())
        if visit_id:
            db.update_vehicle_service_visit(
                visit_id,
                vehicle_id,
                fault_id,
                start_date,
                end_date,
                reason,
                cost_val,
                notes,
                self._entry_region(),
            )
        else:
            db.add_vehicle_service_visit(
                vehicle_id,
                fault_id,
                start_date,
                end_date,
                reason,
                cost_val,
                notes,
                self._entry_region(),
            )
        self.refresh_service_visits()
        self.refresh_vehicle_dashboard()
        self.clear_service_visit_form()
        messagebox.showinfo("Basarili", "Sanayi kaydi kaydedildi.")
        self.trigger_sync("service_visit")

    def delete_service_visit(self):
        visit_id = parse_int(self.service_id_var.get())
        if not visit_id:
            selected = self.service_tree.selection() if hasattr(self, "service_tree") else None
            if selected:
                values = self.service_tree.item(selected[0], "values")
                visit_id = parse_int(values[0])
        if not visit_id:
            messagebox.showwarning("Uyari", "Silinecek kaydi secin.")
            return
        if not messagebox.askyesno("Onay", "Sanayi kaydi silinsin mi?"):
            return
        db.delete_vehicle_service_visit(visit_id)
        self.refresh_service_visits()
        self.refresh_vehicle_dashboard()
        self.clear_service_visit_form()
        self.trigger_sync("service_visit_delete")

    def on_service_visit_select(self, _event=None):
        selected = self.service_tree.selection()
        if not selected:
            return
        values = self.service_tree.item(selected[0], "values")
        visit_id = parse_int(values[0])
        visit = db.get_vehicle_service_visit(visit_id)
        if not visit:
            return
        (
            _vid,
            vehicle_id,
            fault_id,
            start_date,
            end_date,
            reason,
            cost,
            notes,
        ) = visit
        plate = None
        for plate_name, vid in self.vehicle_map.items():
            if vid == vehicle_id:
                plate = plate_name
                break
        if plate:
            self.service_vehicle_var.set(plate)
        fault_display = ""
        if fault_id:
            for display, fid in self.fault_map.items():
                if fid == fault_id:
                    fault_display = display
                    break
        self.service_fault_var.set(fault_display)
        self.service_id_var.set(visit_id)
        self.service_start_var.set(start_date or "")
        self.service_end_var.set(end_date or "")
        self.service_in_shop_var.set(False if end_date else True)
        self._toggle_service_end_date()
        self.service_reason_var.set(reason or "")
        self.service_cost_var.set("" if cost is None else f"{cost:.2f}")
        self.service_notes_var.set(notes or "")

    def _toggle_service_end_date(self):
        state = "disabled" if self.service_in_shop_var.get() else "normal"
        if hasattr(self, "service_end_entry"):
            try:
                self.service_end_entry.configure(state=state)
            except tk.TclError:
                pass

    def refresh_vehicle_dashboard(self):
        if not hasattr(self, "vehicle_status_tree"):
            return
        for item in self.vehicle_status_tree.get_children():
            self.vehicle_status_tree.delete(item)
        for item in self.vehicle_alert_tree.get_children():
            self.vehicle_alert_tree.delete(item)
        for item in self.driver_alert_tree.get_children():
            self.driver_alert_tree.delete(item)

        vehicles = db.list_vehicles(region=self._view_region())
        drivers = db.list_drivers(region=self._view_region())
        driver_by_id = {row[0]: row for row in drivers}
        driver_latest = {}

        oil_due = 0
        insp_due = 0
        ins_due = 0
        maint_due = 0
        lic_due = 0

        for vehicle in vehicles:
            (
                _vid,
                plate,
                brand,
                model,
                year,
                km,
                inspection_date,
                insurance_date,
                maintenance_date,
                oil_change_date,
                oil_change_km,
                oil_interval_km,
                _notes,
            ) = vehicle
            oil_status = "-"
            oil_flag = None
            interval_km = oil_interval_km or DEFAULT_OIL_INTERVAL_KM
            if interval_km and oil_change_km is not None and km is not None:
                remaining = interval_km - (km - oil_change_km)
                oil_status = "Geldi" if remaining <= 0 else f"{remaining} km"
                if remaining <= 0:
                    oil_due += 1
                    oil_flag = "oil_due"
                    self.vehicle_alert_tree.insert("", tk.END, values=(plate, "Yag Degisimi", "Geldi"))
                elif remaining <= DEFAULT_OIL_SOON_KM:
                    oil_flag = "oil_soon"

            insp_days = days_until(inspection_date)
            if insp_days is not None and insp_days <= 30:
                insp_due += 1
                detail = f"{inspection_date} ({insp_days} gun)"
                if insp_days < 0:
                    detail = f"{inspection_date} ({abs(insp_days)} gun gecikme)"
                self.vehicle_alert_tree.insert("", tk.END, values=(plate, "Muayene", detail))

            ins_days = days_until(insurance_date)
            if ins_days is not None and ins_days <= 30:
                ins_due += 1
                detail = f"{insurance_date} ({ins_days} gun)"
                if ins_days < 0:
                    detail = f"{insurance_date} ({abs(ins_days)} gun gecikme)"
                self.vehicle_alert_tree.insert("", tk.END, values=(plate, "Sigorta", detail))

            maint_days = days_until(maintenance_date)
            if maint_days is not None and maint_days <= 30:
                maint_due += 1
                detail = f"{maintenance_date} ({maint_days} gun)"
                if maint_days < 0:
                    detail = f"{maintenance_date} ({abs(maint_days)} gun gecikme)"
                self.vehicle_alert_tree.insert("", tk.END, values=(plate, "Bakim", detail))

            inspections = db.list_vehicle_inspections(vehicle_id=_vid, region=self._view_region())
            last_check = "-"
            last_driver = "-"
            if inspections:
                last_inspection = inspections[0]
                last_check = last_inspection[5]
                last_driver = last_inspection[4] or "-"
                driver_id = last_inspection[3]
                if driver_id:
                    current = driver_latest.get(driver_id)
                    if not current or last_inspection[5] > current[5]:
                        driver_latest[driver_id] = last_inspection

            if len(inspections) >= 2:
                current_inspection = inspections[0]
                previous_inspection = inspections[1]
                current_results = {
                    row[0]: normalize_vehicle_status(row[1])
                    for row in db.list_vehicle_inspection_results(current_inspection[0])
                }
                prev_results = {
                    row[0]: normalize_vehicle_status(row[1])
                    for row in db.list_vehicle_inspection_results(previous_inspection[0])
                }
                for item_key, label in VEHICLE_CHECKLIST:
                    if (
                        current_results.get(item_key) == "Olumsuz"
                        and prev_results.get(item_key) == "Olumsuz"
                    ):
                        self.vehicle_alert_tree.insert(
                            "",
                            tk.END,
                            values=(plate, "Tekrar Eden Sorun", f"{label} (2 hafta)"),
                        )

            self.vehicle_status_tree.insert(
                "",
                tk.END,
                values=(
                    plate,
                    km or "-",
                    oil_status,
                    inspection_date or "-",
                    insurance_date or "-",
                    maintenance_date or "-",
                    last_check,
                    last_driver,
                ),
                tags=(oil_flag,) if oil_flag else (),
            )

        for driver in drivers:
            _did, name, _cls, license_expiry, _phone, _notes = driver
            days = days_until(license_expiry)
            if days is not None and days <= 30:
                lic_due += 1
                detail = f"{license_expiry} ({days} gun)"
                if days < 0:
                    detail = f"{license_expiry} ({abs(days)} gun gecikme)"
                self.driver_alert_tree.insert("", tk.END, values=(name, "Ehliyet", detail))

        faults = db.list_vehicle_faults(region=self._view_region())
        now = datetime.now().date()
        faults_by_plate = {}
        for fault in faults:
            _fid, _vid, plate, title, _desc, opened_date, _closed_date, status = fault
            faults_by_plate.setdefault(plate, []).append(fault)
            if status == "Acik":
                self.vehicle_alert_tree.insert("", tk.END, values=(plate, "Acik Ariza", title))

        for plate, items in faults_by_plate.items():
            title_counts = {}
            for fault in items:
                opened_date = fault[5]
                if not opened_date:
                    continue
                try:
                    opened_dt = datetime.strptime(opened_date, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if (now - opened_dt).days <= 30:
                    title_counts[fault[3]] = title_counts.get(fault[3], 0) + 1
            for title, count in title_counts.items():
                if count >= 2:
                    self.vehicle_alert_tree.insert(
                        "",
                        tk.END,
                        values=(plate, "Tekrar Ariza (30 gun)", f"{title} x{count}"),
                    )

        fault_counts = {}
        for fault in faults:
            plate = fault[2]
            fault_counts[plate] = fault_counts.get(plate, 0) + 1
        top_faults = sorted(fault_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for plate, count in top_faults:
            self.vehicle_alert_tree.insert("", tk.END, values=(plate, "En Cok Ariza", f"{count} kayit"))

        for driver_id, inspection in driver_latest.items():
            driver = driver_by_id.get(driver_id)
            if not driver:
                continue
            name = driver[1]
            plate = inspection[2]
            results = db.list_vehicle_inspection_results(inspection[0])
            bad_items = []
            for item_key, label in VEHICLE_CHECKLIST:
                for res_key, status, _note in results:
                    if res_key == item_key and normalize_vehicle_status(status) == "Olumsuz":
                        bad_items.append(label)
                        break
            if bad_items:
                detail = f"{plate} - {len(bad_items)} olumsuz"
                self.driver_alert_tree.insert("", tk.END, values=(name, "Son Kontrol Sorun", detail))

        self.dashboard_stats["vehicles"].set(str(len(vehicles)))
        self.dashboard_stats["drivers"].set(str(len(drivers)))
        self.dashboard_stats["oil_due"].set(str(oil_due))
        self.dashboard_stats["inspection_due"].set(str(insp_due))
        self.dashboard_stats["insurance_due"].set(str(ins_due))
        self.dashboard_stats["maintenance_due"].set(str(maint_due))
        self.dashboard_stats["license_due"].set(str(lic_due))

    def clear_vehicle_form(self):
        self.vehicle_id_var.set("")
        self.vehicle_plate_var.set("")
        self.vehicle_brand_var.set("")
        self.vehicle_model_var.set("")
        self.vehicle_year_var.set("")
        self.vehicle_km_var.set("")
        self.vehicle_inspection_var.set("")
        self.vehicle_insurance_var.set("")
        self.vehicle_maintenance_var.set("")
        self.vehicle_oil_var.set("")
        self.vehicle_oil_km_var.set("")
        self.vehicle_oil_interval_var.set(str(DEFAULT_OIL_INTERVAL_KM))
        self.vehicle_notes_var.set("")
        self.vehicle_original_plate = None
        clear_date_entry(self.vehicle_insp_entry)
        clear_date_entry(self.vehicle_ins_entry)
        clear_date_entry(self.vehicle_maint_entry)
        clear_date_entry(self.vehicle_oil_entry)

    def on_vehicle_select(self, _event=None):
        selected = self.vehicle_tree.selection()
        if not selected:
            return
        values = self.vehicle_tree.item(selected[0], "values")
        vehicle_id = parse_int(values[0])
        row = db.get_vehicle(vehicle_id)
        if not row:
            return
        (
            _vid,
            plate,
            brand,
            model,
            year,
            km,
            inspection_date,
            insurance_date,
            maintenance_date,
            oil_change_date,
            oil_change_km,
            oil_interval_km,
            _notes,
        ) = row
        self.vehicle_id_var.set(vehicle_id)
        self.vehicle_plate_var.set(plate)
        self.vehicle_original_plate = plate
        self.vehicle_brand_var.set(brand)
        self.vehicle_model_var.set(model)
        self.vehicle_year_var.set(year)
        self.vehicle_km_var.set(km or "")
        self.vehicle_inspection_var.set(inspection_date or "")
        self.vehicle_insurance_var.set(insurance_date or "")
        self.vehicle_maintenance_var.set(maintenance_date or "")
        self.vehicle_oil_var.set(oil_change_date or "")
        self.vehicle_oil_km_var.set(oil_change_km or "")
        self.vehicle_oil_interval_var.set(oil_interval_km or str(DEFAULT_OIL_INTERVAL_KM))

    def add_or_update_vehicle(self):
        plate = self.vehicle_plate_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Plaka zorunlu.")
            return
        brand = self.vehicle_brand_var.get().strip()
        model = self.vehicle_model_var.get().strip()
        year = self.vehicle_year_var.get().strip()
        km = parse_int(self.vehicle_km_var.get(), 0)
        inspection_date = self.vehicle_inspection_var.get().strip()
        insurance_date = self.vehicle_insurance_var.get().strip()
        maintenance_date = self.vehicle_maintenance_var.get().strip()
        oil_change_date = self.vehicle_oil_var.get().strip()
        oil_change_km = parse_int(self.vehicle_oil_km_var.get(), 0)
        oil_interval_km = parse_int(self.vehicle_oil_interval_var.get(), 0)
        notes = self.vehicle_notes_var.get().strip()
        try:
            inspection_date = normalize_date(inspection_date) if inspection_date else ""
            insurance_date = normalize_date(insurance_date) if insurance_date else ""
            maintenance_date = normalize_date(maintenance_date) if maintenance_date else ""
            oil_change_date = normalize_date(oil_change_date) if oil_change_date else ""
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return

        vehicle_id = self.vehicle_id_var.get().strip()
        if vehicle_id and self.vehicle_original_plate and plate != self.vehicle_original_plate:
            add_new = messagebox.askyesno(
                "Onay",
                "Plaka degisti. Yeni arac olarak eklensin mi?\n"
                "Evet: yeni kayit, Hayir: mevcut araci guncelle.",
            )
            if add_new:
                vehicle_id = ""
        try:
            if vehicle_id:
                db.update_vehicle(
                    parse_int(vehicle_id),
                    plate,
                    brand,
                    model,
                    year,
                    km,
                    inspection_date,
                    insurance_date,
                    maintenance_date,
                    oil_change_date,
                    oil_change_km,
                    oil_interval_km,
                    notes,
                    self._entry_region(),
                )
            else:
                db.add_vehicle(
                    plate,
                    brand,
                    model,
                    year,
                    km,
                    inspection_date,
                    insurance_date,
                    maintenance_date,
                    oil_change_date,
                    oil_change_km,
                    oil_interval_km,
                    notes,
                    self._entry_region(),
                )
        except Exception:
            messagebox.showwarning("Uyari", "Arac kaydi eklenemedi. Plaka zaten var olabilir.")
            return
        self.refresh_vehicles()
        self.clear_vehicle_form()
        self.trigger_sync("vehicle")

    def delete_vehicle(self):
        vehicle_id = self.vehicle_id_var.get().strip()
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Silmek icin arac secin.")
            return
        if messagebox.askyesno("Onay", "Araci silmek istiyor musunuz?"):
            db.delete_vehicle(parse_int(vehicle_id))
            self.refresh_vehicles()
            self.clear_vehicle_form()
            self.trigger_sync("vehicle_delete")

    def clear_driver_form(self):
        self.driver_id_var.set("")
        self.driver_name_var.set("")
        self.driver_license_var.set("")
        self.driver_license_exp_var.set("")
        self.driver_phone_var.set("")
        self.driver_notes_var.set("")
        clear_date_entry(self.driver_exp_entry)

    def on_driver_select(self, _event=None):
        selected = self.driver_tree.selection()
        if not selected:
            return
        values = self.driver_tree.item(selected[0], "values")
        self.driver_id_var.set(values[0])
        self.driver_name_var.set(values[1])
        self.driver_license_var.set(values[2])
        self.driver_license_exp_var.set(values[3] or "")
        self.driver_phone_var.set(values[4])

    def add_or_update_driver(self):
        name = self.driver_name_var.get().strip()
        if not name:
            messagebox.showwarning("Uyari", "Ad Soyad zorunlu.")
            return
        license_class = self.driver_license_var.get().strip()
        license_expiry = self.driver_license_exp_var.get().strip()
        phone = self.driver_phone_var.get().strip()
        notes = self.driver_notes_var.get().strip()
        try:
            license_expiry = normalize_date(license_expiry) if license_expiry else ""
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        driver_id = self.driver_id_var.get().strip()
        if driver_id:
            db.update_driver(
                parse_int(driver_id),
                name,
                license_class,
                license_expiry,
                phone,
                notes,
                self._entry_region(),
            )
        else:
            db.add_driver(name, license_class, license_expiry, phone, notes, self._entry_region())
        self.refresh_drivers()
        self.clear_driver_form()
        self.trigger_sync("driver")

    def delete_driver(self):
        driver_id = self.driver_id_var.get().strip()
        if not driver_id:
            messagebox.showwarning("Uyari", "Silmek icin surucu secin.")
            return
        if messagebox.askyesno("Onay", "Surucuyu silmek istiyor musunuz?"):
            db.delete_driver(parse_int(driver_id))
            self.refresh_drivers()
            self.clear_driver_form()
            self.trigger_sync("driver_delete")

    def save_vehicle_inspection(self):
        plate = self.inspect_vehicle_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        driver_name = self.inspect_driver_var.get().strip()
        driver_id = self.driver_map.get(driver_name) if driver_name else None
        inspect_date = self.inspect_date_var.get().strip()
        if not inspect_date:
            messagebox.showwarning("Uyari", "Tarih zorunlu.")
            return
        inspect_km = parse_int(self.inspect_km_var.get(), 0)
        try:
            inspect_date = normalize_date(inspect_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        week_start = week_start_from_date(inspect_date)
        notes = self.inspect_notes_var.get().strip()
        fault_display = self.inspect_fault_var.get().strip()
        fault_id = self.fault_map.get(fault_display) if fault_display else None
        fault_status = self.inspect_fault_status_var.get().strip() if fault_id else None
        service_visit = 1 if self.inspect_service_var.get() else 0
        if service_visit and not fault_id:
            messagebox.showwarning("Uyari", "Sanayi icin ariza secin.")
            return
        inspection_id = db.add_vehicle_inspection(
            vehicle_id,
            driver_id,
            inspect_date,
            week_start,
            inspect_km,
            notes,
            fault_id=fault_id,
            fault_status=fault_status,
            service_visit=service_visit,
        )
        for item_key, _label in VEHICLE_CHECKLIST:
            status = self.inspect_item_vars[item_key].get()
            note = self.inspect_note_vars[item_key].get().strip()
            db.add_vehicle_inspection_result(inspection_id, item_key, status, note)
        if inspect_km:
            current = db.get_vehicle(vehicle_id)
            if current:
                (
                    _vid,
                    plate,
                    brand,
                    model,
                    year,
                    _km,
                    inspection_date,
                    insurance_date,
                    maintenance_date,
                    oil_change_date,
                    oil_change_km,
                    oil_interval_km,
                  notes,
                ) = current
                db.update_vehicle(
                    vehicle_id,
                    plate,
                    brand,
                    model,
                    year,
                    inspect_km,
                    inspection_date or "",
                    insurance_date or "",
                    maintenance_date or "",
                    oil_change_date or "",
                    oil_change_km or 0,
                    oil_interval_km or 0,
                    notes or "",
                    self._entry_region(),
                )
                self.refresh_vehicles()
        if fault_id and fault_status == "Kapandi":
            fault = db.get_vehicle_fault(fault_id)
            if fault:
                (
                    _fid,
                    f_vehicle_id,
                    title,
                    desc,
                    opened_date,
                    closed_date,
                    status,
                ) = fault
                if not closed_date:
                    closed_date = inspect_date
                db.update_vehicle_fault(
                    fault_id,
                    f_vehicle_id,
                    title,
                    desc,
                    opened_date,
                    closed_date,
                    "Kapandi",
                    self._entry_region(),
                )
                self.refresh_faults()
        messagebox.showinfo("Basarili", "Haftalik kontrol kaydedildi.")
        self.trigger_sync("vehicle_inspection")

    def on_inspect_vehicle_change(self, _event=None):
        plate = self.inspect_vehicle_var.get().strip()
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            return
        faults = db.list_open_vehicle_faults(vehicle_id=vehicle_id, region=self._view_region())
        if not faults:
            self.inspect_fault_var.set("")
            self.inspect_fault_status_var.set("Acik")
            return
        latest = faults[0]
        fault_id = latest[0]
        display = self.fault_display_by_id.get(fault_id)
        if display:
            self.inspect_fault_var.set(display)
            self.inspect_fault_status_var.set(latest[7] or "Acik")

    def _get_latest_inspection(self, vehicle_id, week_start):
        inspections = db.list_vehicle_inspections(
            vehicle_id=vehicle_id,
            week_start=week_start,
            region=self._view_region(),
        )
        if not inspections:
            return None
        inspections.sort(key=lambda x: x[5], reverse=True)
        return inspections[0]

    def compare_vehicle_week(self):
        for item in self.vehicle_compare_tree.get_children():
            self.vehicle_compare_tree.delete(item)
        plate = self.inspect_vehicle_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        inspect_date = self.inspect_date_var.get().strip()
        if not inspect_date:
            messagebox.showwarning("Uyari", "Tarih secin.")
            return
        try:
            inspect_date = normalize_date(inspect_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        week_start = week_start_from_date(inspect_date)
        prev_week = (datetime.strptime(week_start, "%Y-%m-%d").date() - timedelta(days=7)).strftime("%Y-%m-%d")

        current = self._get_latest_inspection(vehicle_id, week_start)
        previous = self._get_latest_inspection(vehicle_id, prev_week)
        if not current:
            messagebox.showwarning("Uyari", "Bu hafta icin kontrol bulunamadi.")
            return
        current_results = {row[0]: normalize_vehicle_status(row[1]) for row in db.list_vehicle_inspection_results(current[0])}
        prev_results = (
            {row[0]: normalize_vehicle_status(row[1]) for row in db.list_vehicle_inspection_results(previous[0])}
            if previous
            else {}
        )

        for item_key, label in VEHICLE_CHECKLIST:
            prev_status = prev_results.get(item_key, "-")
            curr_status = current_results.get(item_key, "-")
            if prev_status == curr_status:
                change = "Ayni"
            elif prev_status == "Olumsuz" and curr_status == "Olumsuz":
                change = "Tekrar eden sorun"
            elif curr_status == "Olumsuz" and prev_status != "Olumsuz":
                change = "Kotulesti"
            elif prev_status == "Olumsuz" and curr_status != "Olumsuz":
                change = "Iyilesti"
            else:
                change = "Degisti"
            self.vehicle_compare_tree.insert("", tk.END, values=(label, prev_status, curr_status, change))
        prev_fault_status = previous[10] if previous else None
        curr_fault_status = current[10]
        if prev_fault_status or curr_fault_status:
            prev_fault_status = prev_fault_status or "-"
            curr_fault_status = curr_fault_status or "-"
            if prev_fault_status == curr_fault_status:
                change = "Ayni"
            elif curr_fault_status == "Kapandi":
                change = "Iyilesti"
            elif prev_fault_status == "Kapandi" and curr_fault_status != "Kapandi":
                change = "Kotulesti"
            else:
                change = "Degisti"
            self.vehicle_compare_tree.insert(
                "",
                tk.END,
                values=("Ariza Durumu", prev_fault_status, curr_fault_status, change),
            )
        prev_service = "Evet" if previous and previous[11] else "Hayir"
        curr_service = "Evet" if current[11] else "Hayir"
        change = "Ayni" if prev_service == curr_service else "Degisti"
        self.vehicle_compare_tree.insert(
            "",
            tk.END,
            values=("Sanayiye Gitti", prev_service, curr_service, change),
        )

    def export_vehicle_weekly_report(self):
        plate = self.inspect_vehicle_var.get().strip()
        if not plate:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        inspect_date = self.inspect_date_var.get().strip()
        if not inspect_date:
            messagebox.showwarning("Uyari", "Tarih secin.")
            return
        try:
            inspect_date = normalize_date(inspect_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return
        week_start = week_start_from_date(inspect_date)
        prev_week = (datetime.strptime(week_start, "%Y-%m-%d").date() - timedelta(days=7)).strftime("%Y-%m-%d")
        current = self._get_latest_inspection(vehicle_id, week_start)
        previous = self._get_latest_inspection(vehicle_id, prev_week)
        if not current:
            messagebox.showwarning("Uyari", "Bu hafta icin kontrol bulunamadi.")
            return
        current_results = {row[0]: normalize_vehicle_status(row[1]) for row in db.list_vehicle_inspection_results(current[0])}
        prev_results = (
            {row[0]: normalize_vehicle_status(row[1]) for row in db.list_vehicle_inspection_results(previous[0])}
            if previous
            else {}
        )
        current_fault_id = current[9]
        current_fault_status = current[10] or ""
        current_service = bool(current[11])
        prev_fault_id = previous[9] if previous else None
        prev_fault_status = previous[10] if previous else ""
        prev_service = bool(previous[11]) if previous else False
        current_fault_title = ""
        prev_fault_title = ""
        if current_fault_id:
            fault = db.get_vehicle_fault(current_fault_id)
            if fault:
                current_fault_title = fault[2] or ""
        if prev_fault_id:
            fault = db.get_vehicle_fault(prev_fault_id)
            if fault:
                prev_fault_title = fault[2] or ""
        week_end = week_end_from_start(week_start)
        service_visits = db.list_vehicle_service_visits(
            vehicle_id=vehicle_id,
            start_date=week_start,
            end_date=week_end,
            region=self._view_region(),
        )

        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"arac_kontrol_{plate}_{week_start}.xlsx",
        )
        if not output_path:
            return
        vehicle = None
        for row in db.list_vehicles(region=self._view_region()):
            if row[1] == plate:
                vehicle = row
                break
        report.export_vehicle_weekly_report(
            output_path,
            plate,
            week_start,
            prev_week if previous else None,
            VEHICLE_CHECKLIST,
            prev_results,
            current_results,
            current[7],
            previous[7] if previous else None,
            vehicle,
            {
                "title": current_fault_title,
                "status": current_fault_status,
                "service": current_service,
            },
            {
                "title": prev_fault_title,
                "status": prev_fault_status,
                "service": prev_service,
            },
            service_visits,
        )

    def export_vehicle_card(self, plate):
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        vehicle = db.get_vehicle(vehicle_id)
        if not vehicle:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        inspections = db.list_vehicle_inspections(vehicle_id=vehicle_id, region=self._view_region())
        faults = db.list_vehicle_faults(vehicle_id=vehicle_id, region=self._view_region())
        services = db.list_vehicle_service_visits(vehicle_id=vehicle_id, region=self._view_region())
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"arac_karti_{plate}.xlsx",
        )
        if not output_path:
            return
        report.export_vehicle_card_report(
            output_path,
            plate,
            vehicle,
            inspections,
            faults,
            services,
        )
        messagebox.showinfo("Basarili", "Arac karti Excel olusturuldu.")
        messagebox.showinfo("Basarili", f"Rapor kaydedildi: {output_path}")

    def on_admin_right_click(self, event):
        row_id = self.admin_tree.identify_row(event.y)
        if row_id:
            self.admin_tree.selection_set(row_id)
            self.admin_menu.tk_popup(event.x_root, event.y_root)

    def show_admin_employee_detail(self):
        selected = self.admin_tree.selection()
        if not selected:
            return
        values = self.admin_tree.item(selected[0], "values")
        employee_name = values[0]
        employee_id = self.employee_map.get(employee_name)
        if not employee_id:
            messagebox.showwarning("Uyari", "Calisan bulunamadi.")
            return

        start_date = self.admin_start_var.get().strip() or None
        end_date = self.admin_end_var.get().strip() or None
        try:
            if start_date:
                start_date = normalize_date(start_date)
            if end_date:
                end_date = normalize_date(end_date)
        except ValueError as exc:
            messagebox.showwarning("Uyari", str(exc))
            return

        records = db.list_timesheets(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            region=self._view_region(),
        )
        detail = tk.Toplevel(self)
        detail.title(f"Mesai Detay - {employee_name}")
        detail.geometry("980x600")

        frame = ttk.Frame(detail)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        cols = ("date", "start", "end", "worked", "overtime", "night", "overnight", "special", "note")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        tree.heading("date", text="Tarih")
        tree.heading("start", text="Giris")
        tree.heading("end", text="Cikis")
        tree.heading("worked", text="Calisilan")
        tree.heading("overtime", text="Fazla Mesai")
        tree.heading("night", text="Gece")
        tree.heading("overnight", text="Geceye Tasan")
        tree.heading("special", text="Ozel Gun")
        tree.heading("note", text="Not")
        tree.column("date", width=100)
        tree.column("start", width=70)
        tree.column("end", width=70)
        tree.column("worked", width=90)
        tree.column("overtime", width=90)
        tree.column("night", width=90)
        tree.column("overnight", width=110)
        tree.column("special", width=90)
        tree.column("note", width=240)
        tree.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        for _ts_id, _emp_id, _name, work_date, start_time, end_time, break_minutes, is_special, notes in records:
            (
                worked,
                _scheduled,
                overtime,
                night_hours,
                overnight_hours,
                spec_norm,
                spec_ot,
                spec_night,
            ) = calc.calc_day_hours(
                work_date,
                start_time,
                end_time,
                break_minutes,
                self.settings,
                is_special,
            )
            special_total = round(spec_norm + spec_ot + spec_night, 2)
            tree.insert(
                "",
                tk.END,
                values=(
                    work_date,
                    start_time,
                    end_time,
                    worked,
                    overtime,
                    night_hours,
                    overnight_hours,
                    special_total,
                    notes or "",
                ),
            )

    # Settings tab
    def _build_settings_tab(self):
        frame = ttk.LabelFrame(self.tab_settings_body, text="Genel Ayarlar", style="Section.TLabelframe")
        frame.pack(fill=tk.X, padx=6, pady=6)

        self.company_name_var = tk.StringVar(value=self.settings.get("company_name", ""))
        self.report_title_var = tk.StringVar(value=self.settings.get("report_title", "Puantaj ve Mesai Raporu"))
        self.weekday_hours_var = tk.StringVar(value=self.settings.get("weekday_hours", "9"))
        self.sat_start_var = tk.StringVar(value=self.settings.get("saturday_start", "09:00"))
        self.sat_end_var = tk.StringVar(value=self.settings.get("saturday_end", "14:00"))
        self.logo_path_var = tk.StringVar(value=self.settings.get("logo_path", ""))
        self.sync_enabled_var = tk.BooleanVar(value=self.settings.get("sync_enabled", "0") == "1")
        self.sync_url_var = tk.StringVar(value=self.settings.get("sync_url", ""))
        self.sync_token_var = tk.StringVar(value=self.settings.get("sync_token", ""))
        self.admin_region_var.set(self.settings.get("admin_entry_region", "Ankara"))

        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=4)
        create_labeled_entry(row1, "Kurum Adi", self.company_name_var, 40).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row1, "Rapor Basligi", self.report_title_var, 32).pack(side=tk.LEFT, padx=6)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=4)
        create_labeled_entry(row2, "Hafta Ici Saat", self.weekday_hours_var, 10).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row2, "Cumartesi Baslangic", self.sat_start_var, 10).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(row2, "Cumartesi Bitis", self.sat_end_var, 10).pack(side=tk.LEFT, padx=6)
        if self.is_admin:
            ttk.Label(row2, text="Admin Bolge").pack(side=tk.LEFT, padx=(12, 6))
            region_combo = ttk.Combobox(
                row2,
                textvariable=self.admin_region_var,
                values=REGIONS,
                width=12,
                state="readonly",
            )
            region_combo.pack(side=tk.LEFT, padx=6)

        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, pady=4)
        ttk.Label(row3, text="Logo").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Entry(row3, textvariable=self.logo_path_var, width=60).pack(side=tk.LEFT)
        ttk.Button(row3, text="Sec", command=self.select_logo).pack(side=tk.LEFT, padx=6)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="Kaydet", style="Accent.TButton", command=self.save_settings).pack(
            side=tk.LEFT, padx=6
        )

        sync_frame = ttk.LabelFrame(self.tab_settings_body, text="Bulut Senkron", style="Section.TLabelframe")
        sync_frame.pack(fill=tk.X, padx=6, pady=6)
        srow1 = ttk.Frame(sync_frame)
        srow1.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(srow1, text="Senkronu Ac", variable=self.sync_enabled_var).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(srow1, "Sunucu URL", self.sync_url_var, 40).pack(side=tk.LEFT, padx=6)
        srow2 = ttk.Frame(sync_frame)
        srow2.pack(fill=tk.X, pady=4)
        create_labeled_entry(srow2, "API Token", self.sync_token_var, 40).pack(side=tk.LEFT, padx=6)
        ttk.Button(srow2, text="Senkronu Dene", command=self.manual_sync).pack(side=tk.LEFT, padx=6)
        ttk.Label(
            sync_frame,
            text="Kayit sonrasi otomatik yukleme yapilir. URL ornek: https://seninapp.onrender.com",
            foreground="#5f6a72",
        ).pack(anchor="w", padx=8, pady=(2, 6))

        template_frame = ttk.LabelFrame(self.tab_settings_body, text="Vardiya Sablonlari", style="Section.TLabelframe")
        template_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.st_id_var = tk.StringVar()
        self.st_name_var = tk.StringVar()
        self.st_start_var = tk.StringVar(value="09:00")
        self.st_end_var = tk.StringVar(value="18:00")
        self.st_break_var = tk.StringVar(value="60")

        trow1 = ttk.Frame(template_frame)
        trow1.pack(fill=tk.X, pady=4)
        create_labeled_entry(trow1, "Sablon Adi", self.st_name_var, 26).pack(side=tk.LEFT, padx=6)
        start_tpl_frame = create_time_entry(trow1, "Giris", self.st_start_var, 8)
        start_tpl_frame.pack(side=tk.LEFT, padx=6)
        end_tpl_frame = create_time_entry(trow1, "Cikis", self.st_end_var, 8)
        end_tpl_frame.pack(side=tk.LEFT, padx=6)
        create_labeled_entry(trow1, "Mola dk", self.st_break_var, 8).pack(side=tk.LEFT, padx=6)
        for child in start_tpl_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.bind("<FocusOut>", lambda _e: normalize_time_in_var(self.st_start_var))
        for child in end_tpl_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.bind("<FocusOut>", lambda _e: normalize_time_in_var(self.st_end_var))

        trow2 = ttk.Frame(template_frame)
        trow2.pack(fill=tk.X, pady=4)
        ttk.Button(trow2, text="Kaydet", style="Accent.TButton", command=self.save_shift_template).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(trow2, text="Sil", command=self.delete_shift_template).pack(side=tk.LEFT)
        ttk.Button(trow2, text="Temizle", command=self.clear_shift_template_form).pack(side=tk.LEFT, padx=6)

        list_frame = ttk.Frame(template_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        columns = ("id", "name", "start", "end", "break")
        self.template_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.template_tree.heading("id", text="ID")
        self.template_tree.heading("name", text="Sablon")
        self.template_tree.heading("start", text="Giris")
        self.template_tree.heading("end", text="Cikis")
        self.template_tree.heading("break", text="Mola")
        self.template_tree.column("id", width=60, anchor=tk.CENTER)
        self.template_tree.column("name", width=220)
        self.template_tree.column("start", width=80)
        self.template_tree.column("end", width=80)
        self.template_tree.column("break", width=80)
        self.template_tree.tag_configure("odd", background="#f5f7fb")
        tpl_xscroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.template_tree.xview)
        tpl_yscroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.template_tree.yview)
        self.template_tree.configure(xscrollcommand=tpl_xscroll.set, yscrollcommand=tpl_yscroll.set)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.template_tree.grid(row=0, column=0, sticky="nsew")
        tpl_yscroll.grid(row=0, column=1, sticky="ns")
        tpl_xscroll.grid(row=1, column=0, sticky="ew")
        self.template_tree.bind("<<TreeviewSelect>>", self.on_template_select)

    def _build_vehicles_tab(self):
        vehicle_frame = ttk.LabelFrame(self.tab_vehicles_body, text="Arac Bilgisi", style="Section.TLabelframe")
        vehicle_frame.pack(fill=tk.X, padx=6, pady=6)

        self.vehicle_id_var = tk.StringVar()
        self.vehicle_plate_var = tk.StringVar()
        self.vehicle_brand_var = tk.StringVar()
        self.vehicle_model_var = tk.StringVar()
        self.vehicle_year_var = tk.StringVar()
        self.vehicle_km_var = tk.StringVar()
        self.vehicle_inspection_var = tk.StringVar()
        self.vehicle_insurance_var = tk.StringVar()
        self.vehicle_maintenance_var = tk.StringVar()
        self.vehicle_oil_var = tk.StringVar()
        self.vehicle_oil_km_var = tk.StringVar()
        self.vehicle_oil_interval_var = tk.StringVar(value=str(DEFAULT_OIL_INTERVAL_KM))
        self.vehicle_notes_var = tk.StringVar()

        vrow1 = ttk.Frame(vehicle_frame)
        vrow1.pack(fill=tk.X, pady=4)
        create_labeled_entry(vrow1, "Plaka", self.vehicle_plate_var, 12).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow1, "Marka", self.vehicle_brand_var, 14).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow1, "Model", self.vehicle_model_var, 14).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow1, "Yil", self.vehicle_year_var, 8).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow1, "KM", self.vehicle_km_var, 10).pack(side=tk.LEFT, padx=6)

        vrow2 = ttk.Frame(vehicle_frame)
        vrow2.pack(fill=tk.X, pady=4)
        insp_frame, self.vehicle_insp_entry = create_labeled_date(vrow2, "Muayene", self.vehicle_inspection_var, 12)
        insp_frame.pack(side=tk.LEFT, padx=6)
        ins_frame, self.vehicle_ins_entry = create_labeled_date(vrow2, "Sigorta", self.vehicle_insurance_var, 12)
        ins_frame.pack(side=tk.LEFT, padx=6)
        maint_frame, self.vehicle_maint_entry = create_labeled_date(
            vrow2, "Bakim", self.vehicle_maintenance_var, 12
        )
        maint_frame.pack(side=tk.LEFT, padx=6)
        oil_frame, self.vehicle_oil_entry = create_labeled_date(vrow2, "Yag", self.vehicle_oil_var, 12)
        oil_frame.pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow2, "Yag KM", self.vehicle_oil_km_var, 10).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow2, "Periyot KM", self.vehicle_oil_interval_var, 10).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(vrow2, "Not", self.vehicle_notes_var, 30).pack(side=tk.LEFT, padx=6)

        vbtn = ttk.Frame(vehicle_frame)
        vbtn.pack(fill=tk.X, pady=6)
        ttk.Button(vbtn, text="Kaydet", style="Accent.TButton", command=self.add_or_update_vehicle).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(vbtn, text="Sil", command=self.delete_vehicle).pack(side=tk.LEFT)
        ttk.Button(vbtn, text="Temizle", command=self.clear_vehicle_form).pack(side=tk.LEFT, padx=6)

        vlist_frame = ttk.Frame(self.tab_vehicles_body)
        vlist_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vehicle_tree = ttk.Treeview(
            vlist_frame,
            columns=(
                "id",
                "plate",
                "brand",
                "model",
                "year",
                "km",
                "inspection",
                "insurance",
                "maintenance",
                "oil_due",
            ),
            show="headings",
        )
        self.vehicle_tree.heading("id", text="ID")
        self.vehicle_tree.heading("plate", text="Plaka")
        self.vehicle_tree.heading("brand", text="Marka")
        self.vehicle_tree.heading("model", text="Model")
        self.vehicle_tree.heading("year", text="Yil")
        self.vehicle_tree.heading("km", text="KM")
        self.vehicle_tree.heading("inspection", text="Muayene")
        self.vehicle_tree.heading("insurance", text="Sigorta")
        self.vehicle_tree.heading("maintenance", text="Bakim")
        self.vehicle_tree.heading("oil_due", text="Yag Durum")
        self.vehicle_tree.column("id", width=60, anchor=tk.CENTER)
        self.vehicle_tree.column("plate", width=100)
        self.vehicle_tree.column("brand", width=120)
        self.vehicle_tree.column("model", width=120)
        self.vehicle_tree.column("year", width=70)
        self.vehicle_tree.column("km", width=80)
        self.vehicle_tree.column("inspection", width=100)
        self.vehicle_tree.column("insurance", width=100)
        self.vehicle_tree.column("maintenance", width=100)
        self.vehicle_tree.column("oil_due", width=120)
        v_xscroll = ttk.Scrollbar(vlist_frame, orient=tk.HORIZONTAL, command=self.vehicle_tree.xview)
        v_yscroll = ttk.Scrollbar(vlist_frame, orient=tk.VERTICAL, command=self.vehicle_tree.yview)
        self.vehicle_tree.configure(xscrollcommand=v_xscroll.set, yscrollcommand=v_yscroll.set)
        vlist_frame.columnconfigure(0, weight=1)
        vlist_frame.rowconfigure(0, weight=1)
        self.vehicle_tree.grid(row=0, column=0, sticky="nsew")
        v_yscroll.grid(row=0, column=1, sticky="ns")
        v_xscroll.grid(row=1, column=0, sticky="ew")
        self.vehicle_tree.bind("<<TreeviewSelect>>", self.on_vehicle_select)
        self.vehicle_tree.bind("<Double-1>", lambda _e: self.show_vehicle_card_from_list())

        vcard_row = ttk.Frame(self.tab_vehicles_body)
        vcard_row.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(vcard_row, text="Arac Karti", command=self.show_vehicle_card_from_list).pack(
            side=tk.LEFT, padx=6
        )

        driver_frame = ttk.LabelFrame(self.tab_vehicles_body, text="Surucu Bilgisi", style="Section.TLabelframe")
        driver_frame.pack(fill=tk.X, padx=6, pady=6)

        self.driver_id_var = tk.StringVar()
        self.driver_name_var = tk.StringVar()
        self.driver_license_var = tk.StringVar()
        self.driver_license_exp_var = tk.StringVar()
        self.driver_phone_var = tk.StringVar()
        self.driver_notes_var = tk.StringVar()

        drow1 = ttk.Frame(driver_frame)
        drow1.pack(fill=tk.X, pady=4)
        create_labeled_entry(drow1, "Ad Soyad", self.driver_name_var, 24).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(drow1, "Ehliyet Sinifi", self.driver_license_var, 12).pack(side=tk.LEFT, padx=6)
        d_exp_frame, self.driver_exp_entry = create_labeled_date(drow1, "Bitis", self.driver_license_exp_var, 12)
        d_exp_frame.pack(side=tk.LEFT, padx=6)
        create_labeled_entry(drow1, "Telefon", self.driver_phone_var, 14).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(drow1, "Not", self.driver_notes_var, 30).pack(side=tk.LEFT, padx=6)

        dbtn = ttk.Frame(driver_frame)
        dbtn.pack(fill=tk.X, pady=6)
        ttk.Button(dbtn, text="Kaydet", style="Accent.TButton", command=self.add_or_update_driver).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(dbtn, text="Sil", command=self.delete_driver).pack(side=tk.LEFT)
        ttk.Button(dbtn, text="Temizle", command=self.clear_driver_form).pack(side=tk.LEFT, padx=6)

        dlist_frame = ttk.Frame(self.tab_vehicles_body)
        dlist_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.driver_tree = ttk.Treeview(
            dlist_frame,
            columns=("id", "name", "license", "expiry", "phone"),
            show="headings",
        )
        self.driver_tree.heading("id", text="ID")
        self.driver_tree.heading("name", text="Ad Soyad")
        self.driver_tree.heading("license", text="Ehliyet")
        self.driver_tree.heading("expiry", text="Bitis")
        self.driver_tree.heading("phone", text="Telefon")
        self.driver_tree.column("id", width=60, anchor=tk.CENTER)
        self.driver_tree.column("name", width=220)
        self.driver_tree.column("license", width=100)
        self.driver_tree.column("expiry", width=100)
        self.driver_tree.column("phone", width=120)
        d_xscroll = ttk.Scrollbar(dlist_frame, orient=tk.HORIZONTAL, command=self.driver_tree.xview)
        d_yscroll = ttk.Scrollbar(dlist_frame, orient=tk.VERTICAL, command=self.driver_tree.yview)
        self.driver_tree.configure(xscrollcommand=d_xscroll.set, yscrollcommand=d_yscroll.set)
        dlist_frame.columnconfigure(0, weight=1)
        dlist_frame.rowconfigure(0, weight=1)
        self.driver_tree.grid(row=0, column=0, sticky="nsew")
        d_yscroll.grid(row=0, column=1, sticky="ns")
        d_xscroll.grid(row=1, column=0, sticky="ew")
        self.driver_tree.bind("<<TreeviewSelect>>", self.on_driver_select)
        self.driver_tree.bind("<Double-1>", lambda _e: self.show_driver_detail_from_list())

        inspect_frame = ttk.LabelFrame(self.tab_vehicles_body, text="Haftalik Kontrol", style="Section.TLabelframe")
        inspect_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.inspect_vehicle_var = tk.StringVar()
        self.inspect_driver_var = tk.StringVar()
        self.inspect_date_var = tk.StringVar()
        self.inspect_km_var = tk.StringVar()
        self.inspect_notes_var = tk.StringVar()
        self.inspect_fault_var = tk.StringVar()
        self.inspect_fault_status_var = tk.StringVar(value="Acik")
        self.inspect_service_var = tk.BooleanVar(value=False)

        irow1 = ttk.Frame(inspect_frame)
        irow1.pack(fill=tk.X, pady=4)
        ttk.Label(irow1, text="Arac").pack(side=tk.LEFT, padx=(0, 6))
        self.inspect_vehicle_combo = ttk.Combobox(irow1, textvariable=self.inspect_vehicle_var, width=18, state="readonly")
        self.inspect_vehicle_combo.pack(side=tk.LEFT)
        self.inspect_vehicle_combo.bind("<<ComboboxSelected>>", self.on_inspect_vehicle_change)
        ttk.Label(irow1, text="Surucu").pack(side=tk.LEFT, padx=(12, 6))
        self.inspect_driver_combo = ttk.Combobox(irow1, textvariable=self.inspect_driver_var, width=18, state="readonly")
        self.inspect_driver_combo.pack(side=tk.LEFT)
        date_frame, self.inspect_date_entry = create_labeled_date(irow1, "Tarih", self.inspect_date_var, 12)
        date_frame.pack(side=tk.LEFT, padx=6)
        create_labeled_entry(irow1, "KM", self.inspect_km_var, 10).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(irow1, "Not", self.inspect_notes_var, 40).pack(side=tk.LEFT, padx=6)

        irow2 = ttk.Frame(inspect_frame)
        irow2.pack(fill=tk.X, pady=4)
        ttk.Label(irow2, text="Ariza").pack(side=tk.LEFT, padx=(0, 6))
        self.inspect_fault_combo = ttk.Combobox(
            irow2,
            textvariable=self.inspect_fault_var,
            width=40,
            state="readonly",
            values=[""],
        )
        self.inspect_fault_combo.pack(side=tk.LEFT)
        ttk.Label(irow2, text="Durum").pack(side=tk.LEFT, padx=(12, 6))
        ttk.Combobox(
            irow2,
            textvariable=self.inspect_fault_status_var,
            values=["Acik", "Kapandi", "Takip"],
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(irow2, text="Sanayiye Gitti", variable=self.inspect_service_var).pack(
            side=tk.LEFT, padx=12
        )
        ttk.Label(
            inspect_frame,
            text="Ariza opsiyonel. Sanayiye gidis icin ariza secin; donus tarihi bilinmiyorsa bos kalabilir.",
            foreground="#5f6a72",
        ).pack(anchor="w", padx=8, pady=(2, 6))

        self.inspect_item_vars = {}
        self.inspect_note_vars = {}
        status_values = ["Olumlu", "Olumsuz", "Bilinmiyor"]
        for item_key, label in VEHICLE_CHECKLIST:
            row = ttk.Frame(inspect_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=22).pack(side=tk.LEFT, padx=6)
            status_var = tk.StringVar(value="Olumlu")
            note_var = tk.StringVar()
            ttk.Combobox(row, textvariable=status_var, values=status_values, width=10, state="readonly").pack(
                side=tk.LEFT
            )
            ttk.Entry(row, textvariable=note_var, width=60).pack(side=tk.LEFT, padx=6)
            self.inspect_item_vars[item_key] = status_var
            self.inspect_note_vars[item_key] = note_var

        ibtn = ttk.Frame(inspect_frame)
        ibtn.pack(fill=tk.X, pady=6)
        ttk.Button(ibtn, text="Kontrolu Kaydet", style="Accent.TButton", command=self.save_vehicle_inspection).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(ibtn, text="Haftalik Karsilastir", command=self.compare_vehicle_week).pack(side=tk.LEFT, padx=6)
        ttk.Button(ibtn, text="Excel Raporu", command=self.export_vehicle_weekly_report).pack(
            side=tk.LEFT, padx=6
        )

        compare_frame = ttk.LabelFrame(self.tab_vehicles_body, text="Haftalik Karsilastirma", style="Section.TLabelframe")
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vehicle_compare_tree = ttk.Treeview(
            compare_frame,
            columns=("item", "prev", "current", "change"),
            show="headings",
            height=8,
        )
        self.vehicle_compare_tree.heading("item", text="Kontrol")
        self.vehicle_compare_tree.heading("prev", text="Onceki Hafta")
        self.vehicle_compare_tree.heading("current", text="Bu Hafta")
        self.vehicle_compare_tree.heading("change", text="Durum")
        self.vehicle_compare_tree.column("item", width=220)
        self.vehicle_compare_tree.column("prev", width=120)
        self.vehicle_compare_tree.column("current", width=120)
        self.vehicle_compare_tree.column("change", width=160)
        vc_xscroll = ttk.Scrollbar(compare_frame, orient=tk.HORIZONTAL, command=self.vehicle_compare_tree.xview)
        vc_yscroll = ttk.Scrollbar(compare_frame, orient=tk.VERTICAL, command=self.vehicle_compare_tree.yview)
        self.vehicle_compare_tree.configure(xscrollcommand=vc_xscroll.set, yscrollcommand=vc_yscroll.set)
        compare_frame.columnconfigure(0, weight=1)
        compare_frame.rowconfigure(0, weight=1)
        self.vehicle_compare_tree.grid(row=0, column=0, sticky="nsew")
        vc_yscroll.grid(row=0, column=1, sticky="ns")
        vc_xscroll.grid(row=1, column=0, sticky="ew")

    def _build_dashboard_tab(self):
        summary = ttk.LabelFrame(self.tab_dashboard_body, text="Genel Ozet", style="Section.TLabelframe")
        summary.pack(fill=tk.X, padx=6, pady=6)

        self.dashboard_stats = {
            "vehicles": tk.StringVar(value="0"),
            "drivers": tk.StringVar(value="0"),
            "oil_due": tk.StringVar(value="0"),
            "inspection_due": tk.StringVar(value="0"),
            "insurance_due": tk.StringVar(value="0"),
            "maintenance_due": tk.StringVar(value="0"),
            "license_due": tk.StringVar(value="0"),
        }

        row1 = ttk.Frame(summary)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Arac").pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, textvariable=self.dashboard_stats["vehicles"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Surucu").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.dashboard_stats["drivers"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Yag Degisimi").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.dashboard_stats["oil_due"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Muayene").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.dashboard_stats["inspection_due"]).pack(side=tk.LEFT, padx=6)

        row2 = ttk.Frame(summary)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="Sigorta").pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, textvariable=self.dashboard_stats["insurance_due"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="Bakim").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.dashboard_stats["maintenance_due"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="Ehliyet").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.dashboard_stats["license_due"]).pack(side=tk.LEFT, padx=6)

        vehicle_status = ttk.LabelFrame(self.tab_dashboard_body, text="Arac Durumu", style="Section.TLabelframe")
        vehicle_status.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vehicle_status_tree = ttk.Treeview(
            vehicle_status,
            columns=(
                "plate",
                "km",
                "oil",
                "inspection",
                "insurance",
                "maintenance",
                "last_check",
                "driver",
            ),
            show="headings",
            height=10,
        )
        self.vehicle_status_tree.heading("plate", text="Plaka")
        self.vehicle_status_tree.heading("km", text="KM")
        self.vehicle_status_tree.heading("oil", text="Yag")
        self.vehicle_status_tree.heading("inspection", text="Muayene")
        self.vehicle_status_tree.heading("insurance", text="Sigorta")
        self.vehicle_status_tree.heading("maintenance", text="Bakim")
        self.vehicle_status_tree.heading("last_check", text="Son Kontrol")
        self.vehicle_status_tree.heading("driver", text="Surucu")
        self.vehicle_status_tree.column("plate", width=120)
        self.vehicle_status_tree.column("km", width=80)
        self.vehicle_status_tree.column("oil", width=110)
        self.vehicle_status_tree.column("inspection", width=110)
        self.vehicle_status_tree.column("insurance", width=110)
        self.vehicle_status_tree.column("maintenance", width=110)
        self.vehicle_status_tree.column("last_check", width=110)
        self.vehicle_status_tree.column("driver", width=160)
        self.vehicle_status_tree.tag_configure("oil_due", background="#fde68a")
        self.vehicle_status_tree.tag_configure("oil_soon", background="#fff7ed")
        vs_xscroll = ttk.Scrollbar(vehicle_status, orient=tk.HORIZONTAL, command=self.vehicle_status_tree.xview)
        vs_yscroll = ttk.Scrollbar(vehicle_status, orient=tk.VERTICAL, command=self.vehicle_status_tree.yview)
        self.vehicle_status_tree.configure(xscrollcommand=vs_xscroll.set, yscrollcommand=vs_yscroll.set)
        vehicle_status.columnconfigure(0, weight=1)
        vehicle_status.rowconfigure(0, weight=1)
        self.vehicle_status_tree.grid(row=0, column=0, sticky="nsew")
        vs_yscroll.grid(row=0, column=1, sticky="ns")
        vs_xscroll.grid(row=1, column=0, sticky="ew")
        self.vehicle_status_menu = tk.Menu(self, tearoff=0)
        self.vehicle_status_menu.add_command(label="Detay", command=self.show_vehicle_detail)
        self.vehicle_status_tree.bind("<Button-3>", self.on_vehicle_status_right_click)
        self.vehicle_status_tree.bind("<Double-1>", lambda _e: self.show_vehicle_detail())

        vehicle_alerts = ttk.LabelFrame(self.tab_dashboard_body, text="Arac Uyarilari", style="Section.TLabelframe")
        vehicle_alerts.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vehicle_alert_tree = ttk.Treeview(
            vehicle_alerts,
            columns=("plate", "issue", "detail"),
            show="headings",
            height=6,
        )
        self.vehicle_alert_tree.heading("plate", text="Plaka")
        self.vehicle_alert_tree.heading("issue", text="Uyari")
        self.vehicle_alert_tree.heading("detail", text="Detay")
        self.vehicle_alert_tree.column("plate", width=120)
        self.vehicle_alert_tree.column("issue", width=200)
        self.vehicle_alert_tree.column("detail", width=240)
        va_xscroll = ttk.Scrollbar(vehicle_alerts, orient=tk.HORIZONTAL, command=self.vehicle_alert_tree.xview)
        va_yscroll = ttk.Scrollbar(vehicle_alerts, orient=tk.VERTICAL, command=self.vehicle_alert_tree.yview)
        self.vehicle_alert_tree.configure(xscrollcommand=va_xscroll.set, yscrollcommand=va_yscroll.set)
        vehicle_alerts.columnconfigure(0, weight=1)
        vehicle_alerts.rowconfigure(0, weight=1)
        self.vehicle_alert_tree.grid(row=0, column=0, sticky="nsew")
        va_yscroll.grid(row=0, column=1, sticky="ns")
        va_xscroll.grid(row=1, column=0, sticky="ew")

        driver_alerts = ttk.LabelFrame(self.tab_dashboard_body, text="Surucu Uyarilari", style="Section.TLabelframe")
        driver_alerts.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.driver_alert_tree = ttk.Treeview(
            driver_alerts,
            columns=("driver", "issue", "detail"),
            show="headings",
            height=6,
        )
        self.driver_alert_tree.heading("driver", text="Surucu")
        self.driver_alert_tree.heading("issue", text="Uyari")
        self.driver_alert_tree.heading("detail", text="Detay")
        self.driver_alert_tree.column("driver", width=200)
        self.driver_alert_tree.column("issue", width=200)
        self.driver_alert_tree.column("detail", width=240)
        da_xscroll = ttk.Scrollbar(driver_alerts, orient=tk.HORIZONTAL, command=self.driver_alert_tree.xview)
        da_yscroll = ttk.Scrollbar(driver_alerts, orient=tk.VERTICAL, command=self.driver_alert_tree.yview)
        self.driver_alert_tree.configure(xscrollcommand=da_xscroll.set, yscrollcommand=da_yscroll.set)
        driver_alerts.columnconfigure(0, weight=1)
        driver_alerts.rowconfigure(0, weight=1)
        self.driver_alert_tree.grid(row=0, column=0, sticky="nsew")
        da_yscroll.grid(row=0, column=1, sticky="ns")
        da_xscroll.grid(row=1, column=0, sticky="ew")

    def _build_service_tab(self):
        fault_frame = ttk.LabelFrame(self.tab_service_body, text="Ariza Kaydi", style="Section.TLabelframe")
        fault_frame.pack(fill=tk.X, padx=6, pady=6)

        self.fault_id_var = tk.StringVar()
        self.fault_vehicle_var = tk.StringVar()
        self.fault_title_var = tk.StringVar()
        self.fault_desc_var = tk.StringVar()
        self.fault_open_var = tk.StringVar()
        self.fault_close_var = tk.StringVar()
        self.fault_status_var = tk.StringVar(value="Acik")

        frow1 = ttk.Frame(fault_frame)
        frow1.pack(fill=tk.X, pady=4)
        ttk.Label(frow1, text="Arac").pack(side=tk.LEFT, padx=(0, 6))
        self.fault_vehicle_combo = ttk.Combobox(
            frow1, textvariable=self.fault_vehicle_var, width=18, state="readonly"
        )
        self.fault_vehicle_combo.pack(side=tk.LEFT)
        create_labeled_entry(frow1, "Baslik", self.fault_title_var, 24).pack(side=tk.LEFT, padx=6)

        frow2 = ttk.Frame(fault_frame)
        frow2.pack(fill=tk.X, pady=4)
        create_labeled_entry(frow2, "Aciklama", self.fault_desc_var, 60).pack(side=tk.LEFT, padx=6)

        frow3 = ttk.Frame(fault_frame)
        frow3.pack(fill=tk.X, pady=4)
        open_frame, self.fault_open_entry = create_labeled_date(frow3, "Acilis", self.fault_open_var, 12)
        open_frame.pack(side=tk.LEFT, padx=6)
        close_frame, self.fault_close_entry = create_labeled_date(frow3, "Kapanis", self.fault_close_var, 12)
        close_frame.pack(side=tk.LEFT, padx=6)
        ttk.Label(frow3, text="Durum").pack(side=tk.LEFT, padx=(12, 6))
        ttk.Combobox(
            frow3,
            textvariable=self.fault_status_var,
            values=["Acik", "Kapandi", "Takip"],
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT)

        fbtn = ttk.Frame(fault_frame)
        fbtn.pack(fill=tk.X, pady=6)
        ttk.Button(fbtn, text="Kaydet", style="Accent.TButton", command=self.add_or_update_fault).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(fbtn, text="Sil", command=self.delete_fault).pack(side=tk.LEFT)
        ttk.Button(fbtn, text="Temizle", command=self.clear_fault_form).pack(side=tk.LEFT, padx=6)

        fault_list = ttk.Frame(self.tab_service_body)
        fault_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.fault_tree = ttk.Treeview(
            fault_list,
            columns=("id", "plate", "title", "status", "opened", "closed"),
            show="headings",
            height=8,
        )
        self.fault_tree.heading("id", text="ID")
        self.fault_tree.heading("plate", text="Plaka")
        self.fault_tree.heading("title", text="Baslik")
        self.fault_tree.heading("status", text="Durum")
        self.fault_tree.heading("opened", text="Acilis")
        self.fault_tree.heading("closed", text="Kapanis")
        self.fault_tree.column("id", width=60, anchor=tk.CENTER)
        self.fault_tree.column("plate", width=100)
        self.fault_tree.column("title", width=220)
        self.fault_tree.column("status", width=100)
        self.fault_tree.column("opened", width=120)
        self.fault_tree.column("closed", width=120)
        f_xscroll = ttk.Scrollbar(fault_list, orient=tk.HORIZONTAL, command=self.fault_tree.xview)
        f_yscroll = ttk.Scrollbar(fault_list, orient=tk.VERTICAL, command=self.fault_tree.yview)
        self.fault_tree.configure(xscrollcommand=f_xscroll.set, yscrollcommand=f_yscroll.set)
        fault_list.columnconfigure(0, weight=1)
        fault_list.rowconfigure(0, weight=1)
        self.fault_tree.grid(row=0, column=0, sticky="nsew")
        f_yscroll.grid(row=0, column=1, sticky="ns")
        f_xscroll.grid(row=1, column=0, sticky="ew")
        self.fault_tree.bind("<<TreeviewSelect>>", self.on_fault_select)

        service_frame = ttk.LabelFrame(self.tab_service_body, text="Sanayi Kaydi", style="Section.TLabelframe")
        service_frame.pack(fill=tk.X, padx=6, pady=6)

        self.service_id_var = tk.StringVar()
        self.service_vehicle_var = tk.StringVar()
        self.service_fault_var = tk.StringVar()
        self.service_start_var = tk.StringVar()
        self.service_end_var = tk.StringVar()
        self.service_reason_var = tk.StringVar()
        self.service_cost_var = tk.StringVar()
        self.service_notes_var = tk.StringVar()
        self.service_in_shop_var = tk.BooleanVar(value=False)

        srow1 = ttk.Frame(service_frame)
        srow1.pack(fill=tk.X, pady=4)
        ttk.Label(srow1, text="Arac").pack(side=tk.LEFT, padx=(0, 6))
        self.service_vehicle_combo = ttk.Combobox(
            srow1, textvariable=self.service_vehicle_var, width=18, state="readonly"
        )
        self.service_vehicle_combo.pack(side=tk.LEFT)
        ttk.Label(srow1, text="Ariza").pack(side=tk.LEFT, padx=(12, 6))
        self.service_fault_combo = ttk.Combobox(
            srow1, textvariable=self.service_fault_var, width=40, state="readonly", values=[""]
        )
        self.service_fault_combo.pack(side=tk.LEFT)

        srow2 = ttk.Frame(service_frame)
        srow2.pack(fill=tk.X, pady=4)
        start_frame, self.service_start_entry = create_labeled_date(srow2, "Gidis", self.service_start_var, 12)
        start_frame.pack(side=tk.LEFT, padx=6)
        end_frame, self.service_end_entry = create_labeled_date(srow2, "Donus", self.service_end_var, 12)
        end_frame.pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(
            srow2,
            text="Sanayide",
            variable=self.service_in_shop_var,
            command=self._toggle_service_end_date,
        ).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(srow2, "Masraf", self.service_cost_var, 10).pack(side=tk.LEFT, padx=6)

        srow3 = ttk.Frame(service_frame)
        srow3.pack(fill=tk.X, pady=4)
        create_labeled_entry(srow3, "Neden", self.service_reason_var, 40).pack(side=tk.LEFT, padx=6)
        create_labeled_entry(srow3, "Not", self.service_notes_var, 40).pack(side=tk.LEFT, padx=6)

        sbtn = ttk.Frame(service_frame)
        sbtn.pack(fill=tk.X, pady=6)
        ttk.Button(sbtn, text="Kaydet", style="Accent.TButton", command=self.add_or_update_service_visit).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(sbtn, text="Sil", command=self.delete_service_visit).pack(side=tk.LEFT)
        ttk.Button(sbtn, text="Temizle", command=self.clear_service_visit_form).pack(side=tk.LEFT, padx=6)

        service_list = ttk.Frame(self.tab_service_body)
        service_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.service_tree = ttk.Treeview(
            service_list,
            columns=("id", "plate", "fault", "start", "end", "cost", "reason"),
            show="headings",
            height=8,
        )
        self.service_tree.heading("id", text="ID")
        self.service_tree.heading("plate", text="Plaka")
        self.service_tree.heading("fault", text="Ariza")
        self.service_tree.heading("start", text="Gidis")
        self.service_tree.heading("end", text="Donus")
        self.service_tree.heading("cost", text="Masraf")
        self.service_tree.heading("reason", text="Neden")
        self.service_tree.column("id", width=60, anchor=tk.CENTER)
        self.service_tree.column("plate", width=100)
        self.service_tree.column("fault", width=220)
        self.service_tree.column("start", width=120)
        self.service_tree.column("end", width=120)
        self.service_tree.column("cost", width=90)
        self.service_tree.column("reason", width=180)
        s_xscroll = ttk.Scrollbar(service_list, orient=tk.HORIZONTAL, command=self.service_tree.xview)
        s_yscroll = ttk.Scrollbar(service_list, orient=tk.VERTICAL, command=self.service_tree.yview)
        self.service_tree.configure(xscrollcommand=s_xscroll.set, yscrollcommand=s_yscroll.set)
        service_list.columnconfigure(0, weight=1)
        service_list.rowconfigure(0, weight=1)
        self.service_tree.grid(row=0, column=0, sticky="nsew")
        s_yscroll.grid(row=0, column=1, sticky="ns")
        s_xscroll.grid(row=1, column=0, sticky="ew")
        self.service_tree.bind("<<TreeviewSelect>>", self.on_service_visit_select)

    def on_vehicle_status_right_click(self, event):
        row_id = self.vehicle_status_tree.identify_row(event.y)
        if not row_id:
            return
        self.vehicle_status_tree.selection_set(row_id)
        try:
            self.vehicle_status_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.vehicle_status_menu.grab_release()

    def show_vehicle_detail(self):
        selected = self.vehicle_status_tree.selection()
        if not selected:
            return
        values = self.vehicle_status_tree.item(selected[0], "values")
        if not values:
            return
        plate = values[0]
        self._open_vehicle_card(plate)

    def show_vehicle_card_from_list(self):
        selected = self.vehicle_tree.selection()
        if not selected:
            messagebox.showwarning("Uyari", "Arac secin.")
            return
        values = self.vehicle_tree.item(selected[0], "values")
        if not values:
            return
        plate = values[1]
        self._open_vehicle_card(plate)

    def show_driver_detail_from_list(self):
        selected = self.driver_tree.selection()
        if not selected:
            messagebox.showwarning("Uyari", "Surucu secin.")
            return
        values = self.driver_tree.item(selected[0], "values")
        if not values:
            return
        driver_id = parse_int(values[0])
        self._open_driver_card(driver_id)

    def _open_vehicle_card(self, plate):
        vehicle_id = self.vehicle_map.get(plate)
        if not vehicle_id:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return
        vehicle = db.get_vehicle(vehicle_id)
        if not vehicle:
            messagebox.showwarning("Uyari", "Arac bulunamadi.")
            return

        (
            _vid,
            _plate,
            brand,
            model,
            year,
            km,
            inspection_date,
            insurance_date,
            maintenance_date,
            oil_change_date,
            oil_change_km,
            oil_interval_km,
            notes,
        ) = vehicle

        detail_win = tk.Toplevel(self)
        detail_win.title(f"Arac Karti - {plate}")
        detail_win.geometry("980x700")

        info = ttk.LabelFrame(detail_win, text="Arac Bilgisi", style="Section.TLabelframe")
        info.pack(fill=tk.X, padx=10, pady=8)
        info_row1 = ttk.Frame(info)
        info_row1.pack(fill=tk.X, pady=4)
        ttk.Label(info_row1, text=f"Plaka: {plate}").pack(side=tk.LEFT, padx=6)
        ttk.Label(info_row1, text=f"Marka/Model: {brand} {model}").pack(side=tk.LEFT, padx=12)
        ttk.Label(info_row1, text=f"Yil: {year}").pack(side=tk.LEFT, padx=12)
        info_row2 = ttk.Frame(info)
        info_row2.pack(fill=tk.X, pady=4)
        ttk.Label(info_row2, text=f"KM: {km or '-'}").pack(side=tk.LEFT, padx=6)
        ttk.Label(info_row2, text=f"Yag Degisim: {oil_change_date or '-'}").pack(side=tk.LEFT, padx=12)
        ttk.Label(info_row2, text=f"Yag KM: {oil_change_km or '-'}").pack(side=tk.LEFT, padx=12)
        interval_km = oil_interval_km or DEFAULT_OIL_INTERVAL_KM
        oil_status = "-"
        if interval_km and oil_change_km is not None and km is not None:
            remaining = interval_km - (km - oil_change_km)
            oil_status = "Geldi" if remaining <= 0 else f"{remaining} km"
        ttk.Label(info_row2, text=f"Periyot: {interval_km or '-'} km").pack(side=tk.LEFT, padx=12)
        ttk.Label(info_row2, text=f"Yag Durum: {oil_status}").pack(side=tk.LEFT, padx=12)
        info_row3 = ttk.Frame(info)
        info_row3.pack(fill=tk.X, pady=4)
        ttk.Label(info_row3, text=f"Muayene: {inspection_date or '-'}").pack(side=tk.LEFT, padx=6)
        ttk.Label(info_row3, text=f"Sigorta: {insurance_date or '-'}").pack(side=tk.LEFT, padx=12)
        ttk.Label(info_row3, text=f"Bakim: {maintenance_date or '-'}").pack(side=tk.LEFT, padx=12)
        if notes:
            info_row4 = ttk.Frame(info)
            info_row4.pack(fill=tk.X, pady=4)
            ttk.Label(info_row4, text=f"Not: {notes}").pack(side=tk.LEFT, padx=6)

        btn_row = ttk.Frame(detail_win)
        btn_row.pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(btn_row, text="Excel Arac Karti", command=lambda: self.export_vehicle_card(plate)).pack(
            side=tk.LEFT, padx=6
        )

        inspections = db.list_vehicle_inspections(vehicle_id=vehicle_id, region=self._view_region())
        if inspections:
            last_driver = inspections[0][4] or "-"
            last_date = inspections[0][5] or "-"
            info_row5 = ttk.Frame(info)
            info_row5.pack(fill=tk.X, pady=4)
            ttk.Label(info_row5, text=f"Son Surucu: {last_driver}").pack(side=tk.LEFT, padx=6)
            ttk.Label(info_row5, text=f"Son Kontrol: {last_date}").pack(side=tk.LEFT, padx=12)
        faults = db.list_vehicle_faults(vehicle_id=vehicle_id, region=self._view_region())
        services = db.list_vehicle_service_visits(vehicle_id=vehicle_id, region=self._view_region())

        inspect_frame = ttk.LabelFrame(detail_win, text="Kontroller", style="Section.TLabelframe")
        inspect_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        inspect_tree = ttk.Treeview(
            inspect_frame,
            columns=("date", "week", "driver", "km", "fault", "status", "service", "note"),
            show="headings",
            height=6,
        )
        inspect_tree.heading("date", text="Tarih")
        inspect_tree.heading("week", text="Hafta")
        inspect_tree.heading("driver", text="Surucu")
        inspect_tree.heading("km", text="KM")
        inspect_tree.heading("fault", text="Ariza")
        inspect_tree.heading("status", text="Durum")
        inspect_tree.heading("service", text="Sanayi")
        inspect_tree.heading("note", text="Not")
        inspect_tree.column("date", width=110)
        inspect_tree.column("week", width=110)
        inspect_tree.column("driver", width=160)
        inspect_tree.column("km", width=70)
        inspect_tree.column("fault", width=160)
        inspect_tree.column("status", width=90)
        inspect_tree.column("service", width=80)
        inspect_tree.column("note", width=180)
        i_xscroll = ttk.Scrollbar(inspect_frame, orient=tk.HORIZONTAL, command=inspect_tree.xview)
        i_yscroll = ttk.Scrollbar(inspect_frame, orient=tk.VERTICAL, command=inspect_tree.yview)
        inspect_tree.configure(xscrollcommand=i_xscroll.set, yscrollcommand=i_yscroll.set)
        inspect_frame.columnconfigure(0, weight=1)
        inspect_frame.rowconfigure(0, weight=1)
        inspect_tree.grid(row=0, column=0, sticky="nsew")
        i_yscroll.grid(row=0, column=1, sticky="ns")
        i_xscroll.grid(row=1, column=0, sticky="ew")

        for row in inspections[:20]:
            (
                _iid,
                _veh_id,
                _plate,
                _driver_id,
                driver_name,
                inspect_date,
                week_start,
                km_val,
                note_val,
                fault_id,
                fault_status,
                service_visit,
            ) = row
            fault_title = ""
            if fault_id:
                fault = db.get_vehicle_fault(fault_id)
                if fault:
                    fault_title = fault[2] or ""
            inspect_tree.insert(
                "",
                tk.END,
                values=(
                    inspect_date,
                    week_start,
                    driver_name or "-",
                    km_val or "-",
                    fault_title,
                    fault_status or "",
                    "Evet" if service_visit else "",
                    note_val or "",
                ),
            )

        fault_frame = ttk.LabelFrame(detail_win, text="Ariza Kayitlari", style="Section.TLabelframe")
        fault_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        fault_tree = ttk.Treeview(
            fault_frame,
            columns=("title", "status", "opened", "closed"),
            show="headings",
            height=5,
        )
        fault_tree.heading("title", text="Baslik")
        fault_tree.heading("status", text="Durum")
        fault_tree.heading("opened", text="Acilis")
        fault_tree.heading("closed", text="Kapanis")
        fault_tree.column("title", width=240)
        fault_tree.column("status", width=100)
        fault_tree.column("opened", width=120)
        fault_tree.column("closed", width=120)
        f_xscroll = ttk.Scrollbar(fault_frame, orient=tk.HORIZONTAL, command=fault_tree.xview)
        f_yscroll = ttk.Scrollbar(fault_frame, orient=tk.VERTICAL, command=fault_tree.yview)
        fault_tree.configure(xscrollcommand=f_xscroll.set, yscrollcommand=f_yscroll.set)
        fault_frame.columnconfigure(0, weight=1)
        fault_frame.rowconfigure(0, weight=1)
        fault_tree.grid(row=0, column=0, sticky="nsew")
        f_yscroll.grid(row=0, column=1, sticky="ns")
        f_xscroll.grid(row=1, column=0, sticky="ew")
        for fault in faults:
            _fid, _vid, _plate, title, _desc, opened_date, closed_date, status = fault
            fault_tree.insert("", tk.END, values=(title, status, opened_date or "", closed_date or ""))

        service_frame = ttk.LabelFrame(detail_win, text="Sanayi Kayitlari", style="Section.TLabelframe")
        service_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        service_tree = ttk.Treeview(
            service_frame,
            columns=("fault", "start", "end", "cost", "reason"),
            show="headings",
            height=5,
        )
        service_tree.heading("fault", text="Ariza")
        service_tree.heading("start", text="Gidis")
        service_tree.heading("end", text="Donus")
        service_tree.heading("cost", text="Masraf")
        service_tree.heading("reason", text="Neden")
        service_tree.column("fault", width=220)
        service_tree.column("start", width=120)
        service_tree.column("end", width=120)
        service_tree.column("cost", width=90)
        service_tree.column("reason", width=200)
        s_xscroll = ttk.Scrollbar(service_frame, orient=tk.HORIZONTAL, command=service_tree.xview)
        s_yscroll = ttk.Scrollbar(service_frame, orient=tk.VERTICAL, command=service_tree.yview)
        service_tree.configure(xscrollcommand=s_xscroll.set, yscrollcommand=s_yscroll.set)
        service_frame.columnconfigure(0, weight=1)
        service_frame.rowconfigure(0, weight=1)
        service_tree.grid(row=0, column=0, sticky="nsew")
        s_yscroll.grid(row=0, column=1, sticky="ns")
        s_xscroll.grid(row=1, column=0, sticky="ew")
        for visit in services:
            _sid, _vid, _plate, _fid, title, start_date, end_date, reason, cost, _notes = visit
            end_value = end_date or "Sanayide"
            cost_value = f"{cost:.2f}" if cost is not None else ""
            service_tree.insert("", tk.END, values=(title or "", start_date, end_value, cost_value, reason or ""))

        compare_frame = ttk.LabelFrame(detail_win, text="Haftalik Karsilastirma", style="Section.TLabelframe")
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        compare_tree = ttk.Treeview(
            compare_frame,
            columns=("item", "prev", "current", "change"),
            show="headings",
            height=6,
        )
        compare_tree.heading("item", text="Kontrol")
        compare_tree.heading("prev", text="Onceki Hafta")
        compare_tree.heading("current", text="Bu Hafta")
        compare_tree.heading("change", text="Durum")
        compare_tree.column("item", width=220)
        compare_tree.column("prev", width=120)
        compare_tree.column("current", width=120)
        compare_tree.column("change", width=160)
        c_xscroll = ttk.Scrollbar(compare_frame, orient=tk.HORIZONTAL, command=compare_tree.xview)
        c_yscroll = ttk.Scrollbar(compare_frame, orient=tk.VERTICAL, command=compare_tree.yview)
        compare_tree.configure(xscrollcommand=c_xscroll.set, yscrollcommand=c_yscroll.set)
        compare_frame.columnconfigure(0, weight=1)
        compare_frame.rowconfigure(0, weight=1)
        compare_tree.grid(row=0, column=0, sticky="nsew")
        c_yscroll.grid(row=0, column=1, sticky="ns")
        c_xscroll.grid(row=1, column=0, sticky="ew")

        if len(inspections) >= 2:
            current_inspection = inspections[0]
            previous_inspection = inspections[1]
            current_results = {
                row[0]: normalize_vehicle_status(row[1])
                for row in db.list_vehicle_inspection_results(current_inspection[0])
            }
            prev_results = {
                row[0]: normalize_vehicle_status(row[1])
                for row in db.list_vehicle_inspection_results(previous_inspection[0])
            }
            for item_key, label in VEHICLE_CHECKLIST:
                prev_status = prev_results.get(item_key, "-")
                curr_status = current_results.get(item_key, "-")
                if prev_status == curr_status:
                    change = "Ayni"
                elif prev_status == "Olumsuz" and curr_status == "Olumsuz":
                    change = "Tekrar eden sorun"
                elif curr_status == "Olumsuz" and prev_status != "Olumsuz":
                    change = "Kotulesti"
                elif prev_status == "Olumsuz" and curr_status != "Olumsuz":
                    change = "Iyilesti"
                else:
                    change = "Degisti"
                compare_tree.insert("", tk.END, values=(label, prev_status, curr_status, change))
            prev_fault_status = previous_inspection[10] or "-"
            curr_fault_status = current_inspection[10] or "-"
            if prev_fault_status or curr_fault_status:
                if prev_fault_status == curr_fault_status:
                    change = "Ayni"
                elif curr_fault_status == "Kapandi":
                    change = "Iyilesti"
                elif prev_fault_status == "Kapandi" and curr_fault_status != "Kapandi":
                    change = "Kotulesti"
                else:
                    change = "Degisti"
                compare_tree.insert("", tk.END, values=("Ariza Durumu", prev_fault_status, curr_fault_status, change))
            prev_service = "Evet" if previous_inspection[11] else "Hayir"
            curr_service = "Evet" if current_inspection[11] else "Hayir"
            change = "Ayni" if prev_service == curr_service else "Degisti"
            compare_tree.insert("", tk.END, values=("Sanayiye Gitti", prev_service, curr_service, change))

    def _open_driver_card(self, driver_id):
        driver = db.get_driver(driver_id)
        if not driver:
            messagebox.showwarning("Uyari", "Surucu bulunamadi.")
            return
        _did, name, license_class, license_expiry, phone, notes = driver
        inspections = db.list_driver_inspections(driver_id, region=self._view_region())

        detail_win = tk.Toplevel(self)
        detail_win.title(f"Surucu Karti - {name}")
        detail_win.geometry("960x680")

        info = ttk.LabelFrame(detail_win, text="Surucu Bilgisi", style="Section.TLabelframe")
        info.pack(fill=tk.X, padx=10, pady=8)
        info_row1 = ttk.Frame(info)
        info_row1.pack(fill=tk.X, pady=4)
        ttk.Label(info_row1, text=f"Ad Soyad: {name}").pack(side=tk.LEFT, padx=6)
        ttk.Label(info_row1, text=f"Ehliyet: {license_class or '-'}").pack(side=tk.LEFT, padx=12)
        ttk.Label(info_row1, text=f"Bitis: {license_expiry or '-'}").pack(side=tk.LEFT, padx=12)
        info_row2 = ttk.Frame(info)
        info_row2.pack(fill=tk.X, pady=4)
        ttk.Label(info_row2, text=f"Telefon: {phone or '-'}").pack(side=tk.LEFT, padx=6)
        if notes:
            ttk.Label(info_row2, text=f"Not: {notes}").pack(side=tk.LEFT, padx=12)

        vehicle_frame = ttk.LabelFrame(detail_win, text="Surucunun Araclari", style="Section.TLabelframe")
        vehicle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        vehicle_tree = ttk.Treeview(
            vehicle_frame,
            columns=("plate", "last_date", "count"),
            show="headings",
            height=5,
        )
        vehicle_tree.heading("plate", text="Plaka")
        vehicle_tree.heading("last_date", text="Son Kontrol")
        vehicle_tree.heading("count", text="Kontrol Sayisi")
        vehicle_tree.column("plate", width=140)
        vehicle_tree.column("last_date", width=140)
        vehicle_tree.column("count", width=120, anchor=tk.CENTER)
        v_xscroll = ttk.Scrollbar(vehicle_frame, orient=tk.HORIZONTAL, command=vehicle_tree.xview)
        v_yscroll = ttk.Scrollbar(vehicle_frame, orient=tk.VERTICAL, command=vehicle_tree.yview)
        vehicle_tree.configure(xscrollcommand=v_xscroll.set, yscrollcommand=v_yscroll.set)
        vehicle_frame.columnconfigure(0, weight=1)
        vehicle_frame.rowconfigure(0, weight=1)
        vehicle_tree.grid(row=0, column=0, sticky="nsew")
        v_yscroll.grid(row=0, column=1, sticky="ns")
        v_xscroll.grid(row=1, column=0, sticky="ew")

        vehicle_summary = {}
        for row in inspections:
            plate = row[2]
            inspect_date = row[5]
            entry = vehicle_summary.setdefault(plate, {"last": inspect_date, "count": 0})
            entry["count"] += 1
            if inspect_date and (not entry["last"] or inspect_date > entry["last"]):
                entry["last"] = inspect_date
        for plate, info_row in sorted(vehicle_summary.items()):
            vehicle_tree.insert("", tk.END, values=(plate, info_row["last"] or "-", info_row["count"]))

        history_frame = ttk.LabelFrame(detail_win, text="Kontrol Gecmisi", style="Section.TLabelframe")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        history_tree = ttk.Treeview(
            history_frame,
            columns=("date", "week", "plate", "km", "fault", "status", "service", "note"),
            show="headings",
            height=8,
        )
        history_tree.heading("date", text="Tarih")
        history_tree.heading("week", text="Hafta")
        history_tree.heading("plate", text="Plaka")
        history_tree.heading("km", text="KM")
        history_tree.heading("fault", text="Ariza")
        history_tree.heading("status", text="Durum")
        history_tree.heading("service", text="Sanayi")
        history_tree.heading("note", text="Not")
        history_tree.column("date", width=110)
        history_tree.column("week", width=110)
        history_tree.column("plate", width=120)
        history_tree.column("km", width=70)
        history_tree.column("fault", width=160)
        history_tree.column("status", width=90)
        history_tree.column("service", width=80)
        history_tree.column("note", width=200)
        h_xscroll = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=history_tree.xview)
        h_yscroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(xscrollcommand=h_xscroll.set, yscrollcommand=h_yscroll.set)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        history_tree.grid(row=0, column=0, sticky="nsew")
        h_yscroll.grid(row=0, column=1, sticky="ns")
        h_xscroll.grid(row=1, column=0, sticky="ew")

        for row in inspections[:50]:
            (
                _iid,
                _veh_id,
                plate,
                _driver_id,
                _driver_name,
                inspect_date,
                week_start,
                km_val,
                note_val,
                fault_id,
                fault_status,
                service_visit,
            ) = row
            fault_title = ""
            if fault_id:
                fault = db.get_vehicle_fault(fault_id)
                if fault:
                    fault_title = fault[2] or ""
            history_tree.insert(
                "",
                tk.END,
                values=(
                    inspect_date,
                    week_start,
                    plate,
                    km_val or "-",
                    fault_title,
                    fault_status or "",
                    "Evet" if service_visit else "",
                    note_val or "",
                ),
            )

    def _build_admin_tab(self):
        content = self.tab_admin_body

        filter_frame = ttk.LabelFrame(content, text="Filtre", style="Section.TLabelframe")
        filter_frame.pack(fill=tk.X, padx=6, pady=6)

        self.admin_employee_var = tk.StringVar(value="Tum Calisanlar")
        self.admin_department_var = tk.StringVar(value="Tum Departmanlar")
        self.admin_title_var = tk.StringVar(value="Tum Unvanlar")
        self.admin_start_var = tk.StringVar()
        self.admin_end_var = tk.StringVar()
        self.admin_search_var = tk.StringVar()

        ttk.Label(filter_frame, text="Calisan").pack(side=tk.LEFT, padx=(0, 6))
        self.admin_employee_combo = ttk.Combobox(
            filter_frame, textvariable=self.admin_employee_var, width=24, state="readonly"
        )
        self.admin_employee_combo.pack(side=tk.LEFT)
        ttk.Label(filter_frame, text="Departman").pack(side=tk.LEFT, padx=(12, 6))
        self.admin_department_combo = ttk.Combobox(
            filter_frame, textvariable=self.admin_department_var, width=18, state="readonly"
        )
        self.admin_department_combo.pack(side=tk.LEFT)
        ttk.Label(filter_frame, text="Unvan").pack(side=tk.LEFT, padx=(12, 6))
        self.admin_title_combo = ttk.Combobox(filter_frame, textvariable=self.admin_title_var, width=18, state="readonly")
        self.admin_title_combo.pack(side=tk.LEFT)

        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X, pady=6)
        start_frame, self.admin_start_entry = create_labeled_date(row2, "Baslangic", self.admin_start_var, 12)
        start_frame.pack(side=tk.LEFT, padx=6)
        end_frame, self.admin_end_entry = create_labeled_date(row2, "Bitis", self.admin_end_var, 12)
        end_frame.pack(side=tk.LEFT, padx=6)
        clear_date_entry(self.admin_start_entry)
        clear_date_entry(self.admin_end_entry)
        ttk.Label(row2, text="Ara").pack(side=tk.LEFT, padx=(12, 6))
        ttk.Entry(row2, textvariable=self.admin_search_var, width=24).pack(side=tk.LEFT)
        ttk.Button(row2, text="Guncelle", command=self.refresh_admin_summary).pack(side=tk.LEFT, padx=12)

        summary = ttk.LabelFrame(content, text="Ozet", style="Section.TLabelframe")
        summary.pack(fill=tk.X, padx=6, pady=6)

        self.admin_stats = {
            "total_records": tk.StringVar(value="0"),
            "total_employees": tk.StringVar(value="0"),
            "total_worked": tk.StringVar(value="0"),
            "total_overtime": tk.StringVar(value="0"),
            "total_night": tk.StringVar(value="0"),
            "total_overnight": tk.StringVar(value="0"),
            "total_special": tk.StringVar(value="0"),
            "avg_overtime": tk.StringVar(value="0"),
            "max_daily": tk.StringVar(value="0"),
        }

        row1 = ttk.Frame(summary)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Kayit").pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, textvariable=self.admin_stats["total_records"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Calisan").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.admin_stats["total_employees"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Toplam Calisilan").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.admin_stats["total_worked"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="Toplam Fazla Mesai").pack(side=tk.LEFT, padx=18)
        ttk.Label(row1, textvariable=self.admin_stats["total_overtime"]).pack(side=tk.LEFT, padx=6)

        row2 = ttk.Frame(summary)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="Toplam Gece").pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, textvariable=self.admin_stats["total_night"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="Geceye Tasan").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.admin_stats["total_overnight"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="Ozel Gun").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.admin_stats["total_special"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="Ortalama Fazla Mesai").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.admin_stats["avg_overtime"]).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="En Yuksek Gun").pack(side=tk.LEFT, padx=18)
        ttk.Label(row2, textvariable=self.admin_stats["max_daily"]).pack(side=tk.LEFT, padx=6)

        table_frame = ttk.LabelFrame(content, text="Calisan Ozeti", style="Section.TLabelframe")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.admin_tree = ttk.Treeview(
            table_frame,
            columns=("employee", "worked", "overtime", "night", "overnight", "special"),
            show="headings",
        )
        self.admin_tree.heading("employee", text="Calisan")
        self.admin_tree.heading("worked", text="Calisilan")
        self.admin_tree.heading("overtime", text="Fazla Mesai")
        self.admin_tree.heading("night", text="Gece")
        self.admin_tree.heading("overnight", text="Geceye Tasan")
        self.admin_tree.heading("special", text="Ozel Gun")
        self.admin_tree.column("employee", width=220)
        self.admin_tree.column("worked", width=90)
        self.admin_tree.column("overtime", width=90)
        self.admin_tree.column("night", width=90)
        self.admin_tree.column("overnight", width=110)
        self.admin_tree.column("special", width=90)
        admin_xscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.admin_tree.xview)
        admin_yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.admin_tree.yview)
        self.admin_tree.configure(xscrollcommand=admin_xscroll.set, yscrollcommand=admin_yscroll.set)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.admin_tree.grid(row=0, column=0, sticky="nsew")
        admin_yscroll.grid(row=0, column=1, sticky="ns")
        admin_xscroll.grid(row=1, column=0, sticky="ew")
        self.admin_tree.bind("<Button-3>", self.on_admin_right_click)
        self.admin_menu = tk.Menu(self, tearoff=0)
        self.admin_menu.add_command(label="Detay", command=self.show_admin_employee_detail)

        alert_frame = ttk.LabelFrame(content, text="Uyarilar", style="Section.TLabelframe")
        alert_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.admin_alert_tree = ttk.Treeview(
            alert_frame,
            columns=("date", "employee", "issue", "value"),
            show="headings",
            height=6,
        )
        self.admin_alert_tree.heading("date", text="Tarih")
        self.admin_alert_tree.heading("employee", text="Calisan")
        self.admin_alert_tree.heading("issue", text="Uyari")
        self.admin_alert_tree.heading("value", text="Deger")
        self.admin_alert_tree.column("date", width=100)
        self.admin_alert_tree.column("employee", width=220)
        self.admin_alert_tree.column("issue", width=180)
        self.admin_alert_tree.column("value", width=100)
        alert_xscroll = ttk.Scrollbar(alert_frame, orient=tk.HORIZONTAL, command=self.admin_alert_tree.xview)
        alert_yscroll = ttk.Scrollbar(alert_frame, orient=tk.VERTICAL, command=self.admin_alert_tree.yview)
        self.admin_alert_tree.configure(xscrollcommand=alert_xscroll.set, yscrollcommand=alert_yscroll.set)
        alert_frame.columnconfigure(0, weight=1)
        alert_frame.rowconfigure(0, weight=1)
        self.admin_alert_tree.grid(row=0, column=0, sticky="nsew")
        alert_yscroll.grid(row=0, column=1, sticky="ns")
        alert_xscroll.grid(row=1, column=0, sticky="ew")

        anomaly_frame = ttk.LabelFrame(content, text="Anomali Listesi", style="Section.TLabelframe")
        anomaly_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.admin_anomaly_tree = ttk.Treeview(
            anomaly_frame,
            columns=("employee", "period", "issue"),
            show="headings",
            height=6,
        )
        self.admin_anomaly_tree.heading("employee", text="Calisan")
        self.admin_anomaly_tree.heading("period", text="Donem")
        self.admin_anomaly_tree.heading("issue", text="Durum")
        self.admin_anomaly_tree.column("employee", width=220)
        self.admin_anomaly_tree.column("period", width=160)
        self.admin_anomaly_tree.column("issue", width=220)
        anom_xscroll = ttk.Scrollbar(anomaly_frame, orient=tk.HORIZONTAL, command=self.admin_anomaly_tree.xview)
        anom_yscroll = ttk.Scrollbar(anomaly_frame, orient=tk.VERTICAL, command=self.admin_anomaly_tree.yview)
        self.admin_anomaly_tree.configure(xscrollcommand=anom_xscroll.set, yscrollcommand=anom_yscroll.set)
        anomaly_frame.columnconfigure(0, weight=1)
        anomaly_frame.rowconfigure(0, weight=1)
        self.admin_anomaly_tree.grid(row=0, column=0, sticky="nsew")
        anom_yscroll.grid(row=0, column=1, sticky="ns")
        anom_xscroll.grid(row=1, column=0, sticky="ew")

        pack_frame = ttk.LabelFrame(content, text="Rapor Paketleme", style="Section.TLabelframe")
        pack_frame.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(pack_frame, text="Ay (YYYY-MM)").pack(side=tk.LEFT, padx=6)
        self.admin_month_var = tk.StringVar()
        ttk.Entry(pack_frame, textvariable=self.admin_month_var, width=10).pack(side=tk.LEFT)
        ttk.Button(pack_frame, text="Raporlari Zip Yap", command=self.package_monthly_reports).pack(
            side=tk.LEFT, padx=6
        )

        self.refresh_admin_summary()

    def select_logo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp"), ("All", "*.*")]
        )
        if path:
            self.logo_path_var.set(path)

    def save_settings(self):
        db.set_setting("company_name", self.company_name_var.get().strip())
        db.set_setting("report_title", self.report_title_var.get().strip())
        db.set_setting("weekday_hours", self.weekday_hours_var.get().strip())
        db.set_setting("saturday_start", self.sat_start_var.get().strip())
        db.set_setting("saturday_end", self.sat_end_var.get().strip())
        db.set_setting("logo_path", self.logo_path_var.get().strip())
        db.set_setting("sync_enabled", "1" if self.sync_enabled_var.get() else "0")
        db.set_setting("sync_url", self.sync_url_var.get().strip())
        db.set_setting("sync_token", self.sync_token_var.get().strip())
        if self.is_admin:
            db.set_setting("admin_entry_region", self.admin_region_var.get().strip() or "Ankara")
        self.settings = db.get_all_settings()
        messagebox.showinfo("Basarili", "Ayarlar kaydedildi.")
        self.trigger_sync("settings")


if __name__ == "__main__":
    ensure_app_dirs()
    db.init_db()
    app = PuantajApp()
    app.mainloop()
