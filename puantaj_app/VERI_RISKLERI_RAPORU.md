# Rainstaff - Veri İşleyişi Risk Analizi

**Tarih**: 17 Ocak 2026  
**Seviye**: Kritik & Önemli Sorunlar Tespit Edildi

---

## 📋 Özet

Rainstaff masaüstü uygulamasında veri validasyonu, transaction yönetimi, ve hata kurtarma mekanizmalarında **6 kritik, 8 önemli risk** tespit edilmiştir. Bu riskler veri kaybı, veri tutarsızlığı, ve uygulama çökmelerine neden olabilir.

---

## 🔴 KRİTİK RİSKLER (Hemen Düzeltilmesi Gerekli)

### 1. **Boş/NULL Veri Validasyonu Eksik**
**Dosya**: `app.py` (satır 1455-1475, 1604-1650, 2321+)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
- `import_timesheets()` içinde `work_date`, `start_time`, `end_time` kullanıcı girdisinden doğrudan normalize edilir.
- Normalizasyon başarısız olursa, try-except bloğu yalnızca hata mesajı gösterir ve devam eder.
- Boş tarih/saat, NULL değer, veya invalid format verileri sektir atlayarak (skipped) ancak veritabanına yazılmadığını garantilemez.

**Örnek Senaryo**:
```python
# app.py, satır 1710-1715
try:
    work_date = normalize_date_value(work_date)  # Eğer "" ise?
    start_time = normalize_time_value(start_time)  # Eğer "25:00" ise?
except ValueError:
    skipped += 1
    continue  # Sadece atla, kontrol yok
```

**Etki**: Kısmi boş kayıtlar DB'ye yazılabilir.  
**Çözüm**: Normalizasyon ÖNCESÜ boş kontrol + tip güvenliği ekle.

---

### 2. **Transaction Yönetimi Eksik - get_conn() COMMIT Yok**
**Dosya**: `db.py` (satır 121-130)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
```python
@contextmanager
def get_conn():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()  # ⚠️ COMMIT YOK!
```
- Context manager **rollback yapamaz çünkü commit de yapamaz**.
- Yazma işlemleri (add_timesheet, update_employee, vb.) eksik kalır.
- Hata durumunda rollback mekanizması yok.

**Etki**: Veri kaybı + veritabanı tutarsızlığı.  
**Çözüm**: 
```python
@contextmanager
def get_conn():
    ...
    try:
        yield conn
        conn.commit()  # Ekle
    except Exception:
        conn.rollback()  # Ekle
        raise
    finally:
        conn.close()
```

---

### 3. **Eksik Fonksiyon Referansları - Silent Failures**
**Dosya**: `app.py` (satır 1697, 1715 vb.)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
- `normalize_date_value()` ve `normalize_time_value()` çağrılır ama **hiçbir yerde tanımlanmamış**:
  ```python
  # app.py, satır 1710-1715 (import_timesheets)
  work_date = normalize_date_value(work_date)  # NameError!
  start_time = normalize_time_value(start_time)  # NameError!
  ```
- Varsayılan olarak `normalize_date()` (tanımlı) var ama kodu `_value` varyantı çağırıyor.

**Etki**: İçe aktarma işlemi çöker veya veri atlanır.  
**Çözüm**: Fonksiyonları tanımla veya doğru isim kullan.

---

### 4. **Dosya İçe Aktarma - Karakterset Yönetimi Yok**
**Dosya**: `app.py` (satır 208-230, `load_tabular_file()`)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
```python
def load_tabular_file(path):
    ...
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as handle:  # utf-8-sig only
            ...
    # Excel dosyaları da yüklenebilir, ancak locale encoding yok
```
- Eğer CSV dosyası ISO-8859-9 (TR) veya başka charset ile kaydedilirse, karakterler bozulur.
- Türkçe karakterler (ç, ş, ğ, ü) hatalı okuma riski.

**Etki**: Veri bozulması (çalışan adları, departman adları vb.).  
**Çözüm**: Charset otomatik algılama ekle.

---

