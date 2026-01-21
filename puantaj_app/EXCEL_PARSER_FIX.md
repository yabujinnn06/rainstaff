# Excel Stok Yapısı FİXED ✓

## Problem Bulundu & Çözüldü

### Sorun:
Excel'in gerçek struktuRU **HİYERARŞİK** (nested):
```
Stok Kod | Stok Adı | Adet | Seri Sayım
17 | TABLET TUZ 25 KG LUK ÇUVAL | 0 | 1
  └─ Seri No 1: A084

754 | POS KARBON REVERSE OSMOS | 7 | 11
  ├─ Seri No 1: ADSBGASDG
  ├─ Seri No 2: ST87085
  ├─ Seri No 3: 754xST87083
  ... (11 total)
  └─ Seri No 11: 754xST87080
```

**Eski sistem:** Bu yapıyı okumuyor, her satırı ayrı ürün sanıyor → 42 ürün, 1 seri ✗

### Çözüm:
**Yeni parser:** Nested yapıyı doğru parse ediyor
1. Header satırını tanıdı (stok_kod dolu)
2. Tüm child satırlarını topladı (stok_kod boş)
3. Her serial = ayrı DB row, ama AYNI stok_kod ile

**Test Results:** ✓ PASS
- Ürün 1: 17 → 1 serial (A084)
- Ürün 2: 754 → 11 serials (ADSBGASDG, ST87085, ..., 754xST87080)
- **TOPLAM: 12 serial doğru şekilde**

## Database Yapısı

```
stock_inventory table:
id | stok_kod | stok_adi | seri_no | durum | tarih | ...
1  | 754 | POS KARBON REVERSE OSMOS | ADSBGASDG | OK | 2024-01-21 | ...
2  | 754 | POS KARBON REVERSE OSMOS | ST87085 | OK | 2024-01-21 | ...
3  | 754 | POS KARBON REVERSE OSMOS | 754xST87083 | OK | 2024-01-21 | ...
...
12 | 754 | POS KARBON REVERSE OSMOS | 754xST87080 | OK | 2024-01-21 | ...
```

Her serial = **ayrı row**

## Display

### Desktop App (flat list):
```
Stok Kodu | Ürün Adı | Seri No | Durum | Tarih | Girdi Yapan
754 | POS KARBON REVERSE OSMOS | ADSBGASDG | OK | 2024-01-21 | system
754 | POS KARBON REVERSE OSMOS | ST87085 | OK | 2024-01-21 | system
754 | POS KARBON REVERSE OSMOS | 754xST87083 | OK | 2024-01-21 | system
...
```

### Web Site (grouped + expandable):
```
754 POS KARBON REVERSE OSMOS ▼
  1. ADSBGASDG
  2. ST87085
  3. 754xST87083
  ...
  11. 754xST87080
```

## Kod Değişiklikleri

**File:** `app.py` - `_stock_upload_worker()` method

### Eski (YANLIŞ):
```python
for row in rows[1:]:
    stok_kod = row[0]
    seri_no = row[2]
    # Her satır = ayrı ürün
    INSERT INTO stock_inventory (stok_kod, seri_no, ...)
```

### Yeni (DOĞRU):
```python
i = 1
while i < len(rows):
    row = rows[i]
    if stok_kod not empty:
        # Header = Ürün başlığı
        stok_adi = row[1]
        i += 1
        
        while i < len(rows) and child_stok_kod is empty:
            # Child = Serial numarası
            seri_no = child_row[2]  # ACTUAL serial (ADSBGASDG, ST87085, etc.)
            INSERT INTO stock_inventory (stok_kod, stok_adi, seri_no, ...)
            i += 1
```

## Deployment Status

✓ Code committed (commit 335e8f1)
✓ Pushed to GitHub (main branch)
⏳ Render auto-deploy in progress (2-3 min)

## Test edilecek:

1. Desktop app açılır
2. `test_stok.xlsx` upload edilir
3. Stock tab'da görülür:
   - Stok 17: 1 seri
   - Stok 754: 11 seri (hepsi görülmeli)
4. Site açılır (`/stock`)
   - 754'ü tıkla → 11 serial genişle

## Dosyalar

- Desktop parser: `app.py` (line 5302-5368)
- Server API: `server/app.py` (line 228-274)
- Site template: `server/templates/stock.html`
- Test Excel: `C:\Users\rainwater\Desktop\test_stok.xlsx`

---

**Özet:** Sistem şimdi Excel'in gerçek depo yapısını anlıyor - **her ürünün birden fazla seri numarası var ve hepsi görülüyor.**
