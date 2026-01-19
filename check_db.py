import sqlite3
import os

db_path = r"C:\Users\rainwater\Desktop\puantaj\puantaj_app\data\puantaj.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=" * 60)
print("DATABASE ANALYSIS - 2026-01-19")
print("=" * 60)

print("\n📋 EXISTING TABLES:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
for (name,) in tables:
    print(f"  ✓ {name}")

print("\n👨‍💼 EMPLOYEES COUNT:")
try:
    cur.execute("SELECT COUNT(*) FROM employees")
    emp_count = cur.fetchone()[0]
    print(f"  📍 Total: {emp_count} employees")
    
    cur.execute("SELECT * FROM employees LIMIT 1")
    cols = [desc[0] for desc in cur.description]
    print(f"  Columns: {', '.join(cols)}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n📊 TIMESHEETS COUNT:")
try:
    cur.execute("SELECT COUNT(*) FROM timesheets")
    ts_count = cur.fetchone()[0]
    print(f"  📋 Total: {ts_count} records")
    
    cur.execute("SELECT * FROM timesheets LIMIT 1")
    cols = [desc[0] for desc in cur.description]
    print(f"  Columns: {', '.join(cols)}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n🚗 VEHICLES:")
try:
    cur.execute("SELECT COUNT(*) FROM vehicles")
    veh_count = cur.fetchone()[0]
    print(f"  🚗 Total: {veh_count} records")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n⚙️ SETTINGS:")
try:
    cur.execute("SELECT COUNT(*) FROM settings")
    set_count = cur.fetchone()[0]
    print(f"  ⚙️ Total: {set_count} settings")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ DATABASE SNAPSHOT COMPLETE")
print("=" * 60)

conn.close()