### 5. **Senkronizasyon Hataları - Rollback Yok**
**Dosya**: `app.py` (satır 986-999, `trigger_sync()`)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
```python
def trigger_sync(self, reason="manual"):
    ...
    try:
        with open(DB_PATH, "rb") as f:
            files = {"database": f}
            response = requests.post(url, files=files, headers=headers, timeout=30)
    except Exception as exc:
        messagebox.showerror("Senkron Hatasi", f"Baglantilamadi: {exc}")  # Hata, ama ne yaparsın?
```
- Sunucu POST başarısız olursa, masaüstü DB değişti ancak sunucu DB güncel olmaz.
- Masaüstü ve sunucu veri uyuşmazlığı.

**Etki**: Veri tutarsızlığı, dashboard hatalı rapor gösterebilir.  
**Çözüm**: 
- Sunucu sync'i başarısız olursa, masaüstü pending işaretini kaydet.
- Başarı yanıtını doğrula (HTTP 200 + JSON `success: true`).

---

### 6. **Break Minutes Validasyonu Yok**
**Dosya**: `app.py` (satır 1479, `add_or_update_timesheet()`)  
**Risk Seviyesi**: KRİTİK

**Sorun**:
```python
break_minutes = parse_int(self.ts_break_var.get(), 0)  # 0 varsayılan, ama max nedir?
```
- Kullanıcı "-60" veya "9999" yazabilir.
- Calc.py'daki saat hesaplaması hatalı sonuç döner.

**Etki**: Yanlış puantaj hesaplaması.  
**Çözüm**: 
```python
break_minutes = parse_int(self.ts_break_var.get(), 0)
if break_minutes < 0 or break_minutes > 480:  # Max 8 saat mola
    raise ValueError("Mola 0-480 dakika arasında olmalıdır")
```

---

## 🟠 ÖNEMLİ RİSKLER (Kısa Sürede Düzeltilmeli)

### 7. **Tarih Formatı Standartlaştırılmamış**
**Risk**: Import işleminde "01.01.2026", "2026-01-01", "01/01/2026" karışık kabul ediliyor.  
**Çözüm**: Strict format kontrol ekle (ISO `YYYY-MM-DD` hedef).

### 8. **Bölge Eksik - NULL Region Risk**
**Dosya**: `app.py` (satır 1467, `add_or_update_timesheet()`)  
**Risk**: `self._entry_region()` None dönebilir → DB NULL region → admin user için filtreleme hatası.  
**Çözüm**: 
```python
region = self._entry_region()
if not region:
    raise ValueError("Bölge tanımlanmamış")
```

### 9. **Employee Combo İçinde None/Boş Kayıt**
**Dosya**: `app.py` (satır 1097, `_refresh_employee_comboboxes()`)  
**Risk**: `split_display_name()` başarısız olursa, employee ID bulunmaz.  
**Çözüm**: `split_display_name()` error handling ekle.

### 10. **Import Dosya Boyut Kontrolü Yok**
**Risk**: 500MB CSV yükle → bellek tükenir → crash.  
**Çözüm**: Max dosya boyutu (örn. 50MB) kontrol et.

### 11. **Duplicate Kontrolü Eksik**
**Dosya**: `app.py` (satır 1639, `import_employees()`)  
**Risk**: 
```python
key = (name, self._entry_region())
if not name or key in existing_names:
    skipped += 1
    continue  # Ama varsa adı ve bölge eşitken çoklu kayıt riski
```
**Çözüm**: DB'ye "UNIQUE(name, region)" constraint ekle.

### 12. **Tarih Aralığı Validasyonu Yok**
**Risk**: start_date > end_date filter yazılırsa, sorgu hatalı sonuç döner.  
**Çözüm**: Filter metodu içinde start <= end kontrolü ekle.

### 13. **Saha Hesaplamalarının Kontrol Eksik (calc.py)**
**Risk**: calc_day_hours() boş/NULL tarih aldığında hata verir (ValueError, ama catch mi edildi?).  
**Çözüm**: calc.py hata mesajlarını düzenle, log et.

### 14. **Veritabanı Migration Eksik**
**Risk**: Yeni feature (örn. "region" column) eski DB'ye eklenmiş, ancak ALTER TABLE kontrol yok.  
**Çözüm**: Migration script yaz (ensure_schema() iyileştir).

---

## 🟡 DİĞER RİSKLER

