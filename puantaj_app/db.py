import os
import sqlite3
import shutil
import zipfile
import hashlib
from datetime import datetime, timedelta
from contextlib import contextmanager

APP_NAME = "Rainstaff"
LOCAL_DB_DIR = os.path.join(os.path.dirname(__file__), "data")

if os.name == 'nt':  # Windows
    APPDATA_DIR = os.path.join(os.environ.get("APPDATA", LOCAL_DB_DIR), APP_NAME, "data")
    DB_DIR = APPDATA_DIR
else:  # Linux / Server (Render)
    # Check for Render persistent disk at /data
    if os.path.exists("/data"):
        DB_DIR = "/data"
    else:
        # Fallback for local testing or if /data is not mounted
        DB_DIR = LOCAL_DB_DIR

DB_PATH = os.path.join(DB_DIR, "puantaj.db")
BACKUP_DIR = os.path.join(os.path.dirname(DB_DIR), "backups")
BACKUP_MARKER = os.path.join(BACKUP_DIR, "last_backup.txt")
EXPORT_DIR = os.path.join(os.path.dirname(DB_DIR), "exports")

DEFAULT_SETTINGS = {
    "company_name": "",
    "report_title": "Rainstaff Puantaj ve Mesai Raporu",
    "weekday_hours": "9",
    "saturday_start": "09:00",
    "saturday_end": "14:00",
    "logo_path": "",
    "sync_enabled": "0",
    "sync_url": "",
    "sync_token": "",
    "admin_entry_region": "Ankara",
}

DEFAULT_USERS = [
    ("ankara1", "060106", "user", "Ankara"),
    ("izmir1", "350235", "user", "Izmir"),
    ("bursa1", "160316", "user", "Bursa"),
    ("istanbul1", "340434", "user", "Istanbul"),
    ("admin", "748774", "admin", "ALL"),
]


def ensure_db_dir():
    if not os.path.isdir(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)


def _migrate_local_db():
    local_db = os.path.join(LOCAL_DB_DIR, "puantaj.db")
    if os.path.isfile(local_db) and not os.path.isfile(DB_PATH):
        os.makedirs(DB_DIR, exist_ok=True)
        shutil.copy2(local_db, DB_PATH)


def _backup_db_if_needed():
    if not os.path.isfile(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    last_time = None
    if os.path.isfile(BACKUP_MARKER):
        try:
            with open(BACKUP_MARKER, "r", encoding="ascii") as handle:
                last_time = datetime.fromisoformat(handle.read().strip())
        except Exception:
            last_time = None
    now = datetime.now()
    if last_time and now - last_time < timedelta(days=1):
        return
    stamp = now.strftime("%Y%m%d_%H%M%S")
    create_backup(os.path.join(BACKUP_DIR, f"puantaj_{stamp}.db"))
    with open(BACKUP_MARKER, "w", encoding="ascii") as handle:
        handle.write(now.isoformat())


def create_backup(dest_path=None):
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError("Database not found")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not dest_path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(BACKUP_DIR, f"puantaj_{stamp}.db")
    shutil.copy2(DB_PATH, dest_path)
    return dest_path


def restore_backup(src_path):
    if not os.path.isfile(src_path):
        raise FileNotFoundError("Backup not found")
    ensure_db_dir()
    if os.path.isfile(DB_PATH):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recovery_path = os.path.join(BACKUP_DIR, f"pre_restore_{stamp}.db")
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(DB_PATH, recovery_path)
    shutil.copy2(src_path, DB_PATH)


def export_data_zip(dest_path=None):
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError("Database not found")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    if not dest_path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(EXPORT_DIR, f"rainstaff_export_{stamp}.zip")
    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_PATH, arcname="puantaj.db")
    return dest_path


