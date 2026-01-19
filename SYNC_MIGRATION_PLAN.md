# 🔄 SYNC MIGRATION PLAN - Rainstaff Multi-Region System

**Tarih**: 19 Ocak 2026  
**Status**: READY TO IMPLEMENT  
**Backup**: ✅ Created - `puantaj_BACKUP_2026_01_19_BEFORE_SYNC.db`

---

## 📊 CURRENT DATABASE STATE

```
Employees:      5 records
Timesheets:     37 records
Vehicles:       ❌ TABLE MISSING
Drivers:        ❌ TABLE MISSING
Settings:       6 records
Reports:        ❌ TABLE MISSING
Users:          ❌ TABLE MISSING (needs creation)
```

### 🚨 CRITICAL BUG FOUND:
- **timesheets** table **MISSING region column**
- Current columns: id, employee_id, work_date, start_time, end_time, break_minutes, notes, is_special
- **FIX REQUIRED**: Add `region TEXT NOT NULL` column

---

## 🎯 MIGRATION PHASES

### PHASE 1: Database Schema Fix (Day 1)
```
1. Add missing tables (vehicles, drivers, users, reports, vehicle_faults, etc)
2. Add region column to timesheets table
3. Populate default users (4-5 dashboard users + admin)
4. Verify data integrity
```

### PHASE 2: Server Sync Endpoint (Day 1-2)
```
Render Server (Flask):
├── POST /sync
│   ├── Receive DB file from Desktop
│   ├── Merge with server DB
│   ├── Store merged version
│   └── Return status
│
├── GET /sync/download
│   ├── Send latest merged DB to Desktop
│   └── Return incremental changes
│
└── Admin Dashboard
    ├── Live employee count per region
    ├── Recent timesheet entries
    └── Login/logout activity log
```

### PHASE 3: Desktop Sync Upgrade (Day 2)
```
db.py:
├── New function: sync_with_server()
│   ├── Upload local DB to server
│   ├── Download merged DB
│   ├── Merge logic with conflict detection
│   └── Update local DB
│
└── Periodic trigger (every 5 minutes)

app.py:
├── trigger_sync_periodic()
└── sync_status in UI
```

### PHASE 4: Testing & Deployment (Day 3-4)
```
1. Single-PC test (Ankara - local sync)
2. Dual-PC test (Ankara + Istanbul simulation)
3. Multi-region conflict test
4. Admin dashboard live test
5. Go live on Render
```

---

## 🛠️ IMMEDIATE ACTIONS

### STEP 1: Fix Database Schema
```sql
-- Add region column to timesheets (with default for existing records)
ALTER TABLE timesheets ADD COLUMN region TEXT DEFAULT 'Ankara';

-- Create missing tables
CREATE TABLE vehicles (...);
CREATE TABLE drivers (...);
CREATE TABLE users (...);
CREATE TABLE reports (...);
CREATE TABLE vehicle_faults (...);
CREATE TABLE vehicle_service_visits (...);
CREATE TABLE vehicle_inspections (...);
CREATE TABLE vehicle_inspection_results (...);
```

### STEP 2: Create Server Sync Endpoint
```
Location: server/app.py (on Render)

@app.route('/sync', methods=['POST'])
def sync_desktop_db():
    # 1. Receive DB from desktop
    # 2. Extract region from X-Region header
    # 3. Merge with server DB
    # 4. Return success

@app.route('/sync/download', methods=['GET'])
def download_latest_db():
    # Return latest merged DB
```

### STEP 3: Upgrade Desktop Sync
```
db.py additions:
- def sync_with_server(url, token, region)
- def merge_databases(local_db, server_db)
- def handle_sync_conflict()

app.py modifications:
- trigger_sync_periodic() - every 5 min
- Display sync status in statusbar
- Handle offline mode gracefully
```

### STEP 4: Admin Dashboard Enhancement
```
New features:
✓ Real-time employee count per region
✓ Recent entries (timesheets, vehicles, etc)
✓ User login/logout activity log
✓ Sync status of all regional PCs
✓ Data integrity alerts
```

---

## 📋 ARCHITECTURE DIAGRAM

```
┌──────────────────────────────────────────────────────┐
│          RENDER SERVER (Cloud)                        │
│  - PostgreSQL OR SQLite (merged DB)                   │
│  - Flask sync endpoints                               │
│  - Admin dashboard with live updates                  │
└──────────────┬──────────────┬──────────────┬──────────┘
               │              │              │
        ┌──────▼──┐    ┌──────▼──┐   ┌──────▼──┐
        │ ANKARA   │    │ISTANBUL  │   │ BURSA   │
        │   PC     │    │   PC     │   │   PC    │
        │ (Local   │    │ (Local   │   │ (Local  │
        │  DB)     │    │  DB)     │   │  DB)    │
        └──────────┘    └──────────┘   └─────────┘
        
Region: Ankara      Region: Istanbul   Region: Bursa
User: ankara1       User: istanbul1    User: bursa1
Sync: Every 5 min   Sync: Every 5 min  Sync: Every 5 min

Admin Dashboard (Web):
├─ Views: Tüm bölgeler (ALL)
├─ Real-time updates
└─ Activity log
```

---

## ⚠️ RISKS & MITIGATION

| Risk | Mitigation |
|------|-----------|
| **Timesheets region conflict** | ADD column with DEFAULT, update existing |
| **Sync lag (5 min)** | Acceptable for end-of-shift entry model |
| **Concurrent edits same region** | Each region has separate PC = safe |
| **Network downtime** | Offline work supported, sync on reconnect |
| **Data loss during merge** | Backup + Last-write-wins strategy |
| **Server disk space** | SQLite small, monitor on Render |

---

## 📅 TIMELINE

| Phase | Duration | Deliverable |
|-------|----------|------------|
| Schema fix + DB prep | 1 day | ✅ Fixed DB + migration script |
| Server endpoint | 1-2 days | POST /sync, GET /sync/download |
| Desktop sync logic | 1 day | db.py + app.py upgrades |
| Testing | 1-2 days | All scenarios tested |
| **TOTAL** | **4-5 days** | **Live system** |

---

## 🚀 GO-LIVE CHECKLIST

- [ ] Database schema fixed
- [ ] All 37 timesheets have region = employee's region
- [ ] Default admin users created
- [ ] Server /sync endpoint deployed on Render
- [ ] Desktop sync logic integrated
- [ ] Admin dashboard updated
- [ ] Single-PC sync test ✅
- [ ] Multi-PC conflict test ✅
- [ ] Network downtime test ✅
- [ ] Data integrity audit ✅
- [ ] Production backup ✅
- [ ] Team training completed
- [ ] Go-live approval ✅

---

## 📞 NEXT STEPS

1. **Confirm this plan** with team
2. **Start with PHASE 1** (Database schema fix)
3. **Backup verification** (restore test)
4. **Proceed to PHASE 2** (Server setup)

---

**Prepared by**: GitHub Copilot  
**Date**: 19 Ocak 2026, 14:30  
**Status**: READY FOR EXECUTION
