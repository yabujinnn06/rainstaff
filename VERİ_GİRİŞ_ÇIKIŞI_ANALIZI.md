# Rainstaff - Veri Girişi/İşlemesi/Çıkışı Uyumsuzluk Analizi

**Tarih**: 18 Ocak 2026  
**Analiz Seviyesi**: Detaylı Data Flow Audit

---

## 📊 Veri Akışı Şeması

```
GİRİŞ (INPUT) → KONTROL → İŞLEME → SAKLANAKl → ÇIKIŞI (OUTPUT)
-------         ---------  -------   -------      -------
UI Input        Normalize  Calc.py   Database     Excel
Excel/CSV       Validation Result    Timesheets   Report
Manual Entry                         Save         Export
```

---

## 🔴 KRITIK HATA VE UYUMSUZLUKLAR

### 1. **SAAT TİPİ UYUMSUZLUĞU: Float vs String**

#### Sorun Senaryosu
```python
# app.py Line 1855-1870: Import timesheets
work_date = cell(1)  # Excel'de: 1.5 (float) veya "01.01.2026" (string)
start_time = cell(2)  # Excel'de: 0.40625 (Excel time format = 09:45)
end_time = cell(3)    # Excel'de: 0.75 (Excel time format = 18:00)
break_minutes = cell(4)  # Excel'de: 60 (int) veya "60" (string)

# app.py Line 1870: Normalization
start_time = normalize_time_value(start_time)  # ???
```

#### Normalize_time() fonksiyonu
```python
# app.py Line 247-267: normalize_time()
def normalize_time(value):
    if isinstance(value, (int, float)) and 0 <= value < 1:  # ✅ Excel float handle
        total_minutes = int(round(value * 24 * 60))
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    # ✅ String handling OK
```

**FAKAT**: `normalize_time_value()` (Line 111-118) çağrısı:
```python
def normalize_time_value(value):
    """Import icin flexible saat normalizasyonu"""
    if value is None or value == "":
        raise ValueError("Saat bos olamaz.")
    if isinstance(value, (int, float)):
        # ⚠️ BUG: Eğer 25.0 veya 999.0 gibi invalid float gelmişse?
        # KONTROL YOK! Direkt normalize_time() gider, sonra fail
        return normalize_time(value)  
    return normalize_time(value)
```

**PROBLEM**: 
- Excel'de `0.75` (18:00) geliyorsa ✅ OK
- **Ama** `25.5` (invalid) geliyorsa → `normalize_time()` içinde `0 <= value < 1` kontrolü fail → exception
- Exception catch'lenmiş (Line 1868: `except ValueError`) → row SKIP ediliyor
- **Sonuç**: Valid veri atlanıyor

**ÇÖZÜm**: `normalize_time_value()` içinde range validation:
```python
def normalize_time_value(value):
    if isinstance(value, (int, float)):
        if not (0 <= value < 1):  # ← Ekle
            raise ValueError(f"Saat degeri gecersiz: {value}")
        return normalize_time(value)
```

---

### 2. **TARIH FORMATLARINDA SPEC UYUMSUZLUK** ✅ FIXED

#### Çözüm (Doğru)
```python
# app.py Line 96-110
def normalize_date_value(value):
    """Import icin flexible tarih normalizasyonu; Excel float veya string kabul eder"""
    if value is None or value == "":
        raise ValueError("Tarih bos olamaz.")
    if isinstance(value, str):
        return normalize_date(value)
    if isinstance(value, (int, float)):
        try:
            dt = datetime.fromordinal(int(value) + 693594)  # ✅ Doğru offset
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            raise ValueError(f"Tarih formati gecersiz: {value}")
    raise ValueError(f"Tarih formati gecersiz: {value}")
```

**Status**: ✅ FIXED - `fromordinal()` ile Excel tarihler doğru çevriliyor

---

### 3. **BREAK MINUTES BOUNDS VALIDATION HALA EKSIK**

