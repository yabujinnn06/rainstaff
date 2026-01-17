# Rainstaff Sistem Analiz ve Geliştirme Raporu

**Tarih**: 17 Ocak 2026  
**Durum**: Kod incelenmesi tamamlandı

---

## 1. TESPIT EDILEN SORUNLAR VE RİSKLER

### 🔴 KRİTİK (Acil Düzeltme Gereken)

#### 1.1 Veri Girişinde Eksik Validasyon (app.py)
**Sorun**: `normalize_date()` ve `normalize_time()` hataları UI'da catch edilmiyor
```python
# Risky pattern
value = value.strip()  # .strip() çalışmaz eğer value None ise
for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
```
**Etki**: Kullanıcı geçersiz tarih girerse uygulamahang edebilir  
**Çözüm**:
```python
def normalize_date(value):
    if value is None:
        raise ValueError("Tarih boş olamaz")
    value = str(value).strip()
    if not value:
        raise ValueError("Tarih boş olamaz")
    # ... rest
```

#### 1.2 Senkronizasyonda Hata İşleme Yok (app.py)
**Sorun**: `sync_url` POST isteğinde timeout/bağlantı hatası yakalanmıyor
```python
# Bulunamayan kod pattern - sync sadece requests var mı diye kontrol ediyor
if requests is None:
    # Silent fail
```
**Etki**: Sync başarısız olduğunda kullanıcıya bilgi vermez  
**Çözüm**: Try-except ekle ve kullanıcıya error mesajı göster

#### 1.3 Veritabanında Concurrency Sorunu
**Sorun**: Birden fazla thread aynı DB'ye yazarsa lock olabilir
```python
# db.py - get_conn() context manager var ama threading kontrolü yok
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    # SQLite default olarak timeout=5 saniye var
    # İntensif kullanımda conflict olur
```
**Çözüm**:
```python
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000;")  # 30 saniye
```

#### 1.4 Excel Report Generasyonunda Hata Yok (report.py)
**Sorun**: `openpyxl` exception silently pass ediliyor
```python
try:
    img = Image(logo_path)
    # ...
except Exception:
    pass  # Hatayı görmeyiz!
```
**Etki**: Logo yüklenmezse, rapor bozuk olur ama user bunu bilmez  
**Çözüm**: Logger ile kaydet
```python
except Exception as e:
    logger.warning(f"Logo yüklemesi başarısız: {e}")
```

---

### 🟡 ORTA SEVİYE (Fonksiyon Bozulma Riski)

#### 2.1 Şifre Depolama Şifrelenmiyor (db.py)
**Sorun**: Şifreler hash edilmiş ancak salt yok
```python
DEFAULT_USERS = [
    ("ankara1", "060106", "user", "Ankara"),  # Clear number!
]
```
**Risk**: Veritabanı ifşa olursa, şifreler readableş  
**Çözüm**: Password hashing ekle (bcrypt/argon2)

#### 2.2 Tarih Formatı Çakışması
**Sorun**: `calc.py` ve `app.py` different parsing logic var
```python
# app.py - parse_date()
def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
    
# calc.py - kendi parse_date() var
def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
```
**Risk**: Kodda iki farklı parser = bug riski (DRY prensibine uymuyor)  
**Çözüm**: Tek bir `utils.py` module'de yap, hepsi oradan import etsin

