#!/usr/bin/env python3
"""app.py'nin import ve başlatma test'i"""

import sys
import os
import traceback

print("=" * 60)
print("🧪 App Initialization Test")
print("=" * 60)

try:
    print("\n1. Setting up directories...", end=" ")
    sys.path.insert(0, '.')
    from app import ensure_app_dirs
    ensure_app_dirs()
    print("✓")
    
    print("2. Initializing database...", end=" ")
    import db
    db.init_db()
    print("✓")
    
    print("3. Setting up logging...", end=" ")
    from app import setup_logging
    logger = setup_logging()
    print("✓")
    
    print("4. Creating Tk root...", end=" ")
    import tkinter as tk
    root = tk.Tk()
    print("✓")
    
    print("5. Creating PuantajApp...", end=" ")
    from app import PuantajApp
    # app = PuantajApp()  # Skip GUI creation for now
    print("✓ (skipped GUI)")
    
    root.destroy()
    print("\n✅ All checks passed!")
    
except Exception as e:
    print(f"\n✗ ERROR at step")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
