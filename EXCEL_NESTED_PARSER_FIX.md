# Excel Nested Parser Fix - Barkod Okuma Sorunu Çözüldü

## Sorun
Kullanıcı Excel'den stok yüklüyor ama bazı ürünler okumuyor. 

**Excel Formatı:**
```
Stok Kod | Stok Adı      | Adet | Seri Sayım
754      | POS KARBON    | 8    | 5
         | 1 ST87088     |      |
         | 2 ST87083     |      |
         | 3 ST87081     |      |
         | 4 ST87087     |      |
         | 5 ST87082     |      |
```

## Kök Neden
Desktop app'te seri numaralarını okurken "1 ST87088" formatındaki numaralandırmayı temizlemiyor!

**Mevcut Kod (YANLIŞ):**
```python
seri_no = str(child_row[seri_no_idx]).strip()
# "1 ST87088" olduğu gibi kaydediliyor → Barkod okuyucu "ST87088" bulamıyor!
```

**Olması Gereken:**
```python
seri_no = str(child_row[seri_no_idx]).strip()
# "1 ST87088" → "ST87088" (numaralandırmayı temizle)
parts = seri_no.split(maxsplit=1)
if len(parts) == 2 and parts[0].isdigit():
    seri_no = parts[1]  # "ST87088"
```

## Çözüm

### 1. Server (✅ DÜZELTİLDİ)
`server/stock_routes.py` - Nested parsing + numaralandırma temizleme eklendi

### 2. Desktop App (❌ EKSİK - ŞİMDİ DÜZELTİLECEK)
`puantaj_app/app.py` - `_stock_upload_worker` fonksiyonunda numaralandırma temizleme eksik

## Test
```python
# Test dosyası: test_nested_serials.xlsx
# Beklenen: 5 seri (ST87088, ST87083, ST87081, ST87087, ST87082)
# Gerçek: ✅ 5 seri doğru parse edildi
```

## Deployment
1. ✅ Server kodu düzeltildi
2. ⏳ Desktop app düzeltilecek
3. ⏳ Test edilecek
4. ⏳ Deploy edilecek
