#!/usr/bin/env python3
"""
Add sync functions to db.py for multi-region support
"""

sync_functions = '''

# ============================================================================
# SYNC FUNCTIONS - Multi-region database synchronization (Added 19 Ocak 2026)
# ============================================================================

def sync_with_server(sync_url, api_key, region):
    """
    Upload local database to server and download merged version
    
    Args:
        sync_url: Server URL (e.g., https://rainstaff.onrender.com)
        api_key: API authentication token
        region: Current region (Ankara, Istanbul, etc)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import requests
    
    try:
        # Step 1: Upload local DB to server
        with open(DB_PATH, "rb") as f:
            files = {"db": (f"puantaj_{region}.db", f, "application/octet-stream")}
            headers = {
                "X-API-KEY": api_key,
                "X-Region": region,
                "X-Reason": "periodic_sync"
            }
            upload_url = sync_url.rstrip("/") + "/sync"
            
            resp = requests.post(upload_url, headers=headers, files=files, timeout=15)
            
            if resp.status_code != 200:
                return False, f"Upload failed: HTTP {resp.status_code}"
        
        # Step 2: Download merged database from server
        headers = {"X-API-KEY": api_key}
        download_url = sync_url.rstrip("/") + "/sync/download"
        
        resp = requests.get(download_url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            return False, f"Download failed: HTTP {resp.status_code}"
        
        # Step 3: Backup current local database
        backup_path = DB_PATH + ".sync_backup"
        if os.path.isfile(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
        
        # Step 4: Write downloaded database as new local DB
        with open(DB_PATH, "wb") as f:
            f.write(resp.content)
        
        return True, "Sync completed successfully"
    
    except requests.exceptions.Timeout:
        return False, "Timeout: Server took too long to respond"
    except requests.exceptions.ConnectionError:
        return False, "Connection error: Cannot reach server"
    except Exception as e:
        return False, f"Sync error: {str(e)}"


def get_sync_status(sync_url, api_key):
    """
    Get server sync status and statistics
    
    Args:
        sync_url: Server URL
        api_key: API authentication token
    
    Returns:
        dict: Server status information or None if error
    """
    import requests
    
    try:
        headers = {"X-API-KEY": api_key}
        url = sync_url.rstrip("/") + "/sync/status"
        
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    
    except Exception:
        return None

'''

# Read db.py
db_py_path = r"C:\Users\rainwater\Desktop\puantaj\puantaj_app\db.py"

with open(db_py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add sync functions before the last line (usually blank or at end)
new_content = content.rstrip() + "\n" + sync_functions

# Write back
with open(db_py_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ Sync functions added to db.py!")
print("   ├─ sync_with_server(sync_url, api_key, region)")
print("   └─ get_sync_status(sync_url, api_key)")
