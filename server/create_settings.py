import sqlite3
import os

db_path = os.path.join(os.environ.get("APPDATA", ""), "Rainstaff", "data", "puantaj.db")
print(f"DB Path: {db_path}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    
    # List all tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Existing tables: {[t[0] for t in tables]}")
    
    # Create settings table if not exists
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    print("Settings table created/verified")
    
    # Verify again
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Tables after: {[t[0] for t in tables]}")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")
