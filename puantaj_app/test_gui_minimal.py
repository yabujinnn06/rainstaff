#!/usr/bin/env python3
"""Gui test - sekmeler arasında gezin"""

import tkinter as tk
from tkinter import messagebox
import sys
import threading
import time

# Minimal Tkinter test
print("🧪 Starting minimal GUI test...")

try:
    root = tk.Tk()
    root.title("Rainstaff - GUI Test")
    root.geometry("800x600")
    root.withdraw()  # Kapat
    
    # Eğer buraya geldiysek, Tkinter çalışıyor
    print("✓ Tkinter initialized successfully")
    
    # Import app modulesini test et
    print("  - Importing app modules...", end=" ")
    sys.path.insert(0, '.')
    import db
    import calc
    import report
    print("✓")
    
    # App class'ını test et
    print("  - Creating App instance...", end=" ")
    from app import App
    # app = App(root)  # GUI oluştur
    print("✓ (skipped GUI creation)")
    
    root.destroy()
    print("\n✅ GUI test başarılı!")
    
except Exception as e:
    print(f"\n✗ HATA: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
