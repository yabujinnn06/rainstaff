# Rainstaff - Project Notes and Handover

This README summarizes what was built, how the desktop app and web dashboard work,
how deployments happen, and what to watch for to avoid errors. It is written so a
new engineer or AI can continue the project without missing context.

## 1) Overview
- Two parts:
  1) Desktop app (Tkinter): main data entry, creates and updates the local SQLite DB.
  2) Web dashboard (Flask): read-only admin panel that loads the latest uploaded DB.
- Desktop writes data, dashboard reads data.
- Sync: desktop uploads DB file to server after each change.

## 2) Key Features Implemented
- Puantaj: daily work hours, overtime, night, special day.
- Employees, Timesheets, Reports (Excel).
- Vehicles + Drivers + Weekly inspections.
- Service/Fault tracking (sanayi).
- Oil change tracking (default interval 14000 km).
- Admin dashboard: KPI cards, alerts, data quality, details.
- Region-based users (Ankara, Izmir, Bursa, Istanbul, Admin).
- Auto backup + manual backup/restore.
- Data export/import (ZIP).
- Live log screen inside desktop app.

## 3) Data Storage
- Desktop DB:
  %APPDATA%\Rainstaff\data\puantaj.db
- Backups:
  %APPDATA%\Rainstaff\backups\
- Logs:
  %APPDATA%\Rainstaff\logs\rainstaff.log

## 4) Desktop -> Dashboard Sync
- Desktop setting: "Bulut Senkron"
  - sync_enabled=1
  - sync_url = https://rainstaff.onrender.com (or your server)
  - sync_token = API_KEY value
- After each CRUD action: desktop uploads DB via POST /sync.
- Server replaces its DB with uploaded file.

## 5) Web Dashboard Data Flow
- Flask reads the server DB on each request.
- Endpoints:
  - /dashboard (home)
  - /alerts (weekly alerts)
  - /reports (weekly reports list)
  - /reports/weekly/<plate>/<week_start>
  - /vehicle/<plate>
  - /driver/<id>
  - /employee/<id>
- All pages include fixed sidebar via _sidebar.html.
- Mobile: sidebar fixed and expandable; content shifts accordingly.

## 6) Users and Regions
Default users (stored in DB):
- ankara1 / 060106 (region Ankara)
- izmir1  / 350235 (region Izmir)
- bursa1  / 160316 (region Bursa)
- istanbul1 / 340434 (region Istanbul)
- admin / 748774 (region ALL)

Rules:
- Non-admin users only see their region.
- Admin can set "Kayit Bolge" and "Goruntuleme Bolge".
- Dashboard: admin has a region filter dropdown; others see own region.

## 7) Oil Maintenance
- Vehicle fields: oil_change_km, oil_interval_km.
- Default interval = 14000 km.
- Dashboard shows oil due / soon alerts.
- Vehicle list highlights due/soon.

## 8) Weekly Vehicle Inspections
- Fixed checklist:
  - body_dent, paint_damage, interior_clean, smoke_smell, tire_condition,
    lights, glass, warning_lamps, water_level
- Weekly report compares current vs previous week.
- Alerts generated for worsened/repeated issues.

## 9) Reports
- Timesheet Excel export.
- Weekly vehicle report export.
- Vehicle card report export.
- All report outputs stored in "reports" table (archive).

## 10) Logging and Traceability
- Log file: rainstaff.log
- Live log UI in desktop app ("Loglar" tab).
- Logs include:
  - app start
  - login success/failure
  - CRUD actions (employee, timesheet, vehicle, driver, faults, service visits)
  - report export
  - backup/export/import
  - settings save
- Tkinter exceptions are captured and logged.

## 11) Backup and Data Transfer
- Auto backup: once per day
- Manual backup: Settings > Veri Yonetimi > Yedek Al
- Restore: Settings > Veri Yonetimi > Yedek Geri Yukle
- Export/Import ZIP: Settings > Veri Yonetimi
- After restore/import, restart the app.

## 12) Web Admin Design
- Sidebar fixed (desktop + mobile).
- Topbar fixed.
- KPI cards + alerts + data quality + detail tables.
- Alerts rows link to weekly report pages.

## 13) Deployment via Git + Render
We deploy the Flask dashboard using GitHub -> Render auto-deploy.

Steps:
1) Commit and push:
   git add server/...
   git commit -m "Dashboard update"
   git push

2) Render detects the new push and deploys automatically.
3) URL remains the same (example: https://rainstaff.onrender.com).

Render settings:
- Build: pip install -r requirements.txt
- Start: gunicorn app:app
- Health: /health

## 14) Uptime (anti-sleep)
- UptimeRobot pings /health every 5 minutes.
- Desktop app also pings /health periodically (keepalive).

## 15) Files to Know
Desktop:
- puantaj_app/app.py (UI + logic)
- puantaj_app/db.py (DB + migrations + backup/export)
- puantaj_app/report.py (Excel generation)
- puantaj_app/calc.py (hour calculations)

Server:
- server/app.py (Flask routes and DB read)
- server/templates/*.html
- server/templates/_sidebar.html
- server/static/style.css

## 16) How to Avoid Errors
- Always normalize date/time inputs (YYYY-MM-DD, HH:MM).
- Ensure region columns exist after DB migrations.
- When adding new fields: update schema + ensure migration in db.py.
- Keep report/export functions aligned with DB schema.
- In Flask dashboard, always guard empty DB and missing values.
- Avoid mixing grid/pack in same Tkinter container.
- Test after changes: run desktop app and check key flows.

## 17) Known Limitations
- Dashboard is read-only.
- Desktop must sync for new data to show in web.
- Render free tier may sleep; uptime pings reduce downtime.

## 18) Quick Troubleshooting
- Sync 401: API_KEY mismatch or empty token.
- Dashboard 500: check Render logs for missing imports/vars.
- Desktop errors: open rainstaff.log for details.

---
If someone needs to continue:
- Use this README to understand the architecture.
- Use the files above as entry points.
- Keep ASCII-only edits for consistency, unless the file already uses Unicode.