def import_data_zip(src_path):
    if not os.path.isfile(src_path):
        raise FileNotFoundError("Export file not found")
    ensure_db_dir()
    with zipfile.ZipFile(src_path, "r") as zf:
        names = zf.namelist()
        if "puantaj.db" not in names:
            raise ValueError("Export zip missing puantaj.db")
        temp_path = os.path.join(DB_DIR, "_import_tmp.db")
        with zf.open("puantaj.db") as src, open(temp_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
    restore_backup(temp_path)
    if os.path.isfile(temp_path):
        os.remove(temp_path)


@contextmanager
def get_conn():
    """SQLite baglantrsi, otomatik commit ve rollback ile."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")  # 30 saniye
        yield conn
        conn.commit()  # Basarili islemler commit edilir
    except Exception:
        conn.rollback()  # Hata durumunda geri al
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                identity_no TEXT,
                department TEXT,
                title TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                work_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_minutes INTEGER NOT NULL DEFAULT 0,
                is_special INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                employee TEXT,
                start_date TEXT,
                end_date TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shift_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_minutes INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT NOT NULL UNIQUE,
                brand TEXT,
                model TEXT,
                year TEXT,
                km INTEGER,
                inspection_date TEXT,
                insurance_date TEXT,
                maintenance_date TEXT,
                oil_change_date TEXT,
                oil_change_km INTEGER,
                oil_interval_km INTEGER,
                notes TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                license_class TEXT,
                license_expiry TEXT,
                phone TEXT,
                notes TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                region TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_faults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                opened_date TEXT,
                closed_date TEXT,
                status TEXT DEFAULT 'Acik',
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                driver_id INTEGER,
                inspection_date TEXT NOT NULL,
                week_start TEXT NOT NULL,
                km INTEGER,
                notes TEXT,
                fault_id INTEGER,
                fault_status TEXT,
                service_visit INTEGER DEFAULT 0,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
                FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE SET NULL,
                FOREIGN KEY (fault_id) REFERENCES vehicle_faults (id) ON DELETE SET NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_service_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                fault_id INTEGER,
                start_date TEXT NOT NULL,
                end_date TEXT,
                reason TEXT,
                cost REAL,
                notes TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
                FOREIGN KEY (fault_id) REFERENCES vehicle_faults (id) ON DELETE SET NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_inspection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                item_key TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (inspection_id) REFERENCES vehicle_inspections (id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stok_kod TEXT,
                stok_adi TEXT,
                seri_no TEXT NOT NULL UNIQUE,
                durum TEXT,
                tarih TEXT,
                girdi_yapan TEXT,
                bolge TEXT NOT NULL,
                adet INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Delete tracking table for multi-PC sync (23 Ocak 2026)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                deleted_at TEXT NOT NULL,
                deleted_by TEXT
            );
            """
        )
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);",
                (key, value),
            )
        cur = conn.execute("SELECT COUNT(*) FROM shift_templates;")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO shift_templates (name, start_time, end_time, break_minutes) VALUES (?, ?, ?, ?);",
                [
                    ("Hafta Ici 09-18", "09:00", "18:00", 60),
                    ("Cumartesi 09-14", "09:00", "14:00", 0),
                ],
            )
        _ensure_timesheet_columns(conn)
        _ensure_vehicle_columns(conn)
        _ensure_region_columns(conn)
        _ensure_deleted_records_table(conn)
        _seed_default_users(conn)
        conn.commit()
    _backup_db_if_needed()


def _ensure_deleted_records_table(conn):
    """Ensure deleted_records table exists for sync delete tracking."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS deleted_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            deleted_at TEXT NOT NULL,
            deleted_by TEXT
        );
        """
    )


def _ensure_timesheet_columns(conn):
    cur = conn.execute("PRAGMA table_info(timesheets);")
    columns = {row[1] for row in cur.fetchall()}
    if "is_special" not in columns:
        conn.execute("ALTER TABLE timesheets ADD COLUMN is_special INTEGER NOT NULL DEFAULT 0;")
        conn.commit()


