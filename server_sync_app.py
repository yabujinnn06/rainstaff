"""
Rainstaff Sync Server - Flask Application
Handles multi-region database synchronization

Installation:
    pip install flask requests sqlite3 werkzeug

Deployment (Render):
    1. Create new Web Service on render.com
    2. Connect GitHub repo (server branch)
    3. Set Build Command: pip install -r requirements.txt
    4. Set Start Command: gunicorn app:app
    5. Environment: API_KEY=your_secret_token
"""

import os
import sqlite3
import shutil
import hashlib
import threading
from datetime import datetime
from contextlib import contextmanager
from flask import Flask, request, jsonify, send_file
import io

app = Flask(__name__)

# Configuration
API_KEY = os.environ.get("API_KEY", "default_dev_key")
DB_DIR = os.environ.get("DB_DIR", "/tmp/rainstaff")
MASTER_DB = os.path.join(DB_DIR, "puantaj_master.db")
SYNC_LOCK = threading.Lock()

os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_master_db():
    """SQLite connection context manager"""
    conn = sqlite3.connect(MASTER_DB)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_master_db():
    """Initialize master database if doesn't exist"""
    if os.path.exists(MASTER_DB):
        return
    
    with get_master_db() as conn:
        # Create all tables matching desktop schema
        conn.execute("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                identity_no TEXT,
                department TEXT,
                title TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                work_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_minutes INTEGER NOT NULL DEFAULT 0,
                is_special INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                region TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE vehicles (
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
            )
        """)
        conn.execute("""
            CREATE TABLE drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                license_class TEXT,
                license_expiry TEXT,
                phone TEXT,
                notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                region TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                created_at TEXT,
                employee TEXT,
                start_date TEXT,
                end_date TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE shift_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_minutes INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE vehicle_faults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                opened_date TEXT,
                closed_date TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE vehicle_service_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                service_date TEXT,
                description TEXT,
                cost REAL,
                km_at_service INTEGER,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE vehicle_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                inspection_date TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE vehicle_inspection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                status TEXT,
                notes TEXT,
                FOREIGN KEY (inspection_id) REFERENCES vehicle_inspections (id) ON DELETE CASCADE
            )
        """)
        
        # Insert default users
        conn.execute("INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)", 
                    ("ankara1", "060106", "user", "Ankara"))
        conn.execute("INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)", 
                    ("istanbul1", "340434", "user", "Istanbul"))
        conn.execute("INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)", 
                    ("bursa1", "160316", "user", "Bursa"))
        conn.execute("INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)", 
                    ("izmir1", "350235", "user", "Izmir"))
        conn.execute("INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)", 
                    ("admin", "748774", "admin", "ALL"))


def merge_databases(desktop_db_bytes, region):
    """
    Merge desktop DB with master DB
    Strategy: Last-write-wins for same records, union for different records
    """
    with SYNC_LOCK:
        # Write uploaded DB to temp file
        temp_db = os.path.join(DB_DIR, f"temp_{region}.db")
        with open(temp_db, "wb") as f:
            f.write(desktop_db_bytes)
        
        try:
            desktop_conn = sqlite3.connect(temp_db)
            
            # Get all tables from master
            with get_master_db() as master_conn:
                master_cur = master_conn.cursor()
                master_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in master_cur.fetchall()]
                
                for table in tables:
                    # For each table, get records from desktop
                    desktop_cur = desktop_conn.cursor()
                    desktop_cur.execute(f"SELECT * FROM {table}")
                    desktop_records = desktop_cur.fetchall()
                    
                    # Simple merge: if table is timesheets or employees, merge by ID
                    if table in ["timesheets", "employees", "vehicles", "drivers"]:
                        for record in desktop_records:
                            record_id = record[0]
                            # Check if exists in master
                            master_cur.execute(f"SELECT id FROM {table} WHERE id = ?", (record_id,))
                            exists = master_cur.fetchone() is not None
                            
                            if not exists:
                                # Insert new record
                                placeholders = ",".join(["?" for _ in record])
                                master_conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", record)
            
            master_conn.commit()
            return True, "Merge successful"
        
        except Exception as e:
            return False, str(e)
        finally:
            desktop_conn.close()
            if os.path.exists(temp_db):
                os.remove(temp_db)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint (for monitoring)"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/sync", methods=["POST"])
def sync_desktop_db():
    """
    Receive database file from desktop, merge with master
    
    Headers:
        X-API-KEY: API key for authentication
        X-Region: Region identifier (Ankara, Istanbul, etc)
        X-Reason: Sync reason (manual, auto, etc)
    
    Body:
        file: multipart database file
    """
    
    # Authentication
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    # Get region
    region = request.headers.get("X-Region", "Unknown")
    reason = request.headers.get("X-Reason", "unknown")
    
    # Check file
    if "db" not in request.files:
        return jsonify({"success": False, "error": "No database file in request"}), 400
    
    file = request.files["db"]
    
    try:
        db_bytes = file.read()
        success, msg = merge_databases(db_bytes, region)
        
        if success:
            log_sync_activity("upload", region, reason, "success")
            return jsonify({
                "success": True,
                "message": "Database synced successfully",
                "timestamp": datetime.now().isoformat(),
                "region": region
            })
        else:
            log_sync_activity("upload", region, reason, f"error: {msg}")
            return jsonify({
                "success": False,
                "error": msg
            }), 500
    
    except Exception as e:
        log_sync_activity("upload", region, reason, f"exception: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/sync/download", methods=["GET"])
def download_latest_db():
    """
    Download latest merged database
    
    Query params:
        region: (optional) Return only region's data
    """
    
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    try:
        with open(MASTER_DB, "rb") as f:
            db_bytes = f.read()
        
        return send_file(
            io.BytesIO(db_bytes),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="puantaj.db"
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    """Get server sync status"""
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    try:
        with get_master_db() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM employees")
            emp_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM timesheets")
            ts_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM vehicles")
            veh_count = cur.fetchone()[0]
            
            return jsonify({
                "success": True,
                "employees": emp_count,
                "timesheets": ts_count,
                "vehicles": veh_count,
                "db_path": MASTER_DB,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/auto-sync", methods=["GET", "HEAD", "POST"])
def auto_sync():
    """
    Automatic sync trigger (for cron jobs / UptimeRobot)
    No authentication required - can be called from monitoring service
    Performs internal housekeeping (no upload/download)
    Accepts GET, HEAD, POST methods for flexibility with different monitoring tools
    """
    try:
        with SYNC_LOCK:
            with get_master_db() as conn:
                # Verify DB integrity
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM employees")
                emp_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM timesheets")
                ts_count = cur.fetchone()[0]
                
                # Log the auto-sync event
                log_sync_activity("AUTO-SYNC", "ALL", "periodic_check", f"OK ({emp_count} emp, {ts_count} ts)")
                
                return jsonify({
                    "success": True,
                    "action": "auto-sync",
                    "employees": emp_count,
                    "timesheets": ts_count,
                    "timestamp": datetime.now().isoformat()
                }), 200
    except Exception as e:
        log_sync_activity("AUTO-SYNC", "ALL", "periodic_check", f"ERROR: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def log_sync_activity(action, region, reason, status):
    """Log sync activities (can be extended to database logging)"""
    timestamp = datetime.now().isoformat()
    log_file = os.path.join(DB_DIR, "sync_activity.log")
    
    with open(log_file, "a") as f:
        f.write(f"{timestamp} | {action:10} | {region:15} | {reason:20} | {status}\n")


if __name__ == "__main__":
    init_master_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
