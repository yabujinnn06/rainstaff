import sqlite3
import os

DB_PATH = "puantaj_copy.db"

try:
    if os.path.exists(DB_PATH):
        print(f"Connecting to {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        
        print("--- DELETED RECORDS ---")
        try:
            cursor = conn.execute("SELECT * FROM deleted_records")
            rows = cursor.fetchall()
            if not rows:
                print("No deleted records found.")
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading deleted_records: {e}")

        print("\n--- TIMESHEET 110 ---")
        try:
            cursor = conn.execute("SELECT * FROM timesheets WHERE id=110")
            rows = cursor.fetchall()
            if not rows:
                print("Timesheet 110 NOT found (It is missing).")
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading timesheets: {e}")
            
        conn.close()
    else:
        print(f"File not found: {DB_PATH}")
except Exception as e:
    print(f"Fatal error: {e}")
