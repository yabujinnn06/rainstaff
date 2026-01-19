# 🚀 QUICK START GUIDE - Phase 2 Deployment

**Read this first before next step!**

---

## 📋 CHECKLIST FOR PHASE 2 (Tomorrow/Next Day)

### Step 1: Render Account (10 minutes)
- [ ] Go to https://render.com/
- [ ] Click "Sign Up"
- [ ] Use email
- [ ] Confirm email
- [ ] Login to Render dashboard

### Step 2: Prepare Server Files (15 minutes)

**Create folder:** `server/` in your project

**File 1: `server/requirements.txt`**
```
Flask==2.3.0
gunicorn==20.1.0
requests==2.31.0
Werkzeug==2.3.0
```

**File 2: `server/Procfile`**
```
web: gunicorn app:app
```

**File 3: `server/app.py`**
```
Copy from: server_sync_app.py (already in project)
```

### Step 3: Deploy on Render (30 minutes)

1. In Render dashboard: Click "New" → "Web Service"
2. Choose "Deploy from GitHub" OR "Upload repository"
3. Fill in:
   - **Name**: rainstaff-sync
   - **Branch**: main (or your branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Add **Environment Variable**:
   - Key: `API_KEY`
   - Value: `your_very_secure_random_string_here` (e.g., random 32 chars)
5. Click "Create Web Service"
6. Wait for deployment (2-3 min)
7. Get your URL: `https://your-app-xxxxx.onrender.com`

### Step 4: Test Server (10 minutes)

Open browser, go to:
```
https://your-app-xxxxx.onrender.com/health
```

You should see:
```json
{"status": "ok", "timestamp": "2026-01-20T10:30:45.123456"}
```

If you see this → **Server is working! ✅**

### Step 5: Save Your URL & API_KEY

Create a file: `config_sync.txt`

```
SYNC_URL=https://your-app-xxxxx.onrender.com
SYNC_API_KEY=your_very_secure_random_string_here
SYNC_ENABLED=1
```

Keep this safe! You'll need it for Phase 3.

---

## 🎯 WHAT TO DO WITH THIS INFO

After server is deployed:

1. **Tell me the SYNC_URL** (e.g., https://rainstaff-sync-abcd.onrender.com)
2. **Save API_KEY somewhere safe** (not in code!)
3. **I'll add Phase 3 sync code** to desktop app
4. **Then we test together**

---

## ⚠️ COMMON ISSUES & FIXES

### Issue: "No such module: flask"
```
Fix: Make sure requirements.txt is in server/ folder
     and Build Command is: pip install -r requirements.txt
```

### Issue: Server shows 404
```
Fix: Make sure app.py has:
     if __name__ == "__main__":
         app.run(host="0.0.0.0", port=5000)
```

### Issue: Can't find /health endpoint
```
Fix: Paste this in app.py if missing:
     @app.route("/health", methods=["GET"])
     def health():
         return jsonify({"status": "ok"})
```

---

## 📞 TIMELINE

```
Today (19 Ocak):     ✅ Phase 1 Complete
Tomorrow (20 Ocak):  → Phase 2 Deploy (~2 hours)
Day 3 (21 Ocak):     → Phase 3 Desktop Code (~3 hours)
Day 4-5 (22-23):     → Phase 4 Testing (~1-2 days)
Day 5 (23 Ocak):     → GO-LIVE 🎉
```

---

## ✅ YOU'RE READY!

Everything is prepared. Just follow these steps:

1. Render account create (free)
2. Deploy server code
3. Get URL
4. Tell me URL
5. I code Phase 3
6. We test
7. GO-LIVE

**Questions?** Just ask!

---

**File Location**: `C:\Users\rainwater\Desktop\puantaj\QUICK_START_GUIDE.md`