def _ensure_vehicle_columns(conn):
    cur = conn.execute("PRAGMA table_info(vehicles);")
    columns = {row[1] for row in cur.fetchall()}
    if "oil_change_date" not in columns:
        conn.execute("ALTER TABLE vehicles ADD COLUMN oil_change_date TEXT;")
    if "oil_change_km" not in columns:
        conn.execute("ALTER TABLE vehicles ADD COLUMN oil_change_km INTEGER;")
    if "oil_interval_km" not in columns:
        conn.execute("ALTER TABLE vehicles ADD COLUMN oil_interval_km INTEGER;")
    cur = conn.execute("PRAGMA table_info(vehicle_inspections);")
    columns = {row[1] for row in cur.fetchall()}
    if "km" not in columns:
        conn.execute("ALTER TABLE vehicle_inspections ADD COLUMN km INTEGER;")
    if "fault_id" not in columns:
        conn.execute("ALTER TABLE vehicle_inspections ADD COLUMN fault_id INTEGER;")
    if "fault_status" not in columns:
        conn.execute("ALTER TABLE vehicle_inspections ADD COLUMN fault_status TEXT;")
    if "service_visit" not in columns:
        conn.execute("ALTER TABLE vehicle_inspections ADD COLUMN service_visit INTEGER DEFAULT 0;")


def _ensure_region_columns(conn):
    tables = [
        "employees",
        "timesheets",
        "vehicles",
        "drivers",
        "vehicle_faults",
        "vehicle_inspections",
        "vehicle_service_visits",
    ]
    for table in tables:
        cur = conn.execute(f"PRAGMA table_info({table});")
        columns = {row[1] for row in cur.fetchall()}
        if "region" not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN region TEXT DEFAULT 'Ankara';")
        conn.execute(
            f"UPDATE {table} SET region = 'Ankara' WHERE region IS NULL OR TRIM(region) = '';"
        )


def _seed_default_users(conn):
    conn.executemany(
        "INSERT OR IGNORE INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?);",
        [(u, hash_password(p), r, reg) for u, p, r, reg in DEFAULT_USERS],
    )


def hash_password(password):
    text = f"rainstaff::{password}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_user(username, password):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT username, password_hash, role, region FROM users WHERE username = ?;",
            (username,),
        )
        row = cur.fetchone()
    if not row:
        return None
    if row[1] != hash_password(password):
        return None
    return {"username": row[0], "role": row[2], "region": row[3]}

def get_setting(key):
    with get_conn() as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,))
        row = cur.fetchone()
        return row[0] if row else ""


def set_setting(key, value):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
            (key, value),
        )
        conn.commit()


def get_all_settings():
    with get_conn() as conn:
        cur = conn.execute("SELECT key, value FROM settings;")
        return {row[0]: row[1] for row in cur.fetchall()}


def add_employee(full_name, identity_no, department, title, region="Ankara"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO employees (full_name, identity_no, department, title, region) VALUES (?, ?, ?, ?, ?);",
            (full_name, identity_no, department, title, region),
        )
        conn.commit()
        return cur.lastrowid


def update_employee(employee_id, full_name, identity_no, department, title, region=None):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE employees SET full_name = ?, identity_no = ?, department = ?, title = ?, region = ? "
                "WHERE id = ?;",
                (full_name, identity_no, department, title, region, employee_id),
            )
        else:
            conn.execute(
                "UPDATE employees SET full_name = ?, identity_no = ?, department = ?, title = ? WHERE id = ?;",
                (full_name, identity_no, department, title, employee_id),
            )
        conn.commit()


def delete_employee(employee_id, deleted_by=None):
    with get_conn() as conn:
        # Track deletion for sync
        conn.execute(
            "INSERT INTO deleted_records (table_name, record_id, deleted_at, deleted_by) VALUES (?, ?, ?, ?);",
            ("employees", employee_id, datetime.now().isoformat(), deleted_by),
        )
        conn.execute("DELETE FROM employees WHERE id = ?;", (employee_id,))
        conn.commit()


