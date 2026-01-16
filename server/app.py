import os
import sqlite3
import hashlib
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, request, abort, redirect, url_for, session


APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "puantaj.db")
API_KEY = os.environ.get("API_KEY", "")
LOCAL_TZ = timezone(timedelta(hours=3))
DEFAULT_USERS = [
    ("ankara1", "060106", "user", "Ankara"),
    ("izmir1", "350235", "user", "Izmir"),
    ("bursa1", "160316", "user", "Bursa"),
    ("istanbul1", "340434", "user", "Istanbul"),
    ("admin", "748774", "admin", "ALL"),
]
REGION_OPTIONS = ["Ankara", "Izmir", "Bursa", "Istanbul"]
DEFAULT_OIL_INTERVAL_KM = 14000
OIL_SOON_THRESHOLD_KM = 2000

VEHICLE_CHECKLIST = {
    "body_dent": "Govde ezik/cizik",
    "paint_damage": "Boya hasari",
    "interior_clean": "Ic temizligi",
    "smoke_smell": "Sigara kokusu",
    "tire_condition": "Lastik durumu",
    "lights": "Far/stop/sinyal",
    "glass": "Camlar",
    "warning_lamps": "Ikaz lambalari",
    "water_level": "Su seviyesi",
}


def current_month_range():
    today = datetime.now(LOCAL_TZ).date()
    start = today.replace(day=1)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    end = next_month - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rainstaff-secret")


def ensure_data_dir():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_exists():
    return os.path.isfile(DB_PATH)


def hash_password(password):
    text = f"rainstaff::{password}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_schema(conn):
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
    conn.executemany(
        "INSERT OR IGNORE INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?);",
        [(u, hash_password(p), r, reg) for u, p, r, reg in DEFAULT_USERS],
    )
    conn.commit()


def get_user_context():
    role = session.get("role")
    region = session.get("region")
    return role == "admin", region


@app.route("/health")
def health():
    return {"ok": True, "db": db_exists()}


@app.route("/sync", methods=["POST"])
def sync():
    if API_KEY:
        token = request.headers.get("X-API-KEY", "")
        if token != API_KEY:
            abort(401)
    if "db" not in request.files:
        abort(400)
    ensure_data_dir()
    file = request.files["db"]
    file.save(DB_PATH)
    with get_conn() as conn:
        ensure_schema(conn)
    return {"ok": True}


def is_authenticated():
    return bool(session.get("user"))


@app.before_request
def enforce_login():
    if request.path in ("/login", "/health", "/sync", "/static/style.css"):
        return
    if request.path.startswith("/static/"):
        return
    if not is_authenticated():
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        authenticated = False
        role = None
        region = None
        if db_exists():
            with get_conn() as conn:
                ensure_schema(conn)
                row = conn.execute(
                    "SELECT username, password_hash, role, region FROM users WHERE username = ?;",
                    (username,),
                ).fetchone()
            if row and row["password_hash"] == hash_password(password):
                authenticated = True
                role = row["role"]
                region = row["region"]
        if not authenticated and username == "admin" and password == "748774":
            authenticated = True
            role = "admin"
            region = "ALL"
        if authenticated:
            session["user"] = username
            session["role"] = role or "user"
            session["region"] = region or "Ankara"
            return redirect(url_for("dashboard"))
        error = "Kullanici adi veya sifre hatali."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/employee/<int:employee_id>")
