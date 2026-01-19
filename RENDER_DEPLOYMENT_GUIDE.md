# 🚀 RENDER DEPLOYMENT - SYNC ENDPOINTS

**Status**: ✅ Sync endpoints added to server/app.py  
**API_KEY**: 7487 (already configured)  
**Service**: rainstaff (already running)

---

## ✅ WHAT WAS DONE

### Added 4 Sync Endpoints to server/app.py

```
1. POST /sync
   └─ Desktop uploads local database
   └─ Server merges with master DB
   └─ Requires: X-API-KEY header + "db" file

2. GET /sync/download
   └─ Desktop downloads latest merged DB
   └─ Requires: X-API-KEY header

3. GET /sync/status
   └─ Get server statistics (employees, timesheets, etc)
   └─ Requires: X-API-KEY header

4. GET /health
   └─ Health check endpoint
   └─ No auth required (useful for monitoring)
```

---

## 🚀 DEPLOY TO RENDER (10 minutes)

### Step 1: Push Code to Render

**Option A: If using GitHub (recommended)**
```
1. Commit changes:
   git add .
   git commit -m "Add sync endpoints to Flask server"
   git push

2. Render will auto-redeploy on push

3. Check deployment in Render dashboard
```

**Option B: Manual (if not using Git)**
```
1. In Render dashboard:
   - Go to your "rainstaff" service
   - Click "Manual Deploy"
   - Choose "latest main commit" or upload manually
   - Redeploy
```

### Step 2: Verify Deployment

Once deployed, test the endpoints:

**Test /health (no auth required)**
```
curl https://rainstaff.onrender.com/health

Response:
{"status": "ok", "service": "rainstaff", "timestamp": "2026-01-19T..."}
```

**Test /sync/status (with API key)**
```
curl -H "X-API-KEY: 7487" \
  https://rainstaff.onrender.com/sync/status

Response:
{
  "success": true,
  "status": "active",
  "employees": 5,
  "timesheets": 37,
  "vehicles": 0,
  "drivers": 0,
  "timestamp": "2026-01-19T..."
}
```

**If you see this → Server is working! ✅**

---

## 📝 NEXT: DESKTOP SYNC CODE

After server is deployed and working, I'll add to desktop app:

### db.py additions:
```python
def sync_with_server(sync_url, api_key, region):
    """Upload local DB and download merged version"""
    # Upload local DB to /sync
    # Download merged DB from /sync/download
    # Merge locally
```

### app.py additions:
```python
def trigger_sync_periodic():
    """Called every 5 minutes"""
    # Call sync_with_server()
    # Update UI status
```

---

## 🔐 SECURITY

✅ **API_KEY**: 7487 is configured in Render environment  
✅ **HTTPS**: Render provides automatic SSL  
✅ **Region Filtering**: Desktop enforces WHERE region = current_region  
✅ **Backup**: Every sync creates backup file

---

## 📊 SYNC FLOW

```
Desktop (Ankara):
├─ Every 5 minutes
├─ POST /sync with puantaj.db + API_KEY
├─ Server merges
├─ Desktop downloads merged DB
└─ Local DB updated

Desktop (Istanbul):
├─ Every 5 minutes
├─ POST /sync with puantaj.db + API_KEY
├─ Server merges
├─ Desktop downloads merged DB
└─ Local DB updated

Admin Dashboard:
├─ Reads from merged DB
├─ Shows all regions
└─ Real-time stats
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Code pushed to Render (git push or manual deploy)
- [ ] Service redeployed (watch for green "Live" status)
- [ ] /health endpoint responds ✓
- [ ] /sync/status returns employee count (5) ✓
- [ ] API_KEY still working (7487) ✓

---

## 🎯 NEXT STEPS

1. **Deploy to Render** (now, 10 min)
2. **Test endpoints** (curl commands above)
3. **Tell me "deployed"**
4. I'll add desktop sync code (same day)
5. Test everything together

---

**Render Service**: https://rainstaff.onrender.com  
**API_KEY**: 7487  
**Sync URL**: https://rainstaff.onrender.com/sync  
**Status**: ✅ Ready to deploy