def list_employees(region=None):
    with get_conn() as conn:
        query = "SELECT id, full_name, identity_no, department, title, region FROM employees"
        params = []
        if region and region != "ALL":
            query += " WHERE region = ?"
            params.append(region)
        query += " ORDER BY full_name;"
        cur = conn.execute(query, params)
        return cur.fetchall()


def add_timesheet(employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region="Ankara"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO timesheets (employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region),
        )
        conn.commit()
        return cur.lastrowid


def update_timesheet(ts_id, employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region=None):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE timesheets SET employee_id = ?, work_date = ?, start_time = ?, end_time = ?, "
                "break_minutes = ?, is_special = ?, notes = ?, region = ? WHERE id = ?;",
                (employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region, ts_id),
            )
        else:
            conn.execute(
                "UPDATE timesheets SET employee_id = ?, work_date = ?, start_time = ?, end_time = ?, "
                "break_minutes = ?, is_special = ?, notes = ? WHERE id = ?;",
                (employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, ts_id),
            )
        conn.commit()


def delete_timesheet(ts_id, deleted_by=None):
    with get_conn() as conn:
        # Track deletion for sync
        conn.execute(
            "INSERT INTO deleted_records (table_name, record_id, deleted_at, deleted_by) VALUES (?, ?, ?, ?);",
            ("timesheets", ts_id, datetime.now().isoformat(), deleted_by),
        )
        conn.execute("DELETE FROM timesheets WHERE id = ?;", (ts_id,))
        conn.commit()


def list_timesheets(employee_id=None, start_date=None, end_date=None, region=None):
    query = (
        "SELECT t.id, t.employee_id, e.full_name, t.work_date, t.start_time, t.end_time, "
        "t.break_minutes, t.is_special, t.notes, t.region "
        "FROM timesheets t JOIN employees e ON e.id = t.employee_id"
    )
    conditions = []
    params = []
    if employee_id:
        conditions.append("t.employee_id = ?")
        params.append(employee_id)
    if region and region != "ALL":
        conditions.append("t.region = ?")
        params.append(region)
    if start_date:
        conditions.append("t.work_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("t.work_date <= ?")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY t.work_date, e.full_name;"

    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def list_shift_templates():
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, name, start_time, end_time, break_minutes FROM shift_templates ORDER BY name;"
        )
        return cur.fetchall()


def add_report_log(file_path, created_at, employee, start_date, end_date):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO reports (file_path, created_at, employee, start_date, end_date) "
            "VALUES (?, ?, ?, ?, ?);",
            (file_path, created_at, employee, start_date, end_date),
        )
        conn.commit()


def list_report_logs():
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, file_path, created_at, employee, start_date, end_date "
            "FROM reports ORDER BY created_at DESC;"
        )
        return cur.fetchall()


def add_vehicle(
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
    region="Ankara",
):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vehicles (plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date, "
            "oil_change_date, oil_change_km, oil_interval_km, notes, region) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
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
                region,
            ),
        )
        conn.commit()
        return cur.lastrowid


def update_vehicle(
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
    notes,
    region=None,
):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE vehicles SET plate = ?, brand = ?, model = ?, year = ?, km = ?, inspection_date = ?, "
                "insurance_date = ?, maintenance_date = ?, oil_change_date = ?, oil_change_km = ?, oil_interval_km = ?, "
                "notes = ?, region = ? WHERE id = ?;",
                (
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
                    region,
                    vehicle_id,
                ),
            )
        else:
            conn.execute(
                "UPDATE vehicles SET plate = ?, brand = ?, model = ?, year = ?, km = ?, inspection_date = ?, "
                "insurance_date = ?, maintenance_date = ?, oil_change_date = ?, oil_change_km = ?, oil_interval_km = ?, "
                "notes = ? WHERE id = ?;",
                (
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
                    vehicle_id,
                ),
            )
        conn.commit()


