
import sqlite3
import os

# Try to find the DB path as per logic in db.py
APP_NAME = "Rainstaff"
LOCAL_DB_DIR = os.path.join(os.getcwd(), "puantaj_app", "data")
APPDATA = os.environ.get("APPDATA")
if APPDATA:
    APPDATA_DIR = os.path.join(APPDATA, APP_NAME, "data")
    DB_PATH = os.path.join(APPDATA_DIR, "puantaj.db")
else:
    DB_PATH = os.path.join(LOCAL_DB_DIR, "puantaj.db")

print(f"Checking DB at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print(f"DB not found at primary location. Checking local fallback: {os.path.join(LOCAL_DB_DIR, 'puantaj.db')}")
    DB_PATH = os.path.join(LOCAL_DB_DIR, "puantaj.db")

if not os.path.exists(DB_PATH):
    print("DB still not found.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = ["timesheets", "employees", "vehicles", "drivers"]

with open("schema_report.txt", "w", encoding="utf-8") as f:
    for table in tables:
        f.write(f"\n--- Columns in {table} ---\n")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                f.write(str(col) + "\n")
            
            col_names = [col[1] for col in columns]
            if "region" in col_names:
                 f.write(f"✅ 'region' column exists in {table}\n")
            else:
                 f.write(f"❌ 'region' column MISSING in {table}\n")
        except Exception as e:
            f.write(f"Error checking {table}: {e}\n")

conn.close()
