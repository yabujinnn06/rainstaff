#!/usr/bin/env python3
"""Test the nested Excel parsing logic"""
import openpyxl
from datetime import datetime

# Load test Excel
excel_path = r"C:\Users\rainwater\Desktop\test_stok.xlsx"
wb = openpyxl.load_workbook(excel_path)
ws = wb.active

# Convert to list of rows
rows = []
for row in ws.iter_rows(values_only=True):
    rows.append(list(row))

print(f"Total rows in Excel: {len(rows)}")
print(f"\nRaw rows:")
for i, row in enumerate(rows):
    print(f"  Row {i}: {row}")

# Parse headers
headers = [str(h).strip().lower() if h else '' for h in rows[0]]
print(f"\nHeaders: {headers}")

stok_kod_idx = 0  # "Stok Kod"
stok_adi_idx = 1  # "Stok Adı"
seri_no_idx = 2   # Column C (Adet/Seri No)
seri_sayi_idx = 3 # Column D (Seri Sayım)

# Parse nested structure
print(f"\n=== PARSING NESTED STRUCTURE ===")
imported = 0
products = []

i = 1
while i < len(rows):
    row = rows[i]
    stok_kod = str(row[stok_kod_idx]).strip() if stok_kod_idx < len(row) and row[stok_kod_idx] else ''
    
    print(f"\nRow {i}: stok_kod='{stok_kod}' (is_header={bool(stok_kod)})")
    
    if stok_kod and stok_kod not in ['', 'nan', 'None', None]:
        # Product header
        stok_adi = str(row[stok_adi_idx]).strip() if stok_adi_idx < len(row) else ''
        seri_sayi = 0
        try:
            seri_sayi = int(row[seri_sayi_idx]) if seri_sayi_idx < len(row) and row[seri_sayi_idx] else 0
        except (ValueError, TypeError):
            pass
        
        print(f"  → Product header: {stok_kod} | {stok_adi} ({seri_sayi} serials)")
        
        # Collect child seri_no rows
        i += 1
        seri_count = 0
        while i < len(rows):
            child_row = rows[i]
            child_stok_kod = str(child_row[stok_kod_idx]).strip() if stok_kod_idx < len(child_row) and child_row[stok_kod_idx] else ''
            
            print(f"    Child Row {i}: child_stok_kod='{child_stok_kod}'")
            
            if not child_stok_kod or child_stok_kod in ['', 'nan', 'None', None]:
                # Serial row
                seri_no = str(child_row[seri_no_idx]).strip() if seri_no_idx < len(child_row) and child_row[seri_no_idx] else ''
                
                if seri_no and seri_no not in ['', 'nan', 'None', None]:
                    print(f"      ✓ Serial: {seri_no}")
                    products.append({
                        'stok_kod': stok_kod,
                        'stok_adi': stok_adi,
                        'seri_no': seri_no,
                        'durum': 'OK'
                    })
                    imported += 1
                    seri_count += 1
                
                i += 1
            else:
                # Next product header
                print(f"    → Next product header found")
                break
    else:
        i += 1

print(f"\n\n=== RESULT ===")
print(f"✓ Imported {imported} serials across {len(set(p['stok_kod'] for p in products))} products\n")

for product in products:
    print(f"{product['stok_kod']:<8} | {product['stok_adi']:<30} | {product['seri_no']:<20}")

print(f"\n=== VERIFICATION ===")
print(f"Expected: 1 (17) + 11 (754) = 12 total serials")
print(f"Actual:   {imported} serials")
print(f"Status:   {'✓ PASS' if imported == 12 else '✗ FAIL'}")