def delete_vehicle(vehicle_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM vehicles WHERE id = ?;", (vehicle_id,))
        conn.commit()


def list_vehicles(region=None):
    with get_conn() as conn:
        query = (
            "SELECT id, plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date, "
            "oil_change_date, oil_change_km, oil_interval_km, notes, region "
            "FROM vehicles"
        )
        params = []
        if region and region != "ALL":
            query += " WHERE region = ?"
            params.append(region)
        query += " ORDER BY plate;"
        cur = conn.execute(query, params)
        return cur.fetchall()


def get_vehicle(vehicle_id):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date, "
            "oil_change_date, oil_change_km, oil_interval_km, notes, region FROM vehicles WHERE id = ?;",
            (vehicle_id,),
        )
        return cur.fetchone()


def add_driver(full_name, license_class, license_expiry, phone, notes, region="Ankara"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO drivers (full_name, license_class, license_expiry, phone, notes, region) "
            "VALUES (?, ?, ?, ?, ?, ?);",
            (full_name, license_class, license_expiry, phone, notes, region),
        )
        conn.commit()
        return cur.lastrowid


def update_driver(driver_id, full_name, license_class, license_expiry, phone, notes, region=None):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE drivers SET full_name = ?, license_class = ?, license_expiry = ?, phone = ?, notes = ?, "
                "region = ? WHERE id = ?;",
                (full_name, license_class, license_expiry, phone, notes, region, driver_id),
            )
        else:
            conn.execute(
                "UPDATE drivers SET full_name = ?, license_class = ?, license_expiry = ?, phone = ?, notes = ? "
                "WHERE id = ?;",
                (full_name, license_class, license_expiry, phone, notes, driver_id),
            )
        conn.commit()


def delete_driver(driver_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM drivers WHERE id = ?;", (driver_id,))
        conn.commit()


def list_drivers(region=None):
    with get_conn() as conn:
        query = "SELECT id, full_name, license_class, license_expiry, phone, notes, region FROM drivers"
        params = []
        if region and region != "ALL":
            query += " WHERE region = ?"
            params.append(region)
        query += " ORDER BY full_name;"
        cur = conn.execute(query, params)
        return cur.fetchall()


def add_vehicle_inspection(
    vehicle_id,
    driver_id,
    inspection_date,
    week_start,
    km,
    notes,
    fault_id=None,
    fault_status=None,
    service_visit=0,
    region="Ankara",
):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vehicle_inspections (vehicle_id, driver_id, inspection_date, week_start, km, notes, "
            "fault_id, fault_status, service_visit, region) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                vehicle_id,
                driver_id,
                inspection_date,
                week_start,
                km,
                notes,
                fault_id,
                fault_status,
                service_visit,
                region,
            ),
        )
        conn.commit()
        return cur.lastrowid


def add_vehicle_inspection_result(inspection_id, item_key, status, note):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO vehicle_inspection_results (inspection_id, item_key, status, note) VALUES (?, ?, ?, ?);",
            (inspection_id, item_key, status, note),
        )
        conn.commit()


def list_vehicle_inspections(vehicle_id=None, week_start=None, region=None):
    query = (
        "SELECT i.id, i.vehicle_id, v.plate, i.driver_id, d.full_name, i.inspection_date, i.week_start, i.km, "
        "i.notes, i.fault_id, i.fault_status, i.service_visit "
        "FROM vehicle_inspections i "
        "JOIN vehicles v ON v.id = i.vehicle_id "
        "LEFT JOIN drivers d ON d.id = i.driver_id"
    )
    conditions = []
    params = []
    if vehicle_id:
        conditions.append("i.vehicle_id = ?")
        params.append(vehicle_id)
    if week_start:
        conditions.append("i.week_start = ?")
        params.append(week_start)
    if region and region != "ALL":
        conditions.append("i.region = ?")
        params.append(region)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY i.inspection_date DESC;"
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def get_driver(driver_id):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, full_name, license_class, license_expiry, phone, notes FROM drivers WHERE id = ?;",
            (driver_id,),
        )
        return cur.fetchone()


