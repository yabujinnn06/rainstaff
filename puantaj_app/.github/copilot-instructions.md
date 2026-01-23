
# Rainstaff Copilot Instructions

## Architecture Overview

Rainstaff is a dual-tier timesheet and vehicle management system:
- **Desktop App** (`app.py`): Tkinter (Turkish UI) for all CRUD/data entry, local SQLite DB (`%APPDATA%/Rainstaff/data/puantaj.db`).
- **Web Dashboard** (`server/app.py`): Flask, read-only admin panel, always reflects latest uploaded DB.
- **Sync**: Desktop POSTs DB to `/sync` after every CRUD; server never writes, only serves latest DB.

### Data Flow
1. Desktop writes to local SQLite (`%APPDATA%/Rainstaff/data/puantaj.db`).
2. After any change, desktop uploads DB to server (`/sync`).
3. Dashboard reads server DB on every page load (no caching).
4. No bidirectional sync: desktop is always source of truth.


## Key Components & Files

### Desktop (Tkinter)
- **app.py**: Main UI (region-based tabs: Employees, Timesheets, Vehicles, Drivers, Settings, Logs)
- **db.py**: SQLite schema, migrations, and all DB access (always use `get_conn()` context manager)
- **calc.py**: Hour calculations (normal, overtime, night, overnight, special days)
- **report.py**: Excel export (16-column fixed layout, Turkish headers, openpyxl)

### Web Dashboard (Flask)
- **server/app.py**: Read-only admin panel, sync endpoints, region/user auth
- **server/templates/**: Jinja2 templates for dashboard views

### Database Tables (see `db.py:init_db()` for schema)
- `employees`, `timesheets`, `shift_templates`, `vehicles`, `drivers`, `vehicle_inspections`, `vehicle_inspection_results`, `vehicle_faults`, `vehicle_service_visits`, `users`, `settings`, `stock_inventory`

## Critical Patterns & Conventions


### Date/Time Normalization
* Always use `normalize_date()` and `normalize_time()` before DB insert (see `app.py`, `calc.py`).
* Accepts both ISO (`YYYY-MM-DD`) and Turkish (`DD.MM.YYYY`) formats.
* Example:
    ```python
    normalize_date("05.01.2026")  # → "2026-01-05"
    normalize_time("9:30")        # → "09:30"
    ```

### DB Access
* Always use `with get_conn() as conn:` for all DB operations (autocommit/rollback).
* Never access SQLite directly; use helpers in `db.py`.

### Region-Based Access Control
* Non-admin users see only their region: always filter by `region` column.
* Admin can set "Kayit Bolge" (entry) and "Goruntuleme Bolge" (view).
* Default users: ankara1, izmir1, bursa1, istanbul1 (role=user, region=city), admin (role=admin, region=ALL).


## Key Workflows

### Add Timesheet Entry
1. User selects employee, date, start/end time (UI: Employees/Timesheets tab)
2. Call `normalize_date()`/`normalize_time()`
3. Calculate hours with `calc_day_hours()`
4. Insert into `timesheets` (see `db.py:add_timesheet`)
5. Desktop triggers DB sync to server

### Vehicle Inspection Report
1. Weekly checklist (9 items, Turkish labels, see `VEHICLE_CHECKLIST` in `app.py`)
2. Compare current week vs previous for alerts
3. Store in `vehicle_inspection_results`/`vehicle_inspections`
4. Export as Excel (see `report.py:export_vehicle_weekly_report`)

### Excel Export
* All exports use 16-column fixed layout, Turkish headers, and cell borders/fills (see `report.py`).

### Dashboard Data Query
* Always guard against missing/empty values in Flask routes (see `server/app.py`).
* Example:
    ```python
    weekly_report = get_week_report(plate, week_start)
    if not weekly_report:
            return render_template('404.html')
    ```


## Sync & Deployment

### Desktop Sync
- Controlled by `settings` table: `sync_enabled`, `sync_url`, `sync_token`
- After every CRUD, desktop POSTs DB to `sync_url/sync` with `sync_token` header
- Sync status/errors logged to `%APPDATA%/Rainstaff/logs/rainstaff.log`

### Server Deployment (Render)
- Push to `server/` triggers Render build via GitHub webhook
- Render runs: `pip install -r requirements.txt` then `gunicorn app:app`
- UptimeRobot pings `/health` every 5 min to keep alive


## Testing & Debugging

### Key Files
- Desktop errors: `%APPDATA%/Rainstaff/logs/rainstaff.log`
- UI flows: see `app.py` tab methods (e.g., `refresh_timesheets_tab()`)
- DB schema/migrations: `db.py:init_db()`
- Excel/report issues: check column order in `report.py`

### Common Pitfalls
- **Date Format**: Always normalize to ISO (`YYYY-MM-DD`) before DB insert
- **Region Filter**: Guard against missing/None `region` in old data
- **Tkinter Layout**: Never mix `grid` and `pack` in the same container
- **Sync Failure**: Check API key, sync_url, DB file size
- **Dashboard 500**: Check Render logs for missing imports or DB schema mismatch


## Project-Specific Conventions

- **Language**: All UI labels, field names, and error messages are in Turkish
- **Dates**: Store as ISO (`YYYY-MM-DD`); display as Turkish (`DD.MM.YYYY`)
- **Regions**: Hard-coded: Ankara, Izmir, Bursa, Istanbul, ALL (admin)
- **Excel Export**: 16-column fixed layout, Turkish headers, cell borders/fills
- **Logging**: All CRUD actions logged with user/region context


## Before You Edit

1. **Schema Changes**: Update `db.py:init_db()` and verify migrations are backward compatible
2. **New UI Tab**: Add both Desktop (`app.py`) and Dashboard (`server/app.py`) routes if needed
3. **Hour Calculations**: Test edge cases in `calc.py` (overnight, special days)
4. **Sync Changes**: Ensure backward compatibility; test desktop→server roundtrip
5. **Regional Data**: Always filter by region; never hardcode region assumptions

---
For detailed architecture, see comments in `db.py`, `app.py`, and `server/app.py`.