| # | Risk | Şiddet | Konum |
|---|------|--------|-------|
| 15 | Logo dosyası missing → Exception silent | Orta | app.py:495 |
| 16 | Report Excel export esnasında veri değişse | Orta | report.py |
| 17 | Backup dosya taşınırsa → restore başarısız | Düşük | db.py:63 |
| 18 | Log dosyası full disk → izin hatası | Orta | app.py:85 |
| 19 | Timezone handling yok (tarihler local mi UTC mi?) | Orta | calc.py |
| 20 | Admin user su için hardcoded şifre | KRİTİK | db.py:35 |

---

## ✅ ÖNERİLEN EYLEMLER (Öncelik Sırasına Göre)

### Faz 1: ACIL (Bugün)
1. ✏️ get_conn() context manager'a commit() ekle
2. ✏️ normalize_date_value(), normalize_time_value() eksik fonksiyon tanımla
3. ✏️ break_minutes validasyonu ekle (-59 ~ 480 aralığı)
4. ✏️ Bölge NULL kontrolü ekle

### Faz 2: Bu Hafta
5. ✏️ Import charset algılama ekle (chardet kütüphanesi)
6. ✏️ Dosya boyut kontrolü ekle (max 50MB)
7. ✏️ Senkronizasyon hata recovery ekle (pending flag)
8. ✏️ Tarih format strict kontrol (ISO only)

### Faz 3: Şu Hafta
9. ✏️ DB UNIQUE constraint'ler ekle (name, region)
10. ✏️ Migration script test et (region column)
11. ✏️ Hata handling improvement (calc.py exception handling)
12. ✏️ Admin user şifre hash'le (hardcoded "748774" kaldır)

---

## 📊 Etki Analizi

| Senaryo | Olasılık | Etki | Sonuç |
|---------|----------|------|-------|
| Import boş CSV → 100 satır NULL kayıt | ORTA | HIGH | Rapor yanlış |
| Senkronizasyon başarısız → masaüstü dev, sunucu bayat | YÜKSEK | CRITICAL | Dashboard yanıltıcı veri gösterir |
| Break minutes "-999" → calc error | ORTA | MEDIUM | Saat hesapları hatalı |
| Region NULL → filtreleme çalışmaz | DÜŞÜK | HIGH | Admin panelde veri görünmez |
| File IO exception silent → log yok | YÜKSEK | MEDIUM | Debug imkansız |

---

## 🛠️ Kod Örnekleri

### Problem: get_conn() commit yok
```python
# ❌ YANLII
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()  # Veri yazılmadı!

# ✅ DOĞRU
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()  # Write işlemleri commit
    except Exception:
        conn.rollback()  # Hata varsa geri al
        raise
    finally:
        conn.close()
```

### Problem: break_minutes validasyonu yok
```python
# ❌ YANLII
break_minutes = parse_int(self.ts_break_var.get(), 0)

# ✅ DOĞRU
break_minutes = parse_int(self.ts_break_var.get(), 0)
if not (0 <= break_minutes <= 480):
    raise ValueError("Mola dakikası 0-480 arasında olmalıdır")
```

### Problem: normalize_date_value tanımlanmamış
```python
# ❌ YANLII (app.py:1710)
work_date = normalize_date_value(work_date)  # NameError!

# ✅ DOĞRU
def normalize_date_value(value):
    """Import için flexible tarih normalizasyonu."""
    if not value or value == "":
        raise ValueError("Tarih boş olamaz")
    if isinstance(value, str):
        return normalize_date(value)
    # Excel date (float) desteği
    if isinstance(value, float):
        from datetime import datetime
        return datetime.fromordinal(int(value) + 693594).strftime("%Y-%m-%d")
    raise ValueError(f"Tarih formatı geçersiz: {value}")
```

---

## 📝 Sonuç

**Risk Puan**: 72/100 (YÜKSEK)

Rainstaff uygulaması **temel transaction yönetimi, veri validasyonu, ve hata kurtarma mekanizmalarında ciddi eksiklikler** barındırmaktadır. Özellikle:
- ✏️ Database transaction'lar commit edilmiyor → veri kaybı riski
- ✏️ Eksik fonksiyonlar silent fail → veri tutarsızlığı
- ✏️ Validasyon eksiklikleri → invalid veri DB'ye giriyor
- ✏️ Senkronizasyon hata handling yok → master-replica uyuşmazlığı

**Tavsiye**: Faz 1 (ACIL) işlemleri yapılmadan production kullanımı risklidir.

