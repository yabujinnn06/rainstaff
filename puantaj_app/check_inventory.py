import sqlite3
import os

db_path = os.path.expandvars(r'%APPDATA%\Rainstaff\data\puantaj.db')
if not os.path.exists(db_path):
    print(f"❌ DB bulunamadı: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check total records
cursor.execute('SELECT COUNT(*), COUNT(DISTINCT stok_kod) FROM stock_inventory')
total, unique = cursor.fetchone()
print(f"\n📊 TOPLAM: {total} seri no | {unique} farklı ürün\n")

# Show summary by product
cursor.execute('SELECT stok_kod, stok_adi, COUNT(*) as seri_sayisi FROM stock_inventory GROUP BY stok_kod ORDER BY stok_kod')
print("ÜRÜN\t\t\tSERİ SAYISI")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[0]:<8} {row[1]:<20} {row[2]:>3}")

# Show sample records
print("\n\n=== ÖRNEK VERİLER ===")
cursor.execute('SELECT stok_kod, stok_adi, seri_no, durum FROM stock_inventory LIMIT 10')
print("STOK_KODU\tÜRÜN_ADI\t\tSERİ_NO\t\tDURUM")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:<10}\t{row[1]:<15}\t{row[2]:<15}\t{row[3]}")

conn.close()
