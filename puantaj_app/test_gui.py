#!/usr/bin/env python3
"""Test Tkinter GUI initialization"""

import tkinter as tk
from tkinter import ttk
import sys
import traceback

print("🔍 Testing Tkinter initialization...")

try:
    print("  - Creating Tk root...", end=" ")
    root = tk.Tk()
    root.title("Rainstaff - Test")
    root.geometry("400x300")
    print("✓")
    
    print("  - Creating Frame...", end=" ")
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    print("✓")
    
    print("  - Creating Label...", end=" ")
    label = ttk.Label(frame, text="✅ Tkinter test başarılı!")
    label.pack()
    print("✓")
    
    print("  - Creating Button...", end=" ")
    btn = ttk.Button(frame, text="Kapat", command=root.quit)
    btn.pack(pady=10)
    print("✓")
    
    print("\n✅ GUI initialization başarılı!")
    print("📌 5 saniye içinde otomatik kapanacak...")
    root.after(5000, root.quit)
    root.mainloop()
    
except Exception as e:
    print(f"\n✗ HATA: {e}")
    traceback.print_exc()
    sys.exit(1)
