#!/usr/bin/env python3
"""
Database Migration Script for Rainstaff Sync System
- Adds region column to timesheets
- Creates missing tables (vehicles, drivers, users, etc)
- Populates default data
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = r"C:\Users\rainwater\Desktop\puantaj\puantaj_app\data\puantaj.db"

def execute_sql(conn, sql):
    """Execute SQL with error handling"""
    try:
        conn.execute(sql)
        conn.commit()
        return True, "OK"
    except sqlite3.Error as e:
        return False, str(e)

def migrate_database():
    """Execute all migrations"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    
    print("=" * 70)
    print("🔄 DATABASE MIGRATION - Rainstaff Sync System")
    print("=" * 70)
    
    migrations = [
        ("Add region column to timesheets", """
            ALTER TABLE timesheets ADD COLUMN region TEXT DEFAULT 'Ankara';
        """),
        
        ("Create vehicles table", """
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT NOT NULL UNIQUE,
                brand TEXT,
                model TEXT,
                year TEXT,
                km INTEGER,
                inspection_date TEXT,
                insurance_date TEXT,
                maintenance_date TEXT,
                oil_change_date TEXT,
                oil_change_km INTEGER,
                oil_interval_km INTEGER,
                notes TEXT
            );
        """),
        
        ("Create drivers table", """
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                license_class TEXT,
                license_expiry TEXT,
                phone TEXT,
                notes TEXT
            );
        """),
        
        ("Create users table", """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                region TEXT NOT NULL
            );
        """),
        
        ("Create reports table", """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                created_at TEXT,
                employee TEXT,
                start_date TEXT,
                end_date TEXT
            );
        """),
        
        ("Create vehicle_faults table", """
            CREATE TABLE IF NOT EXISTS vehicle_faults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                opened_date TEXT,
                closed_date TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            );
        """),
        
        ("Create vehicle_service_visits table", """
            CREATE TABLE IF NOT EXISTS vehicle_service_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                service_date TEXT,
                description TEXT,
                cost REAL,
                km_at_service INTEGER,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            );
        """),
        
        ("Create vehicle_inspections table", """
            CREATE TABLE IF NOT EXISTS vehicle_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                inspection_date TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            );
        """),
        
        ("Create vehicle_inspection_results table", """
            CREATE TABLE IF NOT EXISTS vehicle_inspection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                status TEXT,
                notes TEXT,
                FOREIGN KEY (inspection_id) REFERENCES vehicle_inspections (id) ON DELETE CASCADE
            );
        """),
    ]
    
    success_count = 0
    fail_count = 0
    
    for name, sql in migrations:
        success, msg = execute_sql(conn, sql)
        if success:
            print(f"  ✅ {name}")
            success_count += 1
        else:
            # Check if it's "already exists" error (safe to ignore)
            if "already exists" in msg or "duplicate column" in msg:
                print(f"  ℹ️  {name} (already exists)")
                success_count += 1
            else:
                print(f"  ❌ {name}: {msg}")
                fail_count += 1
    
    # Insert default users if table exists and is empty
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        
        if user_count == 0:
            print("\n  📝 Populating default users...")
            default_users = [
                ("ankara1", "060106", "user", "Ankara"),
                ("istanbul1", "340434", "user", "Istanbul"),
                ("bursa1", "160316", "user", "Bursa"),
                ("izmir1", "350235", "user", "Izmir"),
                ("admin", "748774", "admin", "ALL"),
            ]
            
            # Passwords should be hashed in production - for now using as-is for demo
            for username, pwd, role, region in default_users:
                try:
                    conn.execute(
                        "INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)",
                        (username, pwd, role, region)  # In production: hash(pwd)
                    )
                    print(f"    ✓ {username:15} | role: {role:10} | region: {region}")
                except sqlite3.IntegrityError:
                    pass  # Already exists
            
            conn.commit()
    except Exception as e:
        print(f"  ⚠️  Could not populate users: {e}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"✅ MIGRATION COMPLETE: {success_count} changes, {fail_count} errors")
    print("=" * 70)
    
    return fail_count == 0

if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
