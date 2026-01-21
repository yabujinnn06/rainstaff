#!/usr/bin/env python3
"""Test stock flat list display logic"""

# Simulate database rows (like from refresh_stock_list)
db_rows = [
    ("SK001", "Motor", "SN-2024-001", "OK", "2024-01-21", "Admin", "Ankara", 1),
    ("SK001", "Motor", "SN-2024-002", "OK", "2024-01-21", "Admin", "Ankara", 1),
    ("SK001", "Motor", "SN-2024-003", "YOK", "2024-01-20", "Admin", "Ankara", 1),
    ("SK002", "Pompa", "SN-2024-101", "OK", "2024-01-21", "Admin", "Ankara", 1),
    ("SK002", "Pompa", "SN-2024-102", "FAZLA", "2024-01-21", "Admin", "Ankara", 1),
]

print("=== DESKTOP STOCK FLAT LIST FORMAT ===\n")
print("Stok Kodu | Ürün Adı | Seri No       | Durum | Tarih      | Girdi Yapan")
print("-" * 75)

# Group by stok_kod (same logic as app.py refresh_stock_list)
grouped = {}
for row in db_rows:
    stok_kod, stok_adi, seri_no, durum, tarih, girdi_yapan, bolge, adet, *_ = row
    if stok_kod not in grouped:
        grouped[stok_kod] = {
            'stok_adi': stok_adi,
            'items': []
        }
    grouped[stok_kod]['items'].append({
        'seri_no': seri_no,
        'durum': durum,
        'tarih': tarih,
        'girdi_yapan': girdi_yapan,
        'bolge': bolge,
        'adet': adet
    })

# Insert flat list - Excel gibi, tüm serileri listele
tree_data = []
for stok_kod, data in grouped.items():
    for item in data['items']:
        tag = "yok" if item['durum'] == "YOK" else "fazla" if item['durum'] == "FAZLA" else "ok"
        
        row_data = (
            stok_kod,
            data['stok_adi'] or "",
            item['seri_no'] or "",
            item['durum'] or "OK",
            item['tarih'] or "-",
            item['girdi_yapan'] or "-"
        )
        
        tag_display = f"[{tag.upper()}]"
        print(f"{row_data[0]:<12} | {row_data[1]:<8} | {row_data[2]:<13} | {row_data[3]:<5} | {row_data[4]:<10} | {row_data[5]:<12} {tag_display}")
        tree_data.append((row_data, tag))

print("\n=== VERIFICATION ===")
print(f"Total rows in treeview: {len(tree_data)}")
print(f"Unique stok_kodu: {len(grouped)}")
print(f"Expected rows: 5 (3 SK001 + 2 SK002)")
print(f"✓ PASS" if len(tree_data) == 5 else "✗ FAIL")
