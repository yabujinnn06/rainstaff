# 🚀 HYBRID SYNC IMPLEMENTATION GUIDE

**Status**: Phase 1 ✅ Complete | Phase 2 🔧 In Progress | Phase 3 ⏳ Ready | Phase 4 ⏳ Planned

---

## ✅ COMPLETED (19 Ocak 2026)

### Phase 1: Database Schema Fix
- ✅ Backup created: `puantaj_BACKUP_2026_01_19_BEFORE_SYNC.db`
- ✅ Region column added to timesheets table
- ✅ All missing tables created (vehicles, drivers, users, etc)
- ✅ Default users populated (ankara1, istanbul1, bursa1, izmir1, admin)

**Database Status:**
```
Employees:      5 records
Timesheets:     37 records (+ region column)
Vehicles:       0 records (ready)
Drivers:        0 records (ready)
Users:          5 default users
Settings:       6 records
```

---

## 🔧 PHASE 2: SERVER SYNC ENDPOINT (Render Deployment)

### What You Need to Do:

**1. Create Server Directory Structure**
```
server/
├── app.py                    ← Use: server_sync_app.py
├── requirements.txt          ← Dependencies
├── Procfile                  ← Deployment config
└── .env                      ← Secrets (API_KEY)
```

**2. Create requirements.txt**
```
Flask==2.3.0
gunicorn==20.1.0
requests==2.31.0
Werkzeug==2.3.0
```

**3. Create Procfile for Render**
```
web: gunicorn app:app
```

**4. Deploy on Render.com**

```
Steps:
1. Go to https://render.com/
2. Create New → Web Service
3. Connect GitHub repo (if using git)
   OR upload server/ folder manually
4. Set Configuration:
   ├── Build Command: pip install -r requirements.txt
   ├── Start Command: gunicorn app:app
   ├── Environment Variables:
   │   └── API_KEY = "your_secure_token_here"
   └── Instance Type: Free (sufficient for 5-6 PCs)
5. Deploy
6. Note the URL: https://your-app.onrender.com
```

**5. Server Endpoints Available**

```
GET    /health                ← Status check
POST   /sync                  ← Desktop uploads DB
GET    /sync/download         ← Desktop downloads merged DB
GET    /status                ← Sync statistics
```

**Example Usage (from Desktop):**
```bash
# Upload
curl -X POST \
  -H "X-API-KEY: your_token" \
  -H "X-Region: Ankara" \
  -F "db=@puantaj.db" \
  https://your-app.onrender.com/sync

# Download
curl -X GET \
  -H "X-API-KEY: your_token" \
  https://your-app.onrender.com/sync/download \
  -o puantaj.db

# Check status
curl https://your-app.onrender.com/status
```

---

## 📝 PHASE 3: DESKTOP SYNC UPGRADE

### What to Modify in Desktop App:

**1. Update db.py - Add Sync Functions**

```python
# Add to db.py

import requests
import hashlib
from datetime import datetime

def sync_with_server(sync_url, api_key, region):
    """Upload local DB to server and download merged version"""
    
    try:
        # Step 1: Upload local DB
        with open(DB_PATH, "rb") as f:
            files = {"db": (f"puantaj_{region}.db", f, "application/octet-stream")}
            headers = {
                "X-API-KEY": api_key,
                "X-Region": region,
                "X-Reason": "auto_sync"
            }
            url = sync_url.rstrip("/") + "/sync"
            
            resp = requests.post(url, headers=headers, files=files, timeout=10)
            
            if resp.status_code != 200:
                return False, f"Upload failed: {resp.status_code}"
        
        # Step 2: Download merged DB
        resp = requests.get(
            sync_url.rstrip("/") + "/sync/download",
            headers={"X-API-KEY": api_key},
            timeout=10
        )
        
        if resp.status_code != 200:
            return False, f"Download failed: {resp.status_code}"
        
        # Step 3: Backup and replace local DB
        import shutil
        backup_path = DB_PATH + ".sync_backup"
        shutil.copy2(DB_PATH, backup_path)
        
        with open(DB_PATH, "wb") as f:
            f.write(resp.content)
        
        return True, "Sync successful"
    
    except Exception as e:
        return False, str(e)


def get_server_status(sync_url, api_key):
    """Check server sync status"""
    try:
        resp = requests.get(
            sync_url.rstrip("/") + "/status",
            headers={"X-API-KEY": api_key},
            timeout=5
        )
        return resp.json()
    except Exception:
        return None
```

**2. Update app.py - Add Periodic Sync**

```python
# Add to PuantajApp class

def trigger_sync_periodic(self):
    """Called every 5 minutes to sync with server"""
    
    if not hasattr(self, 'sync_enabled_var'):
        return
    
    enabled = self.sync_enabled_var.get() if hasattr(self, 'sync_enabled_var') else False
    if not enabled:
        return
    
    sync_url = self.sync_url_var.get().strip() if hasattr(self, 'sync_url_var') else ""
    api_key = self.sync_token_var.get().strip() if hasattr(self, 'sync_token_var') else ""
    region = self._entry_region()
    
    if not sync_url or not api_key or not region:
        return
    
    # Run sync in background thread
    thread = threading.Thread(
        target=self._sync_worker_periodic,
        args=(sync_url, api_key, region),
        daemon=True
    )
    thread.start()

def _sync_worker_periodic(self, sync_url, api_key, region):
    """Background sync worker"""
    try:
        success, msg = db.sync_with_server(sync_url, api_key, region)
        
        if success:
            self.status_var.set(f"Senkron OK ({region})")
            if self.logger:
                self.logger.info(f"Periodic sync completed: {region}")
        else:
            self.status_var.set(f"Senkron HATA: {msg}")
            if self.logger:
                self.logger.warning(f"Periodic sync failed: {msg}")
    except Exception as e:
        if self.logger:
            self.logger.error(f"Periodic sync error: {e}")

# In __init__, add periodic sync timer
def _start_periodic_sync(self):
    """Start periodic sync timer (every 5 minutes)"""
    self._schedule_sync()

def _schedule_sync(self):
    """Schedule next sync"""
    self.after(5 * 60 * 1000, self._do_periodic_sync)  # 5 minutes

def _do_periodic_sync(self):
    """Execute periodic sync"""
    self.trigger_sync_periodic()
    self._schedule_sync()  # Schedule next one
```

