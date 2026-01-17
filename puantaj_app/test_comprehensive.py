#!/usr/bin/env python3
"""Kapsamlı sistem test - Database, hesaplamalar, fonksiyonlar"""

import sys
import os
import traceback
from datetime import datetime, timedelta
import tempfile
import shutil

# Setup path
sys.path.insert(0, '.')

print("=" * 60)
print("🧪 RAINSTAFF SYSTEM COMPREHENSIVE TEST")
print("=" * 60)

tests_passed = 0
tests_failed = 0

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            try:
                print(f"\n📋 {name}...", end=" ")
                func()
                print("✓")
                tests_passed += 1
            except Exception as e:
                print(f"✗ FAILED")
                print(f"   Error: {e}")
                traceback.print_exc()
                tests_failed += 1
        return wrapper
    return decorator

# ============ DATABASE TESTS ============
@test("DB Module Import")
def test_db_import():
    global db
    import db
    assert hasattr(db, 'get_conn'), "get_conn missing"
    assert hasattr(db, 'init_db'), "init_db missing"

@test("DB Initialization")
def test_db_init():
    import db
    db.ensure_db_dir()
    assert os.path.isdir(db.DB_DIR), f"DB dir not created: {db.DB_DIR}"

@test("DB Connection & Timeout")
def test_db_connection():
    import db
    with db.get_conn() as conn:
        result = conn.execute("SELECT 1").fetchone()
        assert result is not None, "DB connection failed"

@test("DB Schema Tables")
def test_db_schema():
    import db
    db.init_db()
    with db.get_conn() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        required = ['employees', 'timesheets', 'users', 'settings']
        for tbl in required:
            assert tbl in table_names, f"Table {tbl} missing"

# ============ CALC TESTS ============
@test("Calc Module Import")
def test_calc_import():
    global calc
    import calc
    assert hasattr(calc, 'calc_day_hours'), "calc_day_hours missing"
    assert hasattr(calc, 'parse_date'), "parse_date missing"
    assert hasattr(calc, 'parse_time'), "parse_time missing"

@test("Parse Date Function")
def test_parse_date():
    import calc
    # ISO format
    d1 = calc.parse_date("2026-01-18")
    assert d1.year == 2026 and d1.month == 1 and d1.day == 18
    # Turkish format
    d2 = calc.parse_date("18.01.2026")
    assert d2.year == 2026 and d2.month == 1 and d2.day == 18

@test("Parse Time Function")
def test_parse_time():
    import calc
    t = calc.parse_time("09:30")
    assert t.hour == 9 and t.minute == 30

@test("Calc Day Hours - Normal")
def test_calc_hours_normal():
    import calc
    settings = {"weekday_hours": "9", "saturday_start": "09:00", "saturday_end": "14:00"}
    result = calc.calc_day_hours("2026-01-14", "09:00", "17:00", 60, settings, is_special=0)
    # result = (worked, scheduled, overtime, night, overnight, special_normal, special_ot, special_night)
    worked, scheduled, overtime, night, overnight, sn, so, snight = result
    assert worked == 7.0, f"Expected 7.0h worked, got {worked}"
    assert scheduled == 9.0, f"Expected 9.0h scheduled, got {scheduled}"

@test("Calc Day Hours - Overtime")
def test_calc_hours_overtime():
    import calc
    settings = {"weekday_hours": "9", "saturday_start": "09:00", "saturday_end": "14:00"}
    result = calc.calc_day_hours("2026-01-14", "09:00", "19:00", 60, settings, is_special=0)
    worked, scheduled, overtime, night, overnight, sn, so, snight = result
    assert overtime > 0, f"Expected overtime, got {overtime}"

@test("Calc Day Hours - Special Day")
def test_calc_hours_special():
    import calc
    settings = {"weekday_hours": "9", "saturday_start": "09:00", "saturday_end": "14:00"}
    result = calc.calc_day_hours("2026-01-14", "09:00", "17:00", 60, settings, is_special=1)
    worked, scheduled, overtime, night, overnight, sn, so, snight = result
    assert scheduled == 0.0, f"Special day should have 0 scheduled, got {scheduled}"

@test("Calc Day Hours - Break Validation")
def test_calc_hours_break():
    import calc
    settings = {"weekday_hours": "9", "saturday_start": "09:00", "saturday_end": "14:00"}
    # Break > gross hours (should be capped)
    result = calc.calc_day_hours("2026-01-14", "09:00", "10:00", 120, settings, is_special=0)
    worked, scheduled, overtime, _, _, _, _, _ = result
    assert worked >= 0, f"Worked hours should not be negative, got {worked}"

# ============ APP UTILITY TESTS ============
@test("App Normalize Date")
def test_app_normalize_date():
    from app import normalize_date
    assert normalize_date("2026-01-18") == "2026-01-18"
    assert normalize_date("18.01.2026") == "2026-01-18"

@test("App Normalize Time")
def test_app_normalize_time():
    from app import normalize_time
    assert normalize_time("09:30") == "09:30"
    assert normalize_time("930") == "09:30"

@test("App Normalize Vehicle Status")
def test_app_normalize_status():
    from app import normalize_vehicle_status
    assert normalize_vehicle_status("Olumsuz") == "Olumsuz"
    assert normalize_vehicle_status("Olumlu") == "Olumlu"
    assert normalize_vehicle_status(None) == "Belirsiz"
    assert normalize_vehicle_status("bad") == "Olumsuz"
    assert normalize_vehicle_status("good") == "Olumlu"

# ============ REPORT TESTS ============
@test("Report Module Import")
def test_report_import():
    global report
    import report
    assert hasattr(report, 'export_report'), "export_report missing"

@test("Report Export (Minimal)")
def test_report_export():
    import report
    import tempfile
    
    # Create minimal test data
    records = [
        (1, 1, "Test User", "2026-01-14", "09:00", "17:00", 60, 0, "Test note", "Ankara"),
    ]
    settings = {
        "company_name": "Test Co",
        "report_title": "Test Report",
        "logo_path": "",
    }
    
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        report.export_report(tmp_path, records, settings, "2026-01-14")
        assert os.path.isfile(tmp_path), "Report file not created"
        assert os.path.getsize(tmp_path) > 1000, "Report file too small"
    finally:
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)

# ============ RUN TESTS ============
if __name__ == "__main__":
    # Database tests
    test_db_import()
    test_db_init()
    test_db_connection()
    test_db_schema()
    
    # Calc tests
    test_calc_import()
    test_parse_date()
    test_parse_time()
    test_calc_hours_normal()
    test_calc_hours_overtime()
    test_calc_hours_special()
    test_calc_hours_break()
    
    # App utility tests
    test_app_normalize_date()
    test_app_normalize_time()
    test_app_normalize_status()
    
    # Report tests
    test_report_import()
    test_report_export()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✓ PASSED: {tests_passed}")
    print(f"✗ FAILED: {tests_failed}")
    print("=" * 60)
    
    if tests_failed == 0:
        print("\n✅ All tests passed! System is ready.")
        sys.exit(0)
    else:
        print(f"\n❌ {tests_failed} test(s) failed. Fix before build.")
        sys.exit(1)