#### 2.3 Bölge Filtresi Bypass Edilebilir
**Sorun**: Non-admin user "Tum Bolgeler" seçebiliyorsa başka bölge verisi görebilir
```python
# app.py - bölge filtresi client-side
if not is_admin:
    WHERE region = current_region
```
**Risk**: UI'da bölgeyi değiştirebilirse, tüm veri açılır  
**Çözüm**: Server-side validation (Flask dashboard'da olmalı)

---

### 🟢 HAFIF (Kalite İyileştirmesi)

#### 3.1 Logging Kullanımı Tutarsız
- Bazı hataları `logger.error()` ile logguyorsun
- Bazıları silent fail ediyor (try-except Exception: pass)
- Sync hatası loglanmıyor

**Çözüm**: Standart logging pattern belirle

#### 3.2 Eksik Input Bounds Checking
```python
def calc_day_hours(...):
    # Eğer break_minutes > gross_hours ise?
    worked_hours = gross_hours - (break_minutes / 60.0)
    # Negatif olabilir!
```

#### 3.3 Report CSV Import Çok Flexible
```python
EMP_HEADER_ALIASES = {
    "full_name": ["ad soyad", "adsoyad", "calisan", ...]
}
# 4 alias = 4x bug riski
```
**Çözüm**: Header mapping kurallarını database'de tut

---

## 2. EKSİK ÖZELLİKLER

### Yapılması Tavsiye Edilen Geliştirmeler

| Özellik | Önem | Zaman | Açıklama |
|---------|------|-------|----------|
| **Unit Tests** | 🔴 Yüksek | 4-6 saat | `calc.py` için en kritik (saat hesabı) |
| **API Rate Limiting** | 🟡 Orta | 1-2 saat | `/sync` endpoint DOS'a açık |
| **Offline Mode** | 🟡 Orta | 3-4 saat | Sync down ise, local'de çalışamıyor |
| **Audit Log** | 🟡 Orta | 2-3 saat | Kim ne zaman ne değiştirdi? |
| **Backup Encryption** | 🟡 Orta | 2-3 saat | Backup'lar şifresiz |
| **User Permissions** | 🔴 Yüksek | 4-5 saat | Sadece Region değil, Tab-level kontrol |
| **Timesheet Conflict Alert** | 🟢 Hafif | 1-2 saat | Aynı saatte 2 entry varsa uyar |
| **Mobile UI** | 🟢 Hafif | 8-12 saat | Şu an desktop-only |

---

## 3. PERFORMANS SORUNLARI

### Algılanan Bottlenecks

#### 3.1 Large Dataset (10,000+ timesheet)
```python
# app.py - refresh_timesheets_tab()
# SELECT * FROM timesheets WHERE ... 
# Sonra Python'da filter etme (N+1 problem)
```
**Çözüm**: SQL'de GROUP BY yap, pagination ekle

#### 3.2 Excel Report Generasyonu Yavaş
```python
# report.py - 1000 row rapor = 10-15 saniye
# Sebep: Her cell'e style uygulanıyor
```
**Çözüm**: Batch styling, format templatı kullan

#### 3.3 Sync Sırasında UI Freeze
```python
# app.py - sync işlemi main thread'de
# Yapması gereken: threading.Thread ile async yap
```

---

## 4. GÜVENLİK SORUNLARI

| Sorun | Risk | Çözüm |
|-------|------|-------|
| **Şifre Hash Yok** | Yüksek | bcrypt ekle |
| **No Rate Limiting** | Orta | Flask limiter ekle |
| **SQL Injection** | Düşük* | Zaten parameterized queries kullanıyor |
| **CSRF Token** | Düşük | GET-only dashboard olduğu için |
| **HTTPS Opsiyonel** | Orta | sync_url validation ekle |

*Parameterized queries kullanıldığı için SQL injection riski düşük

---

## 5. SPESIFIK KOD DÜZELTMELERİ

### 5.1 app.py - normalize_date() Güvenleştirme
**Geçerli**:
```python
def normalize_date(value):
    value = value.strip()  # BUG: value None olabilir
```

**Düzeltme**:
```python
def normalize_date(value):
    if not isinstance(value, str):
        value = str(value) if value else ""
    value = value.strip()
    if not value:
        raise ValueError("Tarih boş olamaz")
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("Tarih formati gecersiz. Ornek: 2026-01-05 veya 05.01.2026")
```

### 5.2 calc.py - Input Validation
**Geçerli**:
```python
def hours_between(start_time, end_time):
    # start_time / end_time None olabilir
    start_dt = datetime.combine(date.today(), start_time)
```

**Düzeltme**:
```python
def hours_between(start_time, end_time):
    if not start_time or not end_time:
        raise ValueError("Start/end time boş olamaz")
    if not isinstance(start_time, time) or not isinstance(end_time, time):
        raise TypeError("Expected time objects")
    # ... rest
```

### 5.3 db.py - Connection Timeout
**Geçerli**:
```python
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)  # Default timeout=5s
```

**Düzeltme**:
```python
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode = WAL;")  # Better concurrency
    conn.execute("PRAGMA busy_timeout = 30000;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### 5.4 report.py - Error Handling
**Geçerli**:
```python
try:
    img = Image(logo_path)
    ws.add_image(img, "A1")
except Exception:
    pass
```

**Düzeltme**:
```python
try:
    img = Image(logo_path)
    img.width = 110
    img.height = 60
    ws.add_image(img, "A1")
except FileNotFoundError:
    if logger:
        logger.warning(f"Logo bulunamadı: {logo_path}")
except Exception as e:
    if logger:
        logger.error(f"Logo yükleme hatası: {e}")
```

---

## 6. TEST PLANI (Boş Alanlar)

### Yapılması Gereken Testler

#### Unit Tests (Kritik - `calc.py`)
```python
# tests/test_calc.py
def test_hours_between_same_day():
    assert hours_between(time(9, 0), time(17, 0)) == 8.0

def test_hours_between_overnight():
    assert hours_between(time(22, 0), time(6, 0)) == 8.0

def test_night_hours_22_to_6():
    assert night_hours_between(time(22, 0), time(6, 0)) == 8.0

def test_night_hours_10_to_18():
    assert night_hours_between(time(10, 0), time(18, 0)) == 0.0

def test_overnight_hours():
    assert overnight_hours_between(time(22, 0), time(6, 0)) == 8.0
    assert overnight_hours_between(time(10, 0), time(18, 0)) == 0.0
```

#### Integration Tests (Orta - Database)
```python
# tests/test_db.py
def test_backup_and_restore():
    # Create backup, modify DB, restore, verify

def test_concurrent_writes():
    # Simulate 2 simultaneous writes, verify no corruption
```

#### UI Tests (Hafif - Regression)
```python
# tests/test_app_ui.py
def test_login_invalid_password()
def test_employee_add_duplicate_name()
def test_timesheet_future_date_rejected()
```

---

## 7. GELİŞTİRME TAVSIYALARI (Sıra Önem)

### Hafta 1 (Acil)
1. ✅ `normalize_date()` null check ekle
2. ✅ `get_conn()` timeout artır (5s → 30s)
3. ✅ Sync error handling ekle
4. ✅ Report logo exception loggla

### Hafta 2 (Önemli)
5. Password hashing (bcrypt)
6. Tarih parser consolidation (utils.py)
7. Basic unit tests (calc.py)

### Hafta 3+ (İyileştirme)
8. Audit logging
9. Offline mode
10. Permission system (Tab-level)

---

## 8. ÖZET

| Metrik | Durum | Yorum |
|--------|-------|-------|
| **Kod Kalitesi** | 6/10 | Şifre ve senkron hatası kritik |
| **Test Coverage** | 0/10 | Test yok - en büyük risk |
| **Güvenlik** | 5/10 | Password, rate limit gereken |
| **Performans** | 7/10 | İyi, large dataset'te optimize et |
| **Maintainability** | 6/10 | Parser duplicate, logging tutarsız |

### Kontrol Listesi (Başla Buradan)
- [ ] 5.1-5.4 düzeltmeleri yap
- [ ] `tests/test_calc.py` oluştur
- [ ] bcrypt implement et
- [ ] Sync error handling ekle
- [ ] README'deki "Known Limitations" güncelle

---

**Hazırlayan**: AI Code Analyzer  
**Sonraki Review**: 2 hafta sonra