def employee_detail(employee_id):
    if not db_exists():
        abort(404)
    with get_conn() as conn:
        ensure_schema(conn)
        is_admin, region = get_user_context()
        settings = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings;")}
        if is_admin:
            employee = conn.execute(
                "SELECT id, full_name, department, title, identity_no FROM employees WHERE id = ?;",
                (employee_id,),
            ).fetchone()
        else:
            employee = conn.execute(
                "SELECT id, full_name, department, title, identity_no FROM employees WHERE id = ? AND region = ?;",
                (employee_id, region),
            ).fetchone()
        if not employee:
            abort(404)
        if is_admin:
            rows = conn.execute(
                "SELECT work_date, start_time, end_time, break_minutes, is_special "
                "FROM timesheets WHERE employee_id = ? ORDER BY work_date DESC;",
                (employee_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT work_date, start_time, end_time, break_minutes, is_special "
                "FROM timesheets WHERE employee_id = ? AND region = ? ORDER BY work_date DESC;",
                (employee_id, region),
            ).fetchall()
    start_date = request.args.get("start", "").strip()
    end_date = request.args.get("end", "").strip()
    all_months = request.args.get("all", "").strip() == "1"
    try:
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        start_date = ""
        end_date = ""
    if not start_date or not end_date:
        start_date, end_date = current_month_range()
    filtered_rows = rows if all_months else filter_rows_by_date(rows, start_date, end_date)
    day_rows, totals = compute_employee_day_rows(filtered_rows, settings)
    return render_template(
        "employee.html",
        employee=employee,
        day_rows=day_rows,
        totals=totals,
        start_date=start_date,
        end_date=end_date,
        all_months=all_months,
    )


@app.route("/reports")
def reports():
    if not db_exists():
        abort(404)
    with get_conn() as conn:
        ensure_schema(conn)
        is_admin, region = get_user_context()
        if is_admin:
            rows = conn.execute(
                "SELECT v.plate, i.week_start, MAX(i.inspection_date) as last_date, COUNT(*) as cnt "
                "FROM vehicle_inspections i "
                "JOIN vehicles v ON v.id = i.vehicle_id "
                "GROUP BY v.plate, i.week_start "
                "ORDER BY i.week_start DESC, v.plate;"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT v.plate, i.week_start, MAX(i.inspection_date) as last_date, COUNT(*) as cnt "
                "FROM vehicle_inspections i "
                "JOIN vehicles v ON v.id = i.vehicle_id "
                "WHERE i.region = ? "
                "GROUP BY v.plate, i.week_start "
                "ORDER BY i.week_start DESC, v.plate;",
                (region,),
            ).fetchall()
    return render_template("reports.html", reports=rows)


@app.route("/reports/weekly/<plate>/<week_start>")
def weekly_report(plate, week_start):
    if not db_exists():
        abort(404)
    with get_conn() as conn:
        ensure_schema(conn)
        is_admin, region = get_user_context()
        if is_admin:
            vehicle = conn.execute(
                "SELECT id, plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date "
                "FROM vehicles WHERE plate = ?;",
                (plate,),
            ).fetchone()
        else:
            vehicle = conn.execute(
                "SELECT id, plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date "
                "FROM vehicles WHERE plate = ? AND region = ?;",
                (plate, region),
            ).fetchone()
        if not vehicle:
            abort(404)
        if is_admin:
            inspections = conn.execute(
                "SELECT i.id, i.inspection_date, i.week_start, d.full_name as driver, i.km, i.notes, "
                "i.fault_status, i.service_visit "
                "FROM vehicle_inspections i "
                "LEFT JOIN drivers d ON d.id = i.driver_id "
                "WHERE i.vehicle_id = ? AND i.week_start = ? "
                "ORDER BY i.inspection_date DESC;",
                (vehicle["id"], week_start),
            ).fetchall()
        else:
            inspections = conn.execute(
                "SELECT i.id, i.inspection_date, i.week_start, d.full_name as driver, i.km, i.notes, "
                "i.fault_status, i.service_visit "
                "FROM vehicle_inspections i "
                "LEFT JOIN drivers d ON d.id = i.driver_id "
                "WHERE i.vehicle_id = ? AND i.week_start = ? AND i.region = ? "
                "ORDER BY i.inspection_date DESC;",
                (vehicle["id"], week_start, region),
            ).fetchall()
        results = {}
        if inspections:
            latest_id = inspections[0]["id"]
            for row in conn.execute(
                "SELECT item_key, status, note FROM vehicle_inspection_results WHERE inspection_id = ?;",
                (latest_id,),
            ).fetchall():
                results[row["item_key"]] = {
                    "status": row["status"],
                    "note": row["note"],
                }
    return render_template(
        "report_detail.html",
        vehicle=vehicle,
        week_start=week_start,
        inspections=inspections,
        results=results,
        checklist=VEHICLE_CHECKLIST,
    )


@app.route("/alerts")
def alerts():
    if not db_exists():
        abort(404)
    with get_conn() as conn:
        ensure_schema(conn)
        is_admin, region = get_user_context()
        region_filter = None if is_admin else region
        weekly_alerts = build_weekly_alerts(conn, region_filter)
        if region_filter:
            open_faults = conn.execute(
                "SELECT v.plate, f.title, f.opened_date, f.status "
                "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                "WHERE f.region = ? "
                "ORDER BY f.opened_date DESC;",
                (region_filter,),
            ).fetchall()
            service_open = conn.execute(
                "SELECT v.plate, s.start_date, s.reason, s.cost "
                "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                "WHERE (s.end_date IS NULL OR s.end_date = '') AND s.region = ? "
                "ORDER BY s.start_date DESC;",
                (region_filter,),
            ).fetchall()
            service_history = conn.execute(
                "SELECT v.plate, s.start_date, s.end_date, s.reason, s.cost "
                "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                "WHERE s.region = ? "
                "ORDER BY s.start_date DESC LIMIT 50;",
                (region_filter,),
            ).fetchall()
        else:
            open_faults = conn.execute(
                "SELECT v.plate, f.title, f.opened_date, f.status "
                "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                "ORDER BY f.opened_date DESC;"
            ).fetchall()
            service_open = conn.execute(
                "SELECT v.plate, s.start_date, s.reason, s.cost "
                "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                "WHERE s.end_date IS NULL OR s.end_date = '' "
                "ORDER BY s.start_date DESC;"
            ).fetchall()
            service_history = conn.execute(
                "SELECT v.plate, s.start_date, s.end_date, s.reason, s.cost "
                "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                "ORDER BY s.start_date DESC LIMIT 50;"
            ).fetchall()
    total_alerts = len(weekly_alerts) + len(open_faults) + len(service_open)
    return render_template(
        "alerts.html",
        weekly_alerts=weekly_alerts,
        open_faults=open_faults,
        service_open=service_open,
        service_history=service_history,
        total_alerts=total_alerts,
    )


def safe_count(conn, query, params=None):
    try:
        return conn.execute(query, params or []).fetchone()[0]
    except sqlite3.Error:
        return 0


def parse_time_to_minutes(value):
    if not value:
        return None
    parts = value.split(":")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


def normalize_status(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def classify_status(value):
    status = normalize_status(value)
    if status in ("olumsuz", "issue", "bad", "negatif", "problem"):
        return "neg"
    if status in ("olumlu", "ok", "good", "pozitif"):
        return "pos"
    return "unk"


def display_status(value):
    status = normalize_status(value)
    if status in ("olumsuz", "issue", "bad", "negatif", "problem"):
        return "Olumsuz"
    if status in ("olumlu", "ok", "good", "pozitif"):
        return "Olumlu"
    if status == "":
        return "-"
    return "Bilinmiyor"


def get_latest_inspection_id(conn, vehicle_id, week_start):
    row = conn.execute(
        "SELECT id FROM vehicle_inspections "
        "WHERE vehicle_id = ? AND week_start = ? "
        "ORDER BY inspection_date DESC, id DESC LIMIT 1;",
        (vehicle_id, week_start),
    ).fetchone()
    return row["id"] if row else None


def get_inspection_results(conn, inspection_id):
    results = {}
    for row in conn.execute(
        "SELECT item_key, status FROM vehicle_inspection_results WHERE inspection_id = ?;",
        (inspection_id,),
    ).fetchall():
        results[row["item_key"]] = row["status"]
    return results


def build_weekly_alerts(conn, region=None):
    if region:
        rows = conn.execute(
            "SELECT v.id as vehicle_id, v.plate, i.week_start "
            "FROM vehicle_inspections i "
            "JOIN vehicles v ON v.id = i.vehicle_id "
            "WHERE i.region = ? "
            "GROUP BY v.id, v.plate, i.week_start "
            "ORDER BY i.week_start DESC;",
            (region,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT v.id as vehicle_id, v.plate, i.week_start "
            "FROM vehicle_inspections i "
            "JOIN vehicles v ON v.id = i.vehicle_id "
            "GROUP BY v.id, v.plate, i.week_start "
            "ORDER BY i.week_start DESC;"
        ).fetchall()
    vehicle_weeks = {}
    for row in rows:
        entry = vehicle_weeks.setdefault(
            row["vehicle_id"],
            {"plate": row["plate"], "weeks": []},
        )
        entry["weeks"].append(row["week_start"])

    alerts = []
    for vehicle_id, info in vehicle_weeks.items():
        weeks = sorted(set(info["weeks"]), reverse=True)
        if len(weeks) < 2:
            continue
        current_week, prev_week = weeks[0], weeks[1]
        current_id = get_latest_inspection_id(conn, vehicle_id, current_week)
        prev_id = get_latest_inspection_id(conn, vehicle_id, prev_week)
        if not current_id or not prev_id:
            continue
        current_results = get_inspection_results(conn, current_id)
        prev_results = get_inspection_results(conn, prev_id)
        for key, label in VEHICLE_CHECKLIST.items():
            current_status = current_results.get(key)
            prev_status = prev_results.get(key)
            if prev_status is None or current_status is None:
                continue
            current_class = classify_status(current_status)
            prev_class = classify_status(prev_status)
            if prev_class == "neg" and current_class == "neg":
                change = "Tekrar"
                level = "repeat"
            elif prev_class != "neg" and current_class == "neg":
                change = "Kotulesti"
                level = "bad"
            elif prev_class == "neg" and current_class != "neg":
                change = "Duzeldi"
                level = "good"
            elif prev_class != current_class:
                change = "Degisti"
                level = "info"
            else:
                continue
            alerts.append(
                {
                    "plate": info["plate"],
                    "week_start": current_week,
                    "item": label,
                    "prev_status": display_status(prev_status),
                    "current_status": display_status(current_status),
                    "change": change,
                    "level": level,
                }
            )
    return alerts


def compute_day_metrics(work_date, start_time, end_time, break_minutes, is_special, settings):
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    if start_min is None or end_min is None:
        return {
            "worked": 0.0,
            "overtime": 0.0,
            "night": 0.0,
            "special": 0.0,
            "overnight": 0.0,
            "scheduled": 0.0,
        }
    if end_min <= start_min:
        end_min += 1440
    break_min = break_minutes or 0
    worked_minutes = max(0, (end_min - start_min) - break_min)
    worked_hours = round(worked_minutes / 60.0, 2)

    night_minutes = 0
    night_windows = [(22 * 60, 24 * 60), (0, 6 * 60), (1440, 1440 + 6 * 60)]
    for n_start, n_end in night_windows:
        overlap_start = max(start_min, n_start)
        overlap_end = min(end_min, n_end)
        if overlap_end > overlap_start:
            night_minutes += overlap_end - overlap_start
    night_hours = round(night_minutes / 60.0, 2)

    overnight_minutes = max(0, end_min - 1440)
    overnight_hours = round(overnight_minutes / 60.0, 2)

    weekday_hours = float(settings.get("weekday_hours", "9") or 9)
    sat_start = parse_time_to_minutes(settings.get("saturday_start", "09:00")) or 540
    sat_end = parse_time_to_minutes(settings.get("saturday_end", "14:00")) or 840
    saturday_hours = max(0, (sat_end - sat_start) / 60.0)
    scheduled_hours = 0.0
    if not is_special:
        try:
            weekday = datetime.strptime(work_date, "%Y-%m-%d").weekday()
        except ValueError:
            weekday = 0
        if weekday == 5:
            scheduled_hours = saturday_hours
        elif weekday < 5:
            scheduled_hours = weekday_hours
        else:
            scheduled_hours = 0.0

    special_hours = worked_hours if is_special else 0.0
    overtime_hours = 0.0 if is_special else max(0.0, worked_hours - scheduled_hours)

    return {
        "worked": worked_hours,
        "overtime": round(overtime_hours, 2),
        "night": night_hours,
        "special": special_hours,
        "overnight": overnight_hours,
        "scheduled": round(scheduled_hours, 2),
    }


def compute_employee_day_rows(rows, settings):
    results = []
    totals = {"worked": 0.0, "overtime": 0.0, "night": 0.0, "special": 0.0}
    for row in rows:
        metrics = compute_day_metrics(
            row["work_date"],
            row["start_time"],
            row["end_time"],
            row["break_minutes"],
            row["is_special"],
            settings,
        )
        totals["worked"] += metrics["worked"]
        totals["overtime"] += metrics["overtime"]
        totals["night"] += metrics["night"]
        totals["special"] += metrics["special"]
        results.append(
            {
                "date": row["work_date"],
                "start": row["start_time"],
                "end": row["end_time"],
                "break": row["break_minutes"],
                "special": row["is_special"],
                "worked": metrics["worked"],
                "overtime": metrics["overtime"],
                "night": metrics["night"],
                "special_hours": metrics["special"],
            }
        )
    totals = {k: round(v, 2) for k, v in totals.items()}
    return results, totals


def filter_rows_by_date(rows, start_date, end_date):
    if not start_date or not end_date:
        return rows
    return [row for row in rows if start_date <= row["work_date"] <= end_date]


@app.route("/")
@app.route("/dashboard")
def dashboard():
    summary = {
        "employees": 0,
        "timesheets": 0,
        "vehicles": 0,
        "drivers": 0,
        "open_faults": 0,
        "service_open": 0,
        "service_total": 0,
        "worked_hours": 0.0,
        "overtime_hours": 0.0,
        "night_hours": 0.0,
        "special_hours": 0.0,
    }
    open_faults = []
    service_open = []
    top_faults = []
    employee_cards = []
    overtime_leaders = []
    timesheet_rows = []
    recent_timesheets = []
    vehicle_cards = []
    driver_cards = []
    recent_inspections = []
    weekly_inspections = []
    service_history = []
    driver_status = []
    monthly_summary = []
    daily_summary = []
    weekly_alerts = []
    alert_counts = {"total": 0, "bad": 0, "repeat": 0, "good": 0}
    top_overtime = None
    oil_alerts = []
    oil_counts = {"due": 0, "soon": 0}
    range_summary = {
        "worked": 0.0,
        "overtime": 0.0,
        "night": 0.0,
        "special": 0.0,
    }
    last_sync = None
    desktop_online = False
    is_admin = False
    region = "Ankara"
    start_date = request.args.get("start", "").strip()
    end_date = request.args.get("end", "").strip()
    all_months = request.args.get("all", "").strip() == "1"
    selected_region = request.args.get("region", "").strip()
    try:
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        start_date = ""
        end_date = ""
    if not start_date or not end_date:
        start_date, end_date = current_month_range()

    if db_exists():
        last_sync_dt = datetime.fromtimestamp(os.path.getmtime(DB_PATH), tz=LOCAL_TZ)
        last_sync = last_sync_dt.strftime("%Y-%m-%d %H:%M")
        desktop_online = (datetime.now(LOCAL_TZ) - last_sync_dt) <= timedelta(minutes=10)
        with get_conn() as conn:
            ensure_schema(conn)
            is_admin, region = get_user_context()
            region_filter = None if is_admin else region
            if is_admin:
                if selected_region in REGION_OPTIONS:
                    region_filter = selected_region
                elif selected_region in ("ALL", ""):
                    region_filter = None
            settings = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings;")}
            if region_filter:
                summary["employees"] = safe_count(
                    conn, "SELECT COUNT(*) FROM employees WHERE region = ?;", [region_filter]
                )
            else:
                summary["employees"] = safe_count(conn, "SELECT COUNT(*) FROM employees;")
            if region_filter:
                summary["timesheets"] = safe_count(
                    conn, "SELECT COUNT(*) FROM timesheets WHERE region = ?;", [region_filter]
                )
            else:
                summary["timesheets"] = safe_count(conn, "SELECT COUNT(*) FROM timesheets;")
            if region_filter:
                summary["vehicles"] = safe_count(
                    conn, "SELECT COUNT(*) FROM vehicles WHERE region = ?;", [region_filter]
                )
            else:
                summary["vehicles"] = safe_count(conn, "SELECT COUNT(*) FROM vehicles;")
            if region_filter:
                summary["drivers"] = safe_count(
                    conn, "SELECT COUNT(*) FROM drivers WHERE region = ?;", [region_filter]
                )
            else:
                summary["drivers"] = safe_count(conn, "SELECT COUNT(*) FROM drivers;")
            summary["open_faults"] = safe_count(
                conn,
                "SELECT COUNT(*) FROM vehicle_faults WHERE status = 'Acik' "
                + ("AND region = ?;" if region_filter else ";"),
                [region_filter] if region_filter else None,
            )
            if region_filter:
                summary["service_total"] = safe_count(
                    conn, "SELECT COUNT(*) FROM vehicle_service_visits WHERE region = ?;", [region_filter]
                )
            else:
                summary["service_total"] = safe_count(conn, "SELECT COUNT(*) FROM vehicle_service_visits;")
            summary["service_open"] = safe_count(
                conn,
                "SELECT COUNT(*) FROM vehicle_service_visits WHERE (end_date IS NULL OR end_date = '') "
                + ("AND region = ?;" if region_filter else ";"),
                [region_filter] if region_filter else None,
            )
            if region_filter:
                open_faults = conn.execute(
                    "SELECT v.plate, f.title, f.opened_date "
                    "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                    "WHERE f.status = 'Acik' AND f.region = ? "
                    "ORDER BY f.opened_date DESC LIMIT 10;",
                    (region_filter,),
                ).fetchall()
                service_open = conn.execute(
                    "SELECT v.plate, s.start_date, s.reason "
                    "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                    "WHERE (s.end_date IS NULL OR s.end_date = '') AND s.region = ? "
                    "ORDER BY s.start_date DESC LIMIT 10;",
                    (region_filter,),
                ).fetchall()
                top_faults = conn.execute(
                    "SELECT v.plate, COUNT(*) as cnt "
                    "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                    "WHERE f.region = ? "
                    "GROUP BY f.vehicle_id ORDER BY cnt DESC LIMIT 5;",
                    (region_filter,),
                ).fetchall()
                timesheet_rows = conn.execute(
                    "SELECT t.employee_id, e.full_name as name, t.work_date, t.start_time, t.end_time, "
                    "t.break_minutes, t.is_special "
                    "FROM timesheets t JOIN employees e ON e.id = t.employee_id "
                    "WHERE t.region = ?;",
                    (region_filter,),
                ).fetchall()
                vehicle_cards = conn.execute(
                    "SELECT v.plate, v.km, v.inspection_date, v.insurance_date, v.maintenance_date, "
                    "f.title as open_fault, s.start_date as in_service "
                    "FROM vehicles v "
                    "LEFT JOIN vehicle_faults f ON f.vehicle_id = v.id AND f.status = 'Acik' "
                    "LEFT JOIN vehicle_service_visits s ON s.vehicle_id = v.id AND (s.end_date IS NULL OR s.end_date = '') "
                    "WHERE v.region = ? "
                    "ORDER BY v.plate LIMIT 10;",
                    (region_filter,),
                ).fetchall()
                driver_cards = conn.execute(
                    "SELECT d.full_name as name, d.license_class, d.license_expiry, d.phone "
                    "FROM drivers d WHERE d.region = ? ORDER BY d.full_name LIMIT 10;",
                    (region_filter,),
                ).fetchall()
                recent_inspections = conn.execute(
                    "SELECT v.plate, i.inspection_date, i.week_start, d.full_name as driver, i.km, "
                    "i.fault_status, i.service_visit "
                    "FROM vehicle_inspections i "
                    "JOIN vehicles v ON v.id = i.vehicle_id "
                    "LEFT JOIN drivers d ON d.id = i.driver_id "
                    "WHERE i.region = ? "
                    "ORDER BY i.inspection_date DESC, i.id DESC LIMIT 10;",
                    (region_filter,),
                ).fetchall()
                weekly_inspections = conn.execute(
                    "SELECT v.plate, i.week_start, i.inspection_date, d.full_name as driver, i.km, "
                    "i.fault_status, i.service_visit "
                    "FROM vehicle_inspections i "
                    "JOIN vehicles v ON v.id = i.vehicle_id "
                    "LEFT JOIN drivers d ON d.id = i.driver_id "
                    "WHERE i.region = ? "
                    "ORDER BY i.week_start DESC, i.inspection_date DESC LIMIT 20;",
                    (region_filter,),
                ).fetchall()
                service_history = conn.execute(
                    "SELECT v.plate, s.start_date, s.end_date, s.reason, s.cost "
                    "FROM vehicle_service_visits s "
                    "JOIN vehicles v ON v.id = s.vehicle_id "
                    "WHERE s.region = ? "
                    "ORDER BY s.start_date DESC LIMIT 20;",
                    (region_filter,),
                ).fetchall()
                driver_status = conn.execute(
                    "SELECT d.full_name as name, d.license_class, d.license_expiry, d.phone "
                    "FROM drivers d WHERE d.region = ? ORDER BY d.full_name LIMIT 20;",
                    (region_filter,),
                ).fetchall()
                vehicles_for_oil = conn.execute(
                    "SELECT plate, km, oil_change_km, oil_interval_km "
                    "FROM vehicles WHERE region = ?;",
                    (region_filter,),
                ).fetchall()
            else:
                open_faults = conn.execute(
                    "SELECT v.plate, f.title, f.opened_date "
                    "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                    "WHERE f.status = 'Acik' ORDER BY f.opened_date DESC LIMIT 10;"
                ).fetchall()
                service_open = conn.execute(
                    "SELECT v.plate, s.start_date, s.reason "
                    "FROM vehicle_service_visits s JOIN vehicles v ON v.id = s.vehicle_id "
                    "WHERE s.end_date IS NULL OR s.end_date = '' "
                    "ORDER BY s.start_date DESC LIMIT 10;"
                ).fetchall()
                top_faults = conn.execute(
                    "SELECT v.plate, COUNT(*) as cnt "
                    "FROM vehicle_faults f JOIN vehicles v ON v.id = f.vehicle_id "
                    "GROUP BY f.vehicle_id ORDER BY cnt DESC LIMIT 5;"
                ).fetchall()
                timesheet_rows = conn.execute(
                    "SELECT t.employee_id, e.full_name as name, t.work_date, t.start_time, t.end_time, "
                    "t.break_minutes, t.is_special "
                    "FROM timesheets t JOIN employees e ON e.id = t.employee_id;"
                ).fetchall()
                vehicle_cards = conn.execute(
                    "SELECT v.plate, v.km, v.inspection_date, v.insurance_date, v.maintenance_date, "
                    "f.title as open_fault, s.start_date as in_service "
                    "FROM vehicles v "
                    "LEFT JOIN vehicle_faults f ON f.vehicle_id = v.id AND f.status = 'Acik' "
                    "LEFT JOIN vehicle_service_visits s ON s.vehicle_id = v.id AND (s.end_date IS NULL OR s.end_date = '') "
                    "ORDER BY v.plate LIMIT 10;"
                ).fetchall()
                driver_cards = conn.execute(
                    "SELECT d.full_name as name, d.license_class, d.license_expiry, d.phone "
                    "FROM drivers d ORDER BY d.full_name LIMIT 10;"
                ).fetchall()
                recent_inspections = conn.execute(
                    "SELECT v.plate, i.inspection_date, i.week_start, d.full_name as driver, i.km, "
                    "i.fault_status, i.service_visit "
                    "FROM vehicle_inspections i "
                    "JOIN vehicles v ON v.id = i.vehicle_id "
                    "LEFT JOIN drivers d ON d.id = i.driver_id "
                    "ORDER BY i.inspection_date DESC, i.id DESC LIMIT 10;"
                ).fetchall()
                weekly_inspections = conn.execute(
                    "SELECT v.plate, i.week_start, i.inspection_date, d.full_name as driver, i.km, "
                    "i.fault_status, i.service_visit "
                    "FROM vehicle_inspections i "
                    "JOIN vehicles v ON v.id = i.vehicle_id "
                    "LEFT JOIN drivers d ON d.id = i.driver_id "
                    "ORDER BY i.week_start DESC, i.inspection_date DESC LIMIT 20;"
                ).fetchall()
                service_history = conn.execute(
                    "SELECT v.plate, s.start_date, s.end_date, s.reason, s.cost "
                    "FROM vehicle_service_visits s "
                    "JOIN vehicles v ON v.id = s.vehicle_id "
                    "ORDER BY s.start_date DESC LIMIT 20;"
                ).fetchall()
                driver_status = conn.execute(
                    "SELECT d.full_name as name, d.license_class, d.license_expiry, d.phone "
                    "FROM drivers d ORDER BY d.full_name LIMIT 20;"
                ).fetchall()
                vehicles_for_oil = conn.execute(
                    "SELECT plate, km, oil_change_km, oil_interval_km FROM vehicles;"
                ).fetchall()
            weekly_alerts = build_weekly_alerts(conn, region_filter)
            alert_counts = {
                "total": len(weekly_alerts),
                "bad": sum(1 for row in weekly_alerts if row["level"] == "bad"),
                "repeat": sum(1 for row in weekly_alerts if row["level"] == "repeat"),
                "good": sum(1 for row in weekly_alerts if row["level"] == "good"),
            }
            alert_counts["urgent"] = alert_counts["bad"] + alert_counts["repeat"]

            emp_totals = {}
            range_totals = {}
            filtered_rows = (
                timesheet_rows
                if all_months
                else [row for row in timesheet_rows if start_date <= row["work_date"] <= end_date]
            )
            for row in filtered_rows:
                metrics = compute_day_metrics(
                    row["work_date"],
                    row["start_time"],
                    row["end_time"],
                    row["break_minutes"],
                    row["is_special"],
                    settings,
                )
                summary["worked_hours"] += metrics["worked"]
                summary["overtime_hours"] += metrics["overtime"]
                summary["night_hours"] += metrics["night"]
                summary["special_hours"] += metrics["special"]
                emp = emp_totals.setdefault(
                    row["employee_id"],
                    {
                        "id": row["employee_id"],
                        "name": row["name"],
                        "days": 0,
                        "worked": 0.0,
                        "overtime": 0.0,
                        "night": 0.0,
                        "special": 0.0,
                    },
                )
                emp["days"] += 1
                emp["worked"] += metrics["worked"]
                emp["overtime"] += metrics["overtime"]
                emp["night"] += metrics["night"]
                emp["special"] += metrics["special"]
                day = range_totals.setdefault(
                    row["work_date"],
                    {"worked": 0.0, "overtime": 0.0, "night": 0.0, "special": 0.0},
                )
                day["worked"] += metrics["worked"]
                day["overtime"] += metrics["overtime"]
                day["night"] += metrics["night"]
                day["special"] += metrics["special"]
                range_summary["worked"] += metrics["worked"]
                range_summary["overtime"] += metrics["overtime"]
                range_summary["night"] += metrics["night"]
                range_summary["special"] += metrics["special"]

            summary["worked_hours"] = round(summary["worked_hours"], 2)
            summary["overtime_hours"] = round(summary["overtime_hours"], 2)
            summary["night_hours"] = round(summary["night_hours"], 2)
            summary["special_hours"] = round(summary["special_hours"], 2)

            employee_cards = sorted(emp_totals.values(), key=lambda x: x["worked"], reverse=True)[:10]
            overtime_leaders = sorted(emp_totals.values(), key=lambda x: x["overtime"], reverse=True)[:10]
            if overtime_leaders:
                top_overtime = overtime_leaders[0]
            recent_timesheets = sorted(filtered_rows, key=lambda x: x["work_date"], reverse=True)[:15]

            for row in vehicles_for_oil:
                km = row["km"]
                oil_km = row["oil_change_km"]
                interval_km = row["oil_interval_km"] or DEFAULT_OIL_INTERVAL_KM
                if km is None or oil_km is None or interval_km <= 0:
                    continue
                remaining = interval_km - (km - oil_km)
                if remaining <= 0:
                    oil_alerts.append(
                        {"plate": row["plate"], "remaining": remaining, "status": "Geldi"}
                    )
                elif remaining <= OIL_SOON_THRESHOLD_KM:
                    oil_alerts.append(
                        {"plate": row["plate"], "remaining": remaining, "status": "Yaklasti"}
                    )
            oil_counts["due"] = sum(1 for row in oil_alerts if row["status"] == "Geldi")
            oil_counts["soon"] = sum(1 for row in oil_alerts if row["status"] == "Yaklasti")

            monthly_totals = {}
            for row in timesheet_rows:
                month_key = row["work_date"][:7]
                metrics = compute_day_metrics(
                    row["work_date"],
                    row["start_time"],
                    row["end_time"],
                    row["break_minutes"],
                    row["is_special"],
                    settings,
                )
                month = monthly_totals.setdefault(
                    month_key,
                    {"worked": 0.0, "overtime": 0.0, "night": 0.0, "special": 0.0},
                )
                month["worked"] += metrics["worked"]
                month["overtime"] += metrics["overtime"]
                month["night"] += metrics["night"]
                month["special"] += metrics["special"]
            monthly_summary = [
                {
                    "month": key,
                    "worked": round(val["worked"], 2),
                    "overtime": round(val["overtime"], 2),
                    "night": round(val["night"], 2),
                    "special": round(val["special"], 2),
                }
                for key, val in sorted(monthly_totals.items(), reverse=True)[:12]
            ]
            daily_summary = [
                {
                    "date": key,
                    "worked": round(val["worked"], 2),
                    "overtime": round(val["overtime"], 2),
                    "night": round(val["night"], 2),
                    "special": round(val["special"], 2),
                }
                for key, val in sorted(range_totals.items(), reverse=True)
            ]
            range_summary = {k: round(v, 2) for k, v in range_summary.items()}
    else:
        desktop_online = False

    return render_template(
        "dashboard.html",
        summary=summary,
        open_faults=open_faults,
        service_open=service_open,
        top_faults=top_faults,
        employee_cards=employee_cards,
        overtime_leaders=overtime_leaders,
        recent_timesheets=recent_timesheets,
        vehicle_cards=vehicle_cards,
        driver_cards=driver_cards,
        recent_inspections=recent_inspections,
        weekly_inspections=weekly_inspections,
        service_history=service_history,
        driver_status=driver_status,
        monthly_summary=monthly_summary,
        daily_summary=daily_summary,
        weekly_alerts=weekly_alerts,
        alert_counts=alert_counts,
        top_overtime=top_overtime,
        oil_alerts=sorted(oil_alerts, key=lambda x: x["remaining"]),
        oil_counts=oil_counts,
        range_summary=range_summary,
        start_date=start_date,
        end_date=end_date,
        all_months=all_months,
        desktop_online=desktop_online,
        last_sync=last_sync,
        is_admin=is_admin,
        regions=REGION_OPTIONS,
        selected_region=selected_region if is_admin else region,
    )


if __name__ == "__main__":
    ensure_data_dir()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