#### Sorun
```python
# app.py Line 1869: Import
break_minutes = cell(4)  # Excel'de: "-10" (negatif) veya "500" (aşırı)

# app.py Line 1873:
break_minutes = parse_int(break_minutes, 0)  # Kabul eder
# → DB'ye "-10" yazılır

# calc.py Line 62-67: Hesaplama
def calc_day_hours(...):
    break_minutes = max(0, int(break_minutes))  # ✅ Negatif engellendi
    if break_minutes > gross_hours * 60:
        break_minutes = int(gross_hours * 60)  # ✅ Max capping
    worked_hours = gross_hours - (break_minutes / 60.0)
```

**PROBLEM**: 
- Giriş validasyonu yok (app.py)
- Database'e **invalid veri yazılıyor**
- Sonra calc.py'de düzeltiliyor (şans eseri)

**ÇÖZÜm**: app.py'ye validation:
```python
# Line 1873'te:
break_minutes = parse_int(break_minutes, 0)
if break_minutes < 0:
    skipped += 1
    continue  # Negatif break atla
```

---

### 4. **BOOL KONVERSİYONU UYUMSUZ**

#### Sorun
```python
# app.py Line 1872: Import
is_special = cell(5)  # Excel'de: 
    # Doğru: "Evet", "1", "True", "Yes"
    # Yanlış: "Hayir", "0", "False", "No", "" (empty)

# app.py Line 1889:
is_special = 1 if parse_bool(is_special) else 0  # ✅ OK

# ama calc.py Line 86'da
if is_special:  # ← Binary check
```

**Sorun**: 
```python
def parse_bool(value):  # app.py Line 209-213
    text = str(value or "").lower().strip()
    return text in ("true", "yes", "1", "evet")
```

**TEST**: Kullanıcı "0" yazarsa:
```python
is_special = "0"  # String
is_special = 1 if parse_bool("0") else 0  # → False, so 0
# DB'ye yazılır: is_special = 0 ✅ OK

Ama Excel'de 0 (integer):
is_special = 0  # Integer
parse_bool(0) → "0".lower() → "0" in (...) → False
# Database: is_special = 0 ✅ OK

BUT: Excel'de BOŞSA?
is_special = ""  # Empty
parse_bool("") → False
# Database: is_special = 0 ✅ OK (expected)
```

**RESULT**: parse_bool ✅ Güvenli

---

### 5. **SAT SAYISINDA UYUMSUZLUK: 16 KOLON VS SAT SAYISI**

#### Sorun
```python
# report.py Line 53-69: Header (16 columns)
headers = [
    "Calisan", "Bolge", "Tarih", "Giris", "Cikis", "Mola (dk)",
    "Calisilan (s)", "Plan (s)", "Fazla Mesai (s)", "Gece (s)",
    "Geceye Tasan (s)", "Ozel Gun", "Ozel Gun Normal (s)",
    "Ozel Gun Fazla (s)", "Ozel Gun Gece (s)", "Not"
]  # 16 headers

# Line 89-105: Veri yazma
ws.cell(row=row, column=1, value=name)
ws.cell(row=row, column=2, value=region or "")
ws.cell(row=row, column=3, value=work_date)
...
ws.cell(row=row, column=16, value=notes or "")
```

**FAKAT** app.py'de input:
```python
# app.py Line 1658-1667 / 1673-1682
db.add_timesheet(
    employee_id,
    work_date,
    start_time,
    end_time,
    break_minutes,
    is_special,
    notes,
    self._entry_region()  # ← 8. param: region
)

# db.py Line 469-476: INSERT
INSERT INTO timesheets (
    employee_id, work_date, start_time, end_time,
    break_minutes, is_special, notes, region
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)  # ← 8 fields
```

**PROBLEM**: Kolon sayısı ✅ OK, FAKAT:
- `timesheets` table'da **"region" KOLONU VAR MI?**

