#!/usr/bin/env python3
"""
Add Sync Endpoints to Existing Rainstaff Flask Server
This script adds /sync and /sync/download endpoints to the existing server app.py
"""

SYNC_ENDPOINTS = '''

# ============================================================================
# DESKTOP SYNC ENDPOINTS (Added 19 Ocak 2026)
# ============================================================================

@app.route("/sync", methods=["POST"])
def sync_desktop_db():
    """
    Receive database file from desktop, merge with master
    
    Headers:
        X-API-KEY: API key for authentication
        X-Region: Region identifier (Ankara, Istanbul, etc)
        X-Reason: Sync reason (manual, auto, etc)
    
    Body:
        db: multipart database file
    """
    
    # Authentication
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return {"success": False, "error": "Invalid API key"}, 401
    
    # Get metadata
    region = request.headers.get("X-Region", "Unknown")
    reason = request.headers.get("X-Reason", "unknown")
    
    # Check file
    if "db" not in request.files:
        return {"success": False, "error": "No database file in request"}, 400
    
    file = request.files["db"]
    
    try:
        # Read uploaded DB
        db_bytes = file.read()
        
        # Save as backup with timestamp
        timestamp = datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(DATA_DIR, f"sync_backup_{region}_{timestamp}.db")
        
        with open(backup_path, "wb") as f:
            f.write(db_bytes)
        
        # Merge logic: if master DB doesn't exist, use uploaded as master
        if not db_exists():
            with open(DB_PATH, "wb") as f:
                f.write(db_bytes)
        else:
            # Merge: Copy new records from uploaded DB to master
            import tempfile
            temp_path = os.path.join(DATA_DIR, f"temp_sync_{region}.db")
            with open(temp_path, "wb") as f:
                f.write(db_bytes)
            
            # Connection to both databases
            master_conn = get_conn()
            temp_conn = sqlite3.connect(temp_path)
            temp_conn.row_factory = sqlite3.Row
            
            # Copy tables that were modified (timesheets, employees, etc)
            tables_to_merge = ["timesheets", "employees", "vehicles", "drivers"]
            
            for table in tables_to_merge:
                try:
                    # Get all records from uploaded DB
                    temp_records = temp_conn.execute(f"SELECT * FROM {table}").fetchall()
                    
                    for record in temp_records:
                        record_id = record[0]
                        # Check if exists in master
                        exists = master_conn.execute(
                            f"SELECT id FROM {table} WHERE id = ?", (record_id,)
                        ).fetchone()
                        
                        if not exists:
                            # Insert new record
                            cols = [desc[0] for desc in temp_conn.description]
                            placeholders = ",".join(["?" for _ in cols])
                            master_conn.execute(
                                f"INSERT INTO {table} VALUES ({placeholders})",
                                tuple(record)
                            )
                except Exception as e:
                    app.logger.warning(f"Merge {table} error: {e}")
            
            master_conn.commit()
            master_conn.close()
            temp_conn.close()
            
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Log activity
        app.logger.info(f"[SYNC] {region} uploaded DB | Reason: {reason} | Size: {len(db_bytes)} bytes")
        
        return {
            "success": True,
            "message": "Database synced successfully",
            "timestamp": datetime.now(LOCAL_TZ).isoformat(),
            "region": region,
            "backup": backup_path
        }, 200
    
    except Exception as e:
        app.logger.error(f"[SYNC ERROR] {region}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }, 500


@app.route("/sync/download", methods=["GET"])
def download_latest_db():
    """
    Download latest master database
    
    Headers:
        X-API-KEY: API key for authentication
    """
    
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return {"success": False, "error": "Invalid API key"}, 401
    
    try:
        if not db_exists():
            return {"success": False, "error": "No database on server"}, 404
        
        with open(DB_PATH, "rb") as f:
            db_bytes = f.read()
        
        from flask import send_file
        import io
        
        app.logger.info(f"[SYNC DOWNLOAD] Sent {len(db_bytes)} bytes")
        
        return send_file(
            io.BytesIO(db_bytes),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="puantaj.db"
        )
    
    except Exception as e:
        app.logger.error(f"[SYNC DOWNLOAD ERROR] {str(e)}")
        return {"success": False, "error": str(e)}, 500


@app.route("/sync/status", methods=["GET"])
def sync_status():
    """Get server sync status and statistics"""
    
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return {"success": False, "error": "Invalid API key"}, 401
    
    try:
        if not db_exists():
            return {"success": True, "status": "no_database"}
        
        with get_conn() as conn:
            # Get statistics
            emp_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            ts_count = conn.execute("SELECT COUNT(*) FROM timesheets").fetchone()[0]
            veh_count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            drv_count = conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
            
            # Get latest timesheet entry
            latest_ts = conn.execute(
                "SELECT work_date FROM timesheets ORDER BY work_date DESC LIMIT 1"
            ).fetchone()
            
            return {
                "success": True,
                "status": "active",
                "employees": emp_count,
                "timesheets": ts_count,
                "vehicles": veh_count,
                "drivers": drv_count,
                "db_path": DB_PATH,
                "latest_entry": latest_ts[0] if latest_ts else None,
                "timestamp": datetime.now(LOCAL_TZ).isoformat()
            }
    
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "rainstaff",
        "timestamp": datetime.now(LOCAL_TZ).isoformat()
    }, 200

'''

# Read current app.py
app_py_path = r"C:\Users\rainwater\Desktop\puantaj\server\app.py"

with open(app_py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find insertion point (before if __name__ == "__main__")
insertion_point = content.rfind('if __name__ == "__main__"')

if insertion_point == -1:
    print("❌ Could not find insertion point")
    exit(1)

# Insert sync endpoints
new_content = content[:insertion_point] + SYNC_ENDPOINTS + "\n\n" + content[insertion_point:]

# Write back
with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ Sync endpoints added successfully!")
print(f"   ├─ POST /sync (Upload desktop DB)")
print(f"   ├─ GET /sync/download (Download merged DB)")
print(f"   ├─ GET /sync/status (Server status)")
print(f"   └─ GET /health (Health check)")
