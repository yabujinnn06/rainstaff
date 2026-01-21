#!/usr/bin/env python3
"""
Minimal test to verify stock treeview displays flat list correctly
"""
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Stock Treeview Flat List Test")
root.geometry("800x400")

# Create treeview with 6 columns (same as app.py)
columns = ("stok_kod", "stok_adi", "seri_no", "durum", "tarih", "girdi_yapan")
tree = ttk.Treeview(root, columns=columns, show="headings", height=20)

tree.heading("stok_kod", text="Stok Kodu")
tree.heading("stok_adi", text="Ürün Adı")
tree.heading("seri_no", text="Seri No")
tree.heading("durum", text="Durum")
tree.heading("tarih", text="Tarih")
tree.heading("girdi_yapan", text="Girdi Yapan")

tree.column("stok_kod", width=100, anchor="w")
tree.column("stok_adi", width=180, anchor="w")
tree.column("seri_no", width=140, anchor="w")
tree.column("durum", width=80, anchor="center")
tree.column("tarih", width=100, anchor="center")
tree.column("girdi_yapan", width=100, anchor="w")

tree.tag_configure("ok", background="#1f1f1f", foreground="#6db66d")
tree.tag_configure("yok", background="#1f1f1f", foreground="#ff6b6b")
tree.tag_configure("fazla", background="#1f1f1f", foreground="#ffeb99")

# Sample data
sample_data = [
    ("SK001", "Motor", "SN-2024-001", "OK", "2024-01-21", "Admin", "ok"),
    ("SK001", "Motor", "SN-2024-002", "OK", "2024-01-21", "Admin", "ok"),
    ("SK001", "Motor", "SN-2024-003", "YOK", "2024-01-20", "Admin", "yok"),
    ("SK002", "Pompa", "SN-2024-101", "OK", "2024-01-21", "Admin", "ok"),
    ("SK002", "Pompa", "SN-2024-102", "FAZLA", "2024-01-21", "Admin", "fazla"),
]

# Insert flat rows
for row_data, tag in sample_data:
    tree.insert("", tk.END, values=row_data, tags=(tag,))

tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Info label
info = tk.Label(root, text=f"✓ Treeview loaded with {len(sample_data)} rows (flat list, not hierarchical)")
info.pack(pady=5)

root.mainloop()