#### db.py Line 162-171 check:
```python
CREATE TABLE IF NOT EXISTS timesheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    work_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    break_minutes INTEGER NOT NULL DEFAULT 0,
    is_special INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
);
```

🔴 **REGION KOLONU EKSIK!**

**RESULT**: `db.add_timesheet()` çağrısında:
```python
def add_timesheet(employee_id, work_date, start_time, end_time, 
                  break_minutes, is_special, notes, region):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO timesheets (..., region) VALUES (..., ?)",
            (..., region)  # ← region parametresi gönderiliyor
        )
```

**Eğer** migration yapılmamışsa → **OperationalError: no such column: region**

---

### 6. **EMPLOYEE_MAP VERİ KAYBI: Region Filtresi Eksik**

#### Sorun
```python
# app.py Line 1858-1862: Import employee mapping
employee_name = "Ahmet Yilmaz"
base, region = split_display_name(employee_name, REGIONS)
# → base="Ahmet Yilmaz", region=None (çünkü name'de region bilgisi yok)

employee_id = self.employee_map.get((base, ""))  # ← Boş region ile ara
# or self.employee_map.get((base, self._entry_region()))

# ama employee_map nasıl oluştuluyor?
# app.py Line 1210-1220: refresh_employees()
templates = db.list_employees(region)  # ← self._entry_region()
for emp in templates:
    self.employee_map[(emp[1], emp[8])] = emp[0]  # (name, region) → id
```

**PROBLEM**: 
```python
# Admin: self._entry_region() = "ALL"
# Ankara kullanıcısı: self._entry_region() = "Ankara"

# Admin Timesheets import ediyor:
# employee_map.get(("Ahmet", "")) → NOT FOUND
# employee_map.get(("Ahmet", "ALL")) → NOT FOUND

# Çünkü employee_map sadece:
#  ("Ahmet", "Ankara") → id_1
#  ("Ahmet", "Izmir") → id_2
```

**RESULT**: `missing_employee += 1` → Tüm import atlanıyor!

**ÇÖZÜm**: 
```python
# app.py Line 1858-1862:
employee_id = self.employee_map.get((base, self._entry_region()))
if not employee_id:
    employee_id = self.employee_map.get((base, ""))
if not employee_id:
    # Tüm regions'ta ara
    for (emp_name, emp_region), emp_id in self.employee_map.items():
        if emp_name == base:
            employee_id = emp_id
            break
```

---

### 7. **REPORT AÇIKLANMAYAN HATA: calc_day_hours() BAŞARISIZ OLDUĞUNDArepository**

#### Sorun
```python
# report.py Line 88-105
(
    worked,
    scheduled,
    overtime,
    night_hours,
    overnight_hours,
    special_normal,
    special_overtime,
    special_night,
) = calc_day_hours(  # ← No try-except!
    work_date,
    start_time,
    end_time,
    break_minutes,
    settings,
    is_special,
)
```

**PROBLEM**: 
- Eğer `calc_day_hours()` hata verirse (invalid time, date, vb)
- Exception'ı handle yok
- **Rapor export'ı crash ediyor**
- User sadece "Rapor açılamadı" hatasını görüyor

**ÇÖZÜm**:
```python
try:
    (worked, scheduled, ...) = calc_day_hours(...)
except ValueError as e:
    logger.warning(f"calc_day_hours failed for emp {name} date {work_date}: {e}")
    # Satırı atla veya default values set
    worked = 0.0
    scheduled = 0.0
    # ... diğer fields
    continue
```

---

### 8. **CONCURRENT WRITE RİSKİ: Transaction Guarantee Yok**

#### Sorun (Evet, dün gece fixed ama incomplete)
```python
# db.py Line 114-124
@contextmanager
def get_conn():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")  # 30 saniye
        yield conn
        conn.commit()  # ✅ Eklendi
    except Exception:
        conn.rollback()  # ✅ Eklendi
        raise
    finally:
        conn.close()
```