def list_driver_inspections(driver_id, region=None):
    query = (
        "SELECT i.id, i.vehicle_id, v.plate, i.driver_id, d.full_name, i.inspection_date, i.week_start, i.km, "
        "i.notes, i.fault_id, i.fault_status, i.service_visit "
        "FROM vehicle_inspections i "
        "JOIN vehicles v ON v.id = i.vehicle_id "
        "LEFT JOIN drivers d ON d.id = i.driver_id "
        "WHERE i.driver_id = ?"
    )
    params = [driver_id]
    if region and region != "ALL":
        query += " AND i.region = ?"
        params.append(region)
    query += " ORDER BY i.inspection_date DESC;"
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def list_vehicle_inspection_results(inspection_id):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT item_key, status, note FROM vehicle_inspection_results WHERE inspection_id = ?;",
            (inspection_id,),
        )
        return cur.fetchall()


def add_vehicle_fault(vehicle_id, title, description, opened_date, closed_date, status, region="Ankara"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vehicle_faults (vehicle_id, title, description, opened_date, closed_date, status, region) "
            "VALUES (?, ?, ?, ?, ?, ?, ?);",
            (vehicle_id, title, description, opened_date, closed_date, status, region),
        )
        conn.commit()
        return cur.lastrowid


def update_vehicle_fault(fault_id, vehicle_id, title, description, opened_date, closed_date, status, region=None):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE vehicle_faults SET vehicle_id = ?, title = ?, description = ?, opened_date = ?, "
                "closed_date = ?, status = ?, region = ? WHERE id = ?;",
                (vehicle_id, title, description, opened_date, closed_date, status, region, fault_id),
            )
        else:
            conn.execute(
                "UPDATE vehicle_faults SET vehicle_id = ?, title = ?, description = ?, opened_date = ?, "
                "closed_date = ?, status = ? WHERE id = ?;",
                (vehicle_id, title, description, opened_date, closed_date, status, fault_id),
            )
        conn.commit()


def delete_vehicle_fault(fault_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM vehicle_faults WHERE id = ?;", (fault_id,))
        conn.commit()


def get_vehicle_fault(fault_id):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, vehicle_id, title, description, opened_date, closed_date, status "
            "FROM vehicle_faults WHERE id = ?;",
            (fault_id,),
        )
        return cur.fetchone()


def list_vehicle_faults(vehicle_id=None, status=None, region=None):
    query = (
        "SELECT f.id, f.vehicle_id, v.plate, f.title, f.description, f.opened_date, "
        "f.closed_date, f.status, f.region "
        "FROM vehicle_faults f "
        "JOIN vehicles v ON v.id = f.vehicle_id"
    )
    conditions = []
    params = []
    if vehicle_id:
        conditions.append("f.vehicle_id = ?")
        params.append(vehicle_id)
    if status:
        conditions.append("f.status = ?")
        params.append(status)
    if region and region != "ALL":
        conditions.append("f.region = ?")
        params.append(region)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY f.opened_date DESC, f.id DESC;"
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def list_open_vehicle_faults(vehicle_id=None, region=None):
    return list_vehicle_faults(vehicle_id=vehicle_id, status="Acik", region=region)


def add_vehicle_service_visit(vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region="Ankara"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vehicle_service_visits (vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region),
        )
        conn.commit()
        return cur.lastrowid


def update_vehicle_service_visit(visit_id, vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region=None):
    with get_conn() as conn:
        if region:
            conn.execute(
                "UPDATE vehicle_service_visits SET vehicle_id = ?, fault_id = ?, start_date = ?, end_date = ?, "
                "reason = ?, cost = ?, notes = ?, region = ? WHERE id = ?;",
                (vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region, visit_id),
            )
        else:
            conn.execute(
                "UPDATE vehicle_service_visits SET vehicle_id = ?, fault_id = ?, start_date = ?, end_date = ?, "
                "reason = ?, cost = ?, notes = ? WHERE id = ?;",
                (vehicle_id, fault_id, start_date, end_date, reason, cost, notes, visit_id),
            )
        conn.commit()


