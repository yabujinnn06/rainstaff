import os
import sys

# Simulate Linux/Server environment (no APPDATA)
if 'APPDATA' in os.environ:
    del os.environ['APPDATA']

# Set typical server structure
# Root is current dir
os.makedirs("puantaj_app/data", exist_ok=True)

print("Current Working Directory:", os.getcwd())
print("OS Name:", os.name)

# Import db module to see where it points
sys.path.insert(0, os.path.abspath("puantaj_app"))
# Create a dummy db.py inside puantaj_app if not importing from real one
# But we will use the real one by importing from file path

import importlib.util
spec = importlib.util.spec_from_file_location("db", "puantaj_app/db.py")
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)

print("-" * 50)
print("APP_NAME:", db.APP_NAME)
print("LOCAL_DB_DIR:", db.LOCAL_DB_DIR)
# print("APPDATA_DIR:", db.APPDATA_DIR) # Might fail if APPDATA is missing in original code logic
print("DB_DIR:", db.DB_DIR)
print("DB_PATH:", db.DB_PATH)
print("-" * 50)