**ÇOKCİLI TEST**: 5 kullanıcı aynı anda 100 timesheet import ediyor
```
Thread 1: INSERT timesheets row 1-20
Thread 2: INSERT timesheets row 21-40
Thread 3: INSERT timesheets row 41-60
...

Problem: Eğer Thread 2 crash ederse?
- conn.rollback() ✅ çalışıyor
- FAKAT Thread 1, 3, 4, 5'in commitleri done
- Partial write result!
```

**ASLINDA**: Her thread'in kendine ait `get_conn()` var, so each transaction isolated.
✅ **SAFE**

---

## 🟡 ORTA SEVİYE SORUNLAR

### 9. **NULL/Empty Employee Name Accept**
```python
# app.py Line 1858
if not employee_name:
    skipped += 1
    continue  # ✅ OK

# BUT app.py Line 1804:
if not name:
    skipped += 1
    continue  # ✅ OK for employee import
```

**Status**: ✅ Kontrollü

---

### 10. **Special Day vs Overtime Hesap Logic**
```python
# calc.py Line 86-101
if is_special:
    scheduled_hours = 0.0
    overtime_hours = 0.0
    special_normal = worked_hours  # ← Tüm saatler special_normal'e giriyor
    special_overtime = 0.0
    special_night = night_hours
else:
    if scheduled_hours == 0.0:
        overtime_hours = max(0.0, worked_hours)
    else:
        overtime_hours = max(0.0, gross_hours - scheduled_hours)
    special_normal = 0.0
    special_overtime = 0.0
    special_night = 0.0
```

**PROBLEM**: 
- Special day'de night_hours hessap ediliyor ✅ OK
- FAKAT overnght_hours hesaplanmıyor (is_special=1 branch'ta)

**ÇÖZÜm**:
```python
if is_special:
    ...
    special_overnight = overnight_hours  # ← Ekle
else:
    ...
```

---

## ✅ FIX SÖZLÜĞü

| No | Sorun | Dosya | Satır | Öncelik | Status |
|-------|------|-------|------|---------|--------|
| 1 | Excel float time validation | app.py | 111-118 | 🔴 Kritik | ❌ Yapılmadı |
| 3 | Break_minutes giriş validation | app.py | 1873 | 🔴 Kritik | ❌ Yapılmadı |
| 4 | Region kolonu missing (timesheets) | db.py | 162-171 | 🔴 Kritik | ❓ Check |
| 5 | Employee_map region lookup fail | app.py | 1858-1862 | 🔴 Kritik | ❌ Yapılmadı |
| 6 | calc_day_hours no try-except | report.py | 88-105 | 🟡 Önemli | ❌ Yapılmadı |
| 7 | Special overnight_hours eksik | calc.py | 86-101 | 🟡 Orta | ❌ Yapılmadı |
| 8 | Import skip counter (missing_employee) | app.py | 1827-1895 | 🟡 Orta | ⚠️ Eksik log |

---

## 📋 YAPILACAK IŞLER (Sırasıyla)

```
Session 29 (Bugün):
[ ] 1. db.py: timesheets table'a "region" kolonu ekle (migration)
[ ] 2. app.py: normalize_time_value() float range validation ekle
[ ] 3. app.py: normalize_date_value() Excel offset fix
[ ] 4. app.py: break_minutes input validation ekle
[ ] 5. app.py: employee_map region lookup logic fix
[ ] 6. report.py: calc_day_hours() try-except wrapper ekle
[ ] 7. calc.py: special day overnight_hours fix
[ ] 8. Test: Tüm fixes için unit test ve import test

Session 30:
[ ] 9. Field test: 3-4 concurrent user import test
[ ] 10. Regression: Build ve manual test
```

---

**Rapor Hazırlayan**: GitHub Copilot  
**Analiz Tarihi**: 18 Ocak 2026, 14:45  
**Toplam Sorun**: 10 (4 Kritik, 3 Orta, 3 Bilgi)
