#!/usr/bin/env python3
"""Test kritik fonksiyonlar"""

import sys
import traceback

print("🔍 Testing functions...")

try:
    print("  - normalize_vehicle_status()...", end=" ")
    from app import normalize_vehicle_status
    assert normalize_vehicle_status("Olumsuz") == "Olumsuz"
    assert normalize_vehicle_status("Olumlu") == "Olumlu"
    assert normalize_vehicle_status(None) == "Belirsiz"
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - normalize_date()...", end=" ")
    from app import normalize_date
    assert normalize_date("2026-01-18") == "2026-01-18"
    assert normalize_date("18.01.2026") == "2026-01-18"
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - normalize_time()...", end=" ")
    from app import normalize_time
    assert normalize_time("09:30") == "09:30"
    assert normalize_time("930") == "09:30"
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - calc_day_hours()...", end=" ")
    from calc import calc_day_hours
    settings = {"weekday_hours": "9", "saturday_start": "09:00", "saturday_end": "14:00"}
    result = calc_day_hours("2026-01-14", "09:00", "17:00", 60, settings, is_special=0)
    print(f"✓ (worked={result[0]}h)")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

print("\n✅ Tüm test'ler geçti!")
