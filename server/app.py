import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, abort, redirect, url_for, session


APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "puantaj.db")
API_KEY = os.environ.get("API_KEY", "")

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
    return {"ok": True}


def is_authenticated():
    return session.get("user") == "admin"


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
        if username == "admin" and password == "748774":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        error = "Kullanici adi veya sifre hatali."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def safe_count(conn, query):
    try:
        return conn.execute(query).fetchone()[0]
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
    last_sync = None

    if db_exists():
        last_sync = datetime.fromtimestamp(os.path.getmtime(DB_PATH)).strftime("%Y-%m-%d %H:%M")
        with get_conn() as conn:
            settings = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings;")}
            summary["employees"] = safe_count(conn, "SELECT COUNT(*) FROM employees;")
            summary["timesheets"] = safe_count(conn, "SELECT COUNT(*) FROM timesheets;")
            summary["vehicles"] = safe_count(conn, "SELECT COUNT(*) FROM vehicles;")
            summary["drivers"] = safe_count(conn, "SELECT COUNT(*) FROM drivers;")
            summary["open_faults"] = safe_count(
                conn, "SELECT COUNT(*) FROM vehicle_faults WHERE status = 'Acik';"
            )
            summary["service_total"] = safe_count(conn, "SELECT COUNT(*) FROM vehicle_service_visits;")
            summary["service_open"] = safe_count(
                conn, "SELECT COUNT(*) FROM vehicle_service_visits WHERE end_date IS NULL OR end_date = '';"
            )
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

            emp_totals = {}
            for row in timesheet_rows:
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

            summary["worked_hours"] = round(summary["worked_hours"], 2)
            summary["overtime_hours"] = round(summary["overtime_hours"], 2)
            summary["night_hours"] = round(summary["night_hours"], 2)
            summary["special_hours"] = round(summary["special_hours"], 2)

            employee_cards = sorted(emp_totals.values(), key=lambda x: x["worked"], reverse=True)[:10]
            overtime_leaders = sorted(emp_totals.values(), key=lambda x: x["overtime"], reverse=True)[:10]
            recent_timesheets = sorted(timesheet_rows, key=lambda x: x["work_date"], reverse=True)[:15]

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
        last_sync=last_sync,
    )


if __name__ == "__main__":
    ensure_data_dir()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
