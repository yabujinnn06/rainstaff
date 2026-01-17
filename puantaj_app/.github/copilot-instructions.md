# Rainstaff Copilot Instructions

## Architecture Overview

**Rainstaff** is a dual-tier timesheet and vehicle management system:
- **Desktop App** (`app.py`): Tkinter UI for data entry; SQLite DB local storage
- **Web Dashboard** (`server/app.py`): Flask read-only admin panel synced from desktop
- **Desktop → Server**: DB file uploaded after each CRUD action via POST `/sync`

### Data Flow
1. Desktop writes to local SQLite (`%APPDATA%\Rainstaff\data\puantaj.db`)
2. After any change, desktop uploads DB to server
3. Dashboard reads server DB on page load (always latest)
4. No bidirectional sync; desktop is source of truth

## Key Components

### Desktop (Tkinter)
- **app.py**: Main UI (~4800 lines); login → region-based tabs (Employees, Timesheets, Vehicles, Drivers, Settings, Logs)
- **db.py**: SQLite schema + migrations; context manager `get_conn()` for transactions
- **calc.py**: Hour calculations (normal, overtime, night, overnight, special days)
- **report.py**: Excel generation via openpyxl; styling with headers/borders

### Database Tables
- `employees`, `timesheets` (puantaj core)
- `shift_templates` (standard work hours: weekday hours, Saturday start/end)
- `vehicles`, `drivers` (fleet management)
- `vehicle_inspections`, `vehicle_inspection_results` (weekly checklist: 9 items)
- `vehicle_faults`, `vehicle_service_visits` (maintenance tracking)
- `users` (role-based auth: admin/user; region scoped)
- `settings` (app config: company name, sync URL, logo path, etc.)

### Critical Patterns

#### Date/Time Normalization
```python
# calc.py: Flexible input parsing
def parse_date(value):  # Accepts "2026-01-05" or "05.01.2026"
def parse_time(value)   # Accepts "09:30" or Excel time float

# app.py: Normalize before DB insert
normalize_date(value)   # Always returns "YYYY-MM-DD"
normalize_time(value)   # Always returns "HH:MM"
```

#### Context Manager for DB Transactions
```python
# db.py usage pattern
@contextmanager
def get_conn():  # Autocommit on success, rollback on error
    
# Always use: with get_conn() as conn: ...
```

#### Region-Based Access Control
```python
# app.py: Non-admin users see only their region
if not is_admin:
    WHERE region = current_region
    
# Admin: Can set "Kayit Bolge" (entry) and "Goruntuleme Bolge" (view)
# Default users: ankara1, izmir1, bursa1, istanbul1 (user role)
#               admin (role=admin, region=ALL)
```

## Common Workflows

### Adding a New Timesheet Entry
1. User selects employee, date, start/end time
2. `normalize_date()` and `normalize_time()` validate inputs
3. `calc_day_hours()` computes hours (normal, overtime, night, special day)
4. Insert into `timesheets` table
5. Desktop uploads DB to server via sync

### Vehicle Inspection Report
1. Weekly checklist against 9-item `VEHICLE_CHECKLIST` (Turkish labels)
2. Compare current week vs prior week for alerts
3. Results stored in `vehicle_inspection_results` + `vehicle_inspections`
4. Export as Excel report

### Dashboard Data Query
```python
# server/app.py: Always guard empty/missing values
weekly_report = get_week_report(plate, week_start)  # May return None
if not weekly_report:  # Handle gracefully
    return render_template('404.html')
```

## Sync and Deployment

### Desktop Sync Logic
- Setting: `sync_enabled` (0/1), `sync_url`, `sync_token`
- After each CRUD: POST DB file to `sync_url/sync` with `sync_token` header
- Desktop logs sync success/failure

### Render Deployment
- Push to `server/` → GitHub webhook triggers Render build
- Render: `pip install -r requirements.txt` → `gunicorn app:app`
- UptimeRobot pings `/health` every 5 min (anti-sleep)

## Testing & Debugging

### Key Files for Investigation
- Desktop errors → `%APPDATA%\Rainstaff\logs\rainstaff.log`
- UI flows: Trace `app.py` tab methods (e.g., `refresh_timesheets_tab()`)
- DB changes: Check `db.py` migrations in `init_db()`
- Report issues: Verify `report.py` column order matches schema

### Common Pitfalls
- **Date Format**: Always normalize inputs; schema uses ISO `YYYY-MM-DD`
- **Region Filter**: Guard against None/missing `region` column in old data
- **Tkinter Layout**: Never mix grid/pack in same container
- **Sync Failure**: Check API_KEY, sync_url connectivity, DB file size
- **Dashboard 500**: Inspect Render logs; likely missing imports or DB schema mismatch

## Project-Specific Conventions

- **Language**: Turkish UI labels (employee names, field names, error messages in Turkish)
- **Dates**: ISO format in DB; display in Turkish settings (YYYY-MM-DD or DD.MM.YYYY)
- **Regions**: Hard-coded list: Ankara, Izmir, Bursa, Istanbul + "ALL" for admin
- **Excel Export**: 16-column fixed layout; headers + data rows with borders/fills
- **Logging**: All CRUD actions logged with user/region context

## Before You Edit

1. **Schema Changes**: Update `db.py:init_db()` AND verify migrations won't break existing DBs
2. **New UI Tab**: Add both Desktop (app.py) and Dashboard (if read-only needed) routes
3. **Hour Calculations**: Test edge cases in `calc.py` (overnight hours, special days)
4. **Sync Changes**: Ensure backward compatibility; test desktop→server roundtrip
5. **Regional Data**: Filter by region consistently; no hardcoded region assumptions

---

For detailed architecture, see `../README.md` in parent directory.