**3. Settings Tab Configuration**

Ensure Settings tab has:
```
- Senkron Aktif: [checkbox]
- Senkron URL: [text field]
- Senkron Token: [text field]
- Test Button: [button to test connection]
- Last Sync: [status label showing timestamp]
```

---

## 🧪 PHASE 4: TESTING PLAN

### Test 1: Single-PC Sync
```
✓ Desktop with Ankara user
  ├─ Enable sync with server URL
  ├─ Click "Test Connection"
  ├─ Add new timesheet
  ├─ Check sync status
  └─ Verify on server (/status endpoint)
```

### Test 2: Dual-PC Sync
```
✓ Ankara PC adds employee
  ├─ Istanbul PC downloads (pull latest)
  ├─ Istanbul sees Ankara employee? YES/NO
  ├─ Istanbul adds own employee
  ├─ Ankara downloads (pull latest)
  └─ Ankara sees Istanbul employee? YES/NO
```

### Test 3: Concurrent Writes (Safe Case)
```
✓ Ankara and Istanbul edit SAME data simultaneously?
  ├─ Ankara: Add timesheet for Ahmet (Ankara employee)
  ├─ Istanbul: Add timesheet for Fatma (Istanbul employee)
  ├─ Both sync
  ├─ Check master DB
  └─ Both records present? YES ✓
```

### Test 4: Admin Dashboard
```
✓ Admin user logs in → sees all regions
✓ Admin dashboard shows:
  ├─ Total employees: 5
  ├─ Total timesheets: 37+
  └─ Recent entries (all regions)
```

### Test 5: Network Downtime
```
✓ Desktop PC loses network
  ├─ Continue working offline
  ├─ Add new timesheets
  ├─ Network comes back
  ├─ Click "Sync Now"
  └─ New entries uploaded? YES ✓
```

---

## 📊 ADMIN DASHBOARD ENHANCEMENT

### Current Status: Static Flask page on Render
### Target: Enhanced with live data

**Add to server_sync_app.py:**

```python
@app.route("/dashboard", methods=["GET"])
def admin_dashboard():
    """Admin dashboard showing all regions"""
    
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return "Unauthorized", 401
    
    try:
        with get_master_db() as conn:
            cur = conn.cursor()
            
            # Get stats by region
            cur.execute("""
                SELECT 
                    e.region,
                    COUNT(DISTINCT e.id) as employees,
                    COUNT(DISTINCT t.id) as timesheets,
                    MAX(t.work_date) as last_entry
                FROM employees e
                LEFT JOIN timesheets t ON e.id = t.employee_id AND t.region = e.region
                GROUP BY e.region
            """)
            
            stats = cur.fetchall()
            
            return render_template("dashboard.html", stats=stats)
    
    except Exception as e:
        return f"Error: {e}", 500
```

---

## 🚨 ROLLBACK PROCEDURE

If anything goes wrong:

```bash
# 1. Stop all desktop apps
# 2. Stop server
# 3. Restore database from backup
sqlite3 puantaj.db < puantaj_BACKUP_2026_01_19_BEFORE_SYNC.db

# 4. Restart without sync enabled
# 5. Contact support
```

---

## ✅ GO-LIVE CHECKLIST

- [ ] Server app deployed on Render
- [ ] API_KEY configured in environment
- [ ] Desktop sync endpoint configured (URL + token)
- [ ] Test single-PC sync ✓
- [ ] Test dual-PC sync ✓
- [ ] Test offline scenario ✓
- [ ] Admin dashboard working ✓
- [ ] Backup verified (restore test) ✓
- [ ] Team trained on new sync system ✓
- [ ] Production backup taken ✓
- [ ] Go-live approval signed ✓

---

## 🔗 CONNECTIONS SUMMARY

```
Desktop (Ankara PC)
├── Uses: ankara1 / Ankara region
├── Syncs to: https://your-app.onrender.com/sync
└── Every 5 minutes ✓

Desktop (Istanbul PC)
├── Uses: istanbul1 / Istanbul region
├── Syncs to: https://your-app.onrender.com/sync
└── Every 5 minutes ✓

Admin Dashboard
├── URL: https://your-app.onrender.com/dashboard
├── API Key: (same as sync token)
└── Shows: All regions, real-time stats ✓

Server Master DB
└── Location: /tmp/rainstaff/puantaj_master.db (Render)
```

---

## 📞 NEXT STEPS

1. **Deploy server on Render** (Phase 2)
2. **Modify desktop sync code** (Phase 3)
3. **Run tests** (Phase 4)
4. **Go-live** (Phase 5)

**Timeline**: 3-4 days from now

---

**Prepared by**: GitHub Copilot  
**Date**: 19 Ocak 2026  
**Status**: Ready for Phase 2 Deployment