def delete_vehicle_service_visit(visit_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM vehicle_service_visits WHERE id = ?;", (visit_id,))
        conn.commit()


def get_vehicle_service_visit(visit_id):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, vehicle_id, fault_id, start_date, end_date, reason, cost, notes "
            "FROM vehicle_service_visits WHERE id = ?;",
            (visit_id,),
        )
        return cur.fetchone()


def list_vehicle_service_visits(vehicle_id=None, fault_id=None, start_date=None, end_date=None, region=None):
    query = (
        "SELECT s.id, s.vehicle_id, v.plate, s.fault_id, f.title, s.start_date, s.end_date, s.reason, s.cost, s.notes, s.region "
        "FROM vehicle_service_visits s "
        "JOIN vehicles v ON v.id = s.vehicle_id "
        "LEFT JOIN vehicle_faults f ON f.id = s.fault_id"
    )
    conditions = []
    params = []
    if vehicle_id:
        conditions.append("s.vehicle_id = ?")
        params.append(vehicle_id)
    if fault_id:
        conditions.append("s.fault_id = ?")
        params.append(fault_id)
    if region and region != "ALL":
        conditions.append("s.region = ?")
        params.append(region)
    if start_date:
        conditions.append("s.start_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("s.start_date <= ?")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY s.start_date DESC, s.id DESC;"
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def upsert_shift_template(name, start_time, end_time, break_minutes):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO shift_templates (name, start_time, end_time, break_minutes) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET start_time = excluded.start_time, "
            "end_time = excluded.end_time, break_minutes = excluded.break_minutes;",
            (name, start_time, end_time, break_minutes),
        )
        conn.commit()


def delete_shift_template(template_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM shift_templates WHERE id = ?;", (template_id,))
        conn.commit()


# ============================================================================
# SYNC FUNCTIONS - Multi-region database synchronization (Added 19 Ocak 2026)
# ============================================================================

def sync_with_server(sync_url, api_key, region):
    """
    Upload local database to server and download merged version
    
    Args:
        sync_url: Server URL (e.g., https://rainstaff.onrender.com)
        api_key: API authentication token
        region: Current region (Ankara, Istanbul, etc)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import requests
    
    try:
        # Step 1: Upload local DB to server
        with open(DB_PATH, "rb") as f:
            files = {"db": (f"puantaj_{region}.db", f, "application/octet-stream")}
            headers = {
                "X-API-KEY": api_key,
                "X-Region": region,
                "X-Reason": "periodic_sync"
            }
            upload_url = sync_url.rstrip("/") + "/sync"
            
            resp = requests.post(upload_url, headers=headers, files=files, timeout=15)
            
            if resp.status_code != 200:
                return False, f"Upload failed: HTTP {resp.status_code}"
        
        # Step 2: Download merged database from server
        headers = {"X-API-KEY": api_key}
        download_url = sync_url.rstrip("/") + "/sync/download"
        
        resp = requests.get(download_url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            return False, f"Download failed: HTTP {resp.status_code}"
        
        # Step 3: Backup current local database
        backup_path = DB_PATH + ".sync_backup"
        if os.path.isfile(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
        
        # Step 4: Write downloaded database as new local DB
        with open(DB_PATH, "wb") as f:
            f.write(resp.content)
        
        return True, "Sync completed successfully"
    
    except requests.exceptions.Timeout:
        return False, "Timeout: Server took too long to respond"
    except requests.exceptions.ConnectionError:
        return False, "Connection error: Cannot reach server"
    except Exception as e:
        return False, f"Sync error: {str(e)}"


def get_sync_status(sync_url, api_key):
    """
    Get server sync status and statistics
    
    Args:
        sync_url: Server URL
        api_key: API authentication token
    
    Returns:
        dict: Server status information or None if error
    """
    import requests
    
    try:
        headers = {"X-API-KEY": api_key}
        url = sync_url.rstrip("/") + "/sync/status"
        
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    
    except Exception:
        return None

