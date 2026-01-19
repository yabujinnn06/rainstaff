# Rainstaff Sync Service - Installation Guide

## Overview
Sync Service is a **24/7 background process** that automatically synchronizes your Rainstaff database with the web server every 3 minutes. Desktop app doesn't need to be open.

## Installation Steps

### Step 1: Download NSSM
1. Right-click `download_nssm.bat` → "Run as Administrator"
2. Wait for completion (will download ~500KB)
3. NSSM will be extracted to `nssm/` folder

### Step 2: Install Service
1. Right-click `install_sync_service.bat` → "Run as Administrator"
2. Script will:
   - Create Windows Service named `RainstaffSyncService`
   - Set it to start automatically on boot
   - Start it immediately
3. You'll see: `[✓] SUCCESS! Rainstaff Sync Service is running!`

### Step 3: Verify Installation
```
Open Windows Services (services.msc):
- Find "RainstaffSyncService"
- Status should be: Running
- Startup Type should be: Automatic
```

Or command line:
```
sc query RainstaffSyncService
```

### Step 4: Enable Sync in Desktop App
1. Open Rainstaff Desktop App
2. Go to Settings tab
3. Enable: ☑️ Senkron Etkinlestir
4. Enter sync URL and token (from server admin)
5. Click Save

**Note:** Desktop sync_enabled will still work (manual/on-change), but Service syncs continuously.

---

## How It Works

### Desktop App
- **Before:** Manual sync on every change (only when app is running)
- **After:** Local data entry only; Service handles sync

### Sync Service
- Checks every **3 minutes** if sync is enabled
- If enabled: Uploads DB → Downloads merged DB → Updates local DB
- Logs to: `%APPDATA%\Rainstaff\logs\sync_service.log`
- Auto-restarts if crashes
- Runs in background even when PC is restarted

### Result
- **Web server always has latest data** (updated every 3 min)
- **Desktop always has latest merged data** (from service download)
- **No conflicts** (single sync thread)
- **No data loss** (backup created before each update)

---

## Management

### View Logs
```
C:\Users\{YourName}\AppData\Roaming\Rainstaff\logs\sync_service.log
```

### Start Service
```
net start RainstaffSyncService
```

### Stop Service
```
net stop RainstaffSyncService
```

### Check Status
```
sc query RainstaffSyncService
```

### View Service Settings
```
Open: services.msc → Find "RainstaffSyncService" → Right-click Properties
```

### Remove Service (Uninstall)
```
net stop RainstaffSyncService
nssm\win64\nssm.exe remove RainstaffSyncService confirm
```

---

## Troubleshooting

### Service won't start
1. **Check logs:** `C:\Users\{YourName}\AppData\Roaming\Rainstaff\logs\sync_service.log`
2. **Verify Python:** `python --version` in Command Prompt
3. **Verify sync_service.py path:** Should be in `puantaj_app/` folder
4. **Check permissions:** Service runs as current user (should have access to DB)

### Service starts but doesn't sync
1. Check if sync is enabled in Desktop App Settings
2. Verify sync_url and sync_token are set correctly
3. Check network connectivity to server
4. View logs for detailed error messages

### Logs are missing
- Folder might not exist: `C:\Users\{YourName}\AppData\Roaming\Rainstaff\logs\`
- Create it manually and restart service

### Service disappeared from services.msc
1. Reinstall: Run `install_sync_service.bat` again
2. Make sure to run as Administrator

---

## Configuration

### Change Sync Interval
Edit `sync_service.py`, line ~28:
```python
SYNC_INTERVAL_SECONDS = 180  # Change this number (seconds)
```

### Change Retry Settings
Edit `sync_service.py`, lines ~31-32:
```python
MAX_RETRIES = 3  # How many times to retry if sync fails
RETRY_DELAY_SECONDS = 5  # Wait time between retries
```

---

## Safety & Backups

✅ **Safe:**
- Service creates backup before each update: `.sync_backup`
- Runs as current user (same permissions as Desktop app)
- Logs all actions for debugging
- Automatic restart on failure
- No data loss (DB merged on server)

⚠️ **Important:**
- Don't edit DB while service is syncing (unlikely to cause issues, but avoid)
- Keep at least 3GB free disk space (for backup + DB)
- Service has access to `%APPDATA%` - don't change folder permissions

---

## Support

If you see errors in the log file:
1. Screenshot the error
2. Check last 20 lines: `%APPDATA%\Rainstaff\logs\sync_service.log`
3. Contact system administrator

---

## Summary

**Before Sync Service:**
- Desktop must be open to sync data
- Manual sync on each change
- Web dashboard may show old data

**After Sync Service:**
- ✅ 24/7 automatic sync (every 3 minutes)
- ✅ Desktop can be closed
- ✅ Web always shows latest data
- ✅ PC restart doesn't stop sync
- ✅ Detailed logging for debugging
