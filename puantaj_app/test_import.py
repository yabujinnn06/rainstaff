#!/usr/bin/env python3
"""Test eski Tkinter uygulamasının import'larını"""

import sys
import traceback

print("🔍 Importing modules...")

try:
    print("  - db.py...", end=" ")
    import db
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - calc.py...", end=" ")
    import calc
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - report.py...", end=" ")
    import report
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

try:
    print("  - app.py...", end=" ")
    import app
    print("✓")
except Exception as e:
    print(f"✗ HATA: {e}")
    traceback.print_exc()

print("\n✅ Tüm import'lar başarılı!")
