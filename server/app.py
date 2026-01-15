import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, abort


APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "puantaj.db")
API_KEY = os.environ.get("API_KEY", "")

app = Flask(__name__)


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


def safe_count(conn, query):
    try:
        return conn.execute(query).fetchone()[0]
    except sqlite3.Error:
        return 0


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
    }
    open_faults = []
    service_open = []
    top_faults = []
    last_sync = None

    if db_exists():
        last_sync = datetime.fromtimestamp(os.path.getmtime(DB_PATH)).strftime("%Y-%m-%d %H:%M")
        with get_conn() as conn:
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

    return render_template(
        "dashboard.html",
        summary=summary,
        open_faults=open_faults,
        service_open=service_open,
        top_faults=top_faults,
        last_sync=last_sync,
    )


if __name__ == "__main__":
    ensure_data_dir()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
