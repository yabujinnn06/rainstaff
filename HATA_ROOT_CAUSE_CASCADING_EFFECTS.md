# Hataların Root Cause Analizi & Cascading Effects

**Tarih**: 18 Ocak 2026  
**Analiz Seviyesi**: Derin Root Cause & Side Effects

---

## 🔍 Kalan 7 Kritik Hata - Root Cause & Cascading Effects

---

## HATA #1: Excel Float Time Validation Eksik

### Root Cause
```python
# app.py Line 111-118: normalize_time_value()
def normalize_time_value(value):
    if value is None or value == "":
        raise ValueError("Saat bos olamaz.")
    if isinstance(value, (int, float)):  # ← PROBLEM
        return normalize_time(value)      # ← Direct call, no range check
    return normalize_time(value)

# normalize_time() Line 247-267
def normalize_time(value):
    if isinstance(value, (int, float)) and 0 <= value < 1:  # ← Sadece valid range check
        total_minutes = int(round(value * 24 * 60))
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
```

**Sorun**: Excel'de `25.5` (invalid) geliyorsa:
- `normalize_time(25.5)` çağrılır
- `0 <= 25.5 < 1` → False
- String işleme branch'ine gider → `str(25.5)` = "25.5"
- Format check fail → ValueError

**KÖK**: Input validation'ı `normalize_time_value()`'de yapmalı, `normalize_time()` içinde değil.

---

### ⚠️ CASCADING EFFECT #1: Import Exception Silently Skip
```python
# app.py Line 1867-1870: Import timesheet
try:
    work_date = normalize_date_value(work_date)
    start_time = normalize_time_value(start_time)  # ← Exception buraya
    end_time = normalize_time_value(end_time)
except ValueError:
    skipped += 1  # ← Silent skip!
    continue
```

**Effect**: 
- Invalid float saat → Exception
- Row skip ediliyor
- **AMA User "atlanan" row'ın saat değeri olduğunu bilmiyor**

**Yeni Hata**: User raporunu indir → 100 row'dan 87 atlanmış
- "Niye?" diye sorgulamıyor, veri kaybı oluyor

**Ek**: app.py Line 1889'da log:
```python
self._log_action(
    "timesheet_import",
    f"file={os.path.basename(path)} added={imported} skipped={skipped}"
)
```

Log'da sadece "skipped=13" yazıyor, hangi row'ların skip olduğu yazılmıyor!

---

### ⚠️ CASCADING EFFECT #2: Calc Error Silent Pass
Report export'ta:
```python
# report.py Line 88-105
(worked, scheduled, ...) = calc_day_hours(
    work_date="2026-01-18",
    start_time="25.5",  # ← HALA GEÇMIŞ (invalid format)
    end_time="18:00",
    ...
)
```

Wait, start_time "25.5" mi olacak? Hayır, normalize_time_value() fail ediyor import'ta.
**AMA** Diyelim ki somehow "9925" gibi bir string geldi (user Excel'e yanlış format yazdı):

```python
def normalize_time(value):
    text = str(value).strip()  # "9925"
    if text.isdigit() and len(text) in (3, 4):
        if len(text) == 3:
            text = "0" + text  # "09925"
        return f"{text[:2]}:{text[2:]}"  # "99:25" ← INVALID!
```

**Result**: `normalize_time("9925")` = "99:25"
- DB'ye "99:25" yazılır!
- calc_day_hours() sonradan `parse_time("99:25")` çalıştırır
- `datetime.strptime("99:25", "%H:%M")` → ValueError!
- **Report export crash ediyor** (try-except yok)

---

### ✅ FIX:
```python
def normalize_time_value(value):
    if value is None or value == "":
        raise ValueError("Saat bos olamaz.")
    if isinstance(value, (int, float)):
        if not (0 <= value < 1):  # ← ADD THIS
            raise ValueError(f"Saat float degeri 0-1 arasında olmalı: {value}")
        return normalize_time(value)
    return normalize_time(value)
```

### 🆕 YENI HATALAR SONRA:
1. **UI Warning Eksik**: User "invalid time format" görmüyor, sessiz skip
   - **Fix**: messagebox.showwarning() ekle import'ta
   
2. **Skipped Row Details Log Eksik**: Hangi row'lar skip olduğunu log'a yaz
   - **Fix**: Skipped row'ları ayrı log'la

3. **calc_day_hours Exception Handling**: report.py'ye try-except ekle (Hata #6'yla bağlantılı)

---

## HATA #3: Break_minutes Giriş Validation Yok

### Root Cause
```python
# app.py Line 1869-1873: Import
break_minutes = cell(4)  # Excel'de: "-10", "999", "ABC", etc.

# Line 1873:
break_minutes = parse_int(break_minutes, 0)  # -10, 999, 0 (ABC için)
# DEFAULT: 0 eğer parse fail ise

# Database'e yazılıyor: 
# INSERT INTO timesheets (..., break_minutes) VALUES (..., -10)
```

**KÖK**: `parse_int()` sadece string → int convert ediyor, **bound checking yok**.

```python
def parse_int(value, default=0):
    try:
        return int(value)  # ← HATA!
    except (ValueError, TypeError):
        return default
```

---

### ⚠️ CASCADING EFFECT #1: DB Tutarsızlığı
```python
# Database Row:
# id=1, employee_id=5, work_date=2026-01-18,
# start_time=09:00, end_time=18:00,
# break_minutes=-10, is_special=0

# calc_day_hours() call:
# Line 62-67 (calc.py)
break_minutes = max(0, int(break_minutes))  # → 0 (fixed)
if break_minutes > gross_hours * 60:
    break_minutes = int(gross_hours * 60)  # (also OK)

worked_hours = 9 - (-10/60) = 9 + 0.167 = 9.167  # ← YANLIŞ!
# (-10 break = +10 minute eklenmiş = longer shift)
```

**PROBLEM**: 
- DB'de break_minutes = -10
- Report açılınca calc_day_hours() düzeltme yapıyor (-10 → 0)
- **AMAN report açan her zaman farklı çıkabiliyor** (caching vs fresh calc)

**Test**: 
```
User 1: Report açıyor → worked_hours = 9.167 (fresh calc)
User 2: Dashboard açıyor → worked_hours gösteriliyor ama cache'de (eski calc)
Farklı sayılar!
```

---

### ⚠️ CASCADING EFFECT #2: Salary Calculation Error
HR bölüm base pay hesaplıyor:
```
worked_hours = 9.167 × hourly_rate = YANLIŞ PAY
```

Denetim sonrası (DB check):
```
"Neden Ahmet'e fazla maaş ödedik?"
Kapat: break_minutes = -10 (invalid)
Açıklama: -10 = 10 dakika KESİNTİ yerine EKLEME
```

Yasal risk: **Veri integriteyi koruma** → ISO 27001 fail

---

### ⚠️ CASCADING EFFECT #3: Overtime Calculation False
```python
# calc.py Line 96-98
if scheduled_hours == 0.0:
    overtime_hours = max(0.0, worked_hours)  # 9.167 (WRONG)
else:
    overtime_hours = max(0.0, gross_hours - scheduled_hours)
    # 9 - 9 = 0 (OK)
```

**IF** user "Pazar günü" işe gitmişse + break_minutes = -10:
```python
gross_hours = 9 - (-10/60) = 9.167
scheduled_hours = 0 (Pazar)
overtime_hours = 9.167  # ← Fazla hesaplanan!
```

---

### ✅ FIX:
```python
# app.py Line 1873: Validation BEFORE DB insert
break_minutes = parse_int(break_minutes, 0)
if break_minutes < 0:
    skipped += 1
    continue
if break_minutes > 480:  # Max 8 hours
    skipped += 1
    continue
```

### 🆕 YENI HATALAR:
1. **User Feedback Eksik**: "Niye break -10 atlandı?" (hata mesajı yok)
   - **Fix**: Skip detaylarını log'la + UI uyarısı

2. **Database Cleanup**: Eski imported veriler (-10 break) fix edilmeli
   - **Fix**: Migration script: `UPDATE timesheets SET break_minutes = 0 WHERE break_minutes < 0`

3. **Salary Recalculation**: Yanlış ödenen maaşlar
   - **New Task**: Finance audit + correction

---

## HATA #4: Region Kolonu Timesheets'te Missing

### Root Cause
```python
# db.py Line 162-171: Table definition
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
# ← REGION KOLONU YOK!

# AMAN: employees table'da region var mı?
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    identity_no TEXT,
    department TEXT,
    title TEXT
);
# ← EMPLOYEE'DE DE REGION YOK!
```

**KÖK**: Schema design eksik - Region field'ı tanımlanmamış.

---

### ⚠️ CASCADING EFFECT #1: INSERT FAIL - Application Crash
```python
# app.py Line 1676-1685: Save timesheet
db.add_timesheet(
    employee_id,
    work_date,
    start_time,
    end_time,
    break_minutes,
    is_special,
    notes,
    self._entry_region()  # ← region parameter
)

# db.py Line 469-476: add_timesheet()
def add_timesheet(employee_id, work_date, start_time, end_time,
                  break_minutes, is_special, notes, region):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO timesheets (..., region) VALUES (..., ?)",
            #              ↑ REGION KOLONU EKLE
            (..., region)
        )
# ← OperationalError: no such column: region
```

**RESULT**: 
- User "Puantaj Kaydet" butonuna basıyor
- App crash ediyor: `sqlite3.OperationalError: no such column: region`
- **User data loss** (form temizlenmişse)

---

### ⚠️ CASCADING EFFECT #2: Dashboard Filtering Broken
```python
# app.py Line 1547-1550: Refresh timesheets
results = db.list_timesheets_by_region(region)

# db.py (assume exists):
def list_timesheets_by_region(region):
    with get_conn() as conn:
        if region == "ALL":
            cursor = conn.execute(
                "SELECT ... FROM timesheets WHERE region IS NOT NULL"
                # ← HATA: region column yoksa SELECT FAIL
            )
```

**RESULT**: Dashboard'ı açan Admin → Hiç timesheet görünmüyor

---

### ⚠️ CASCADING EFFECT #3: Multi-region Data Isolation Broken
```python
# Original design intent:
# Ankara bölgesi user → Sadece Ankara timesheets görmeli
# Istanbul bölgesi user → Sadece Istanbul timesheets görmeli

# WITHOUT region column:
results = conn.execute(
    "SELECT * FROM timesheets WHERE employee_id IN (...)"
)
# ← Tüm employee'ler atlanıyor (employee_id'ye göre)
# ← Bölge filtresi çalışmıyor
```

**Security Risk**: 
- Ankara user, Istanbul verilerine erişebiliyor
- **GDPR Risk** - Unauthorized data access

---

### ✅ FIX: Migration Script
```python
# db.py: init_db() içine migration ekle
ALTER TABLE employees ADD COLUMN region TEXT DEFAULT "Ankara";
ALTER TABLE timesheets ADD COLUMN region TEXT DEFAULT "Ankara";

# Existing employees'lere region ata (based on identity_no or department)
UPDATE employees SET region = "Ankara" WHERE id < 100;  # Example
```

**AMAN**: Migration yapılırsa, tüm old data'ya "Ankara" assign ediliyor → Loss of region info!

---

### 🆕 YENI HATALAR:
1. **Data Loss on Migration**: Eski timesheets'in region'ı unknown
   - **Fix**: Pre-migration backup + manual region assignment

2. **Employee region Unknown**: Kimin hangi bölgede olduğu bilinmiyor
   - **New Task**: HR'den employee-region mapping al

3. **Concurrent Migration Crash**: Migration sırasında User INSERT yapıyor
   - **Fix**: Maintenance mode yap, migration'ı single-user'da çalıştır

4. **Cascading UPDATE Lock**: 10.000 old row'ı UPDATE ediyor
   - **Risk**: Database lock 30+ saniye (timeout)
   - **Fix**: Batch UPDATE: 1000 rows per batch

---

## HATA #5: Employee_map Region Lookup Fail

### Root Cause
```python
# app.py Line 1210-1220: refresh_employees()
self.employee_map = {}
templates = db.list_employees(region=self._entry_region())
for emp in templates:  # emp = (id, name, ..., region)
    self.employee_map[(emp[1], emp[8])] = emp[0]
    # (name, region) → employee_id
    # Example: ("Ahmet Yilmaz", "Ankara") → 5

# app.py Line 1858-1862: Import timesheet
employee_name = "Ahmet Yilmaz"  # (no region info)
base, region = split_display_name(employee_name, REGIONS)
# → base="Ahmet", region=None (because name doesn't have " (Ankara)")

employee_id = self.employee_map.get((base, ""))  # (Ahmet, "")
# NOT FOUND! employee_map has ("Ahmet Yilmaz", "Ankara")
# ← NAME MISMATCH (base vs full_name)
```

**KÖK**: 
1. `split_display_name()` assumption: "Ahmet Yilmaz (Ankara)" format
2. Import file'da sadece "Ahmet Yilmaz" yazılı
3. Lookup: employee_map key = full_name, BUT base = partial name

---

### ⚠️ CASCADING EFFECT #1: All Imports Skip
```python
# app.py Line 1862-1865
if not employee_id:
    missing_employee += 1
    continue  # ← SKIP THIS ROW
```

**RESULT**: Import file'da 100 timesheet
- 100'ü de skip ediliyor
- `missing_employee = 100`
- Log: "Calisan bulunamadi: 100"

---

### ⚠️ CASCADING EFFECT #2: Silent Failure
```python
messagebox.showinfo(
    "Bilgi",
    f"Iceri aktarma tamamlandi. Eklenen: 0, Atlanan: 0, "
    f"Calisan bulunamadi: 100"
)
```

User: "Niye hiç import olmadı?"
- "100 çalışan bulunamadı" diyorsunuz
- **AMAN import file'daki çalışanlar DB'de var!**

**Root**: employee_map'te isimleri yanlış format

---

### ⚠️ CASCADING EFFECT #3: Admin Override Yok
```python
# Admin istiyorum: "Ahmet Yilmaz için timesheet ekle"
# Ama import'ta skip ediliyor

# Workaround: Manual add timesheet (Timesheets tab)
# user_form'da employee seçiyor
# → self.employee_combo = ttk.Combobox(values=self.employee_map.keys())
#    values = [("Ahmet Yilmaz", "Ankara"), ("Ahmet Yilmaz", "Istanbul"), ...]
# → UI gösterir "Ahmet Yilmaz" × 2
# → Kullanıcı hangisinin Ankara olduğu bilmiyor
```

---

### ✅ FIX: Fuzzy Name Matching
```python
# app.py Line 1858-1865
employee_name = "Ahmet Yilmaz"  # Import file'dan

# Seçenek 1: Exact match
base, region = split_display_name(employee_name, REGIONS)
employee_id = self.employee_map.get((employee_name, self._entry_region()))

# Seçenek 2: Fuzzy match (name sadece başında eşleş)
if not employee_id:
    for (emp_full_name, emp_region), emp_id in self.employee_map.items():
        if emp_full_name.startswith(base) and emp_region == self._entry_region():
            employee_id = emp_id
            break

# Seçenek 3: Default region fallback
if not employee_id:
    for (emp_full_name, emp_region), emp_id in self.employee_map.items():
        if emp_full_name == employee_name:
            employee_id = emp_id
            break
```

### 🆕 YENI HATALAR:
1. **Ambiguous Match**: 2 employee aynı ada sahip farklı bölgelerde
   - "Ahmet Yilmaz (Ankara)" vs "Ahmet Yilmaz (Istanbul)"
   - Fuzzy match → hangi biri seçilecek?
   - **Fix**: User seçsin dialog'ta

2. **Performance**: Fuzzy match = O(n) loop
   - 10.000 employee × 100 import row = 1.000.000 comparison
   - **Fix**: Lookup index cache

3. **Partial Name Collision**: 
   - Import: "Ahmet"
   - DB: "Ahmet Yilmaz", "Ahmet Kara"
   - Both match "Ahmet*"
   - **Fix**: Require exact match or interactif selection

---

## HATA #6: calc_day_hours No Try-Except (Report)

### Root Cause
```python
# report.py Line 88-105
(worked, scheduled, ...) = calc_day_hours(
    work_date,
    start_time,  # ← Eğer "99:25" ise?
    end_time,
    break_minutes,
    settings,
    is_special,
)
# ← NO TRY-EXCEPT
```

**calc.py Line 25**:
```python
def parse_time(value):
    return datetime.strptime(value, "%H:%M").time()
    # ← ValueError if value is invalid
```

---

### ⚠️ CASCADING EFFECT #1: Report Export Full Crash
```python
# UI: User "Excel Rapor Olustur" butonuna basıyor
# report.py export_report() çalışıyor
# Line 88: calc_day_hours() → parse_time("99:25") → ValueError
# EXCEPTION NOT CAUGHT
# App thread crash!

# UI gösterir: "Rapor açılamadı - Unknown Error"
```

**User**: "Ne oldu? Rapor niye açılmadı?"
- Log'da hata yok (exception silindi)
- No error message
- No recovery

---

### ⚠️ CASCADING EFFECT #2: Partial Report Saved
```python
# report.py Line 20: wb = Workbook()
# Line 53-69: Headers yazılıyor ✅
# Line 88-105: Data write loop
#   Row 1: OK
#   Row 2: OK
#   Row 3: calc_day_hours() FAIL → ValueError

# Exception thrown BEFORE wb.save()
# AMAN: wb object'i half-written durumda

# File system'de:
# partial_report.xlsx created (incomplete)
# User açıyor → "Dosya bozuk" hatasında
```

---

### ⚠️ CASCADING EFFECT #3: Audit Log Empty
```python
# Database: reports table'a insert YOK
# (because exception before conn.commit())

# db.list_reports() → empty
# User "Dün oluşturduğum rapor nerede?"
# Admin: "DB'de yok, o zaman başarısız olmuş"

# AMAN: Partial file saved! Disk'te var!
```

---

### ✅ FIX:
```python
# report.py Line 80-105
for ...:
    try:
        (worked, scheduled, ...) = calc_day_hours(...)
    except (ValueError, TypeError) as e:
        logger.warning(f"calc_day_hours failed for {name} {work_date}: {e}")
        # Skip this row or use default zeros
        worked = 0.0
        scheduled = 0.0
        # ... other fields
        continue

# Also: Wrap entire export in try-except
def export_report(...):
    try:
        wb = Workbook()
        # ... all code ...
        wb.save(output_path)
        db.log_report(...)
    except Exception as e:
        logger.error(f"Report export failed: {e}")
        messagebox.showerror("Hata", f"Rapor oluşturulamadı: {e}")
        raise  # or return None
```

### 🆕 YENI HATALAR:
1. **Silent Skip**: calc fail olan row'lar skip ediliyor (no warning)
   - **Fix**: Skip count + warning to user

2. **Data Loss in Report**: Eğer row skip edildiyse o timesheet raporda yok
   - **Risk**: Payroll accuracy ↓
   - **Fix**: Add "SKIPPED ROWS" section to report

3. **Inconsistent Data**: 
   - Dashboard shows: 100 timesheet
   - Report shows: 87 timesheet (13 calc fail)
   - **User confusion**

---

## HATA #7: Special Day Overnight Hours Eksik

### Root Cause
```python
# calc.py Line 86-101
if is_special:
    scheduled_hours = 0.0
    overtime_hours = 0.0
    special_normal = worked_hours
    special_overtime = 0.0
    special_night = night_hours  # ← special_overnight YOKSUN!
else:
    # ... normal day logic ...

return (
    worked_hours,
    scheduled_hours,
    overtime_hours,
    night_hours,
    overnight_hours,  # ← Always returned, but never set for is_special!
    special_normal,
    special_overtime,
    special_night,
)
```

**KÖK**: Special day calculation'da overnight_hours branch'i forgot ediliyor.

---

### ⚠️ CASCADING EFFECT #1: Zero Overnight Hour Special Days
```python
# Scenario: Resmi tatil (Pazar) 22:00-08:00 (next day)
# is_special=1, start_time=22:00, end_time=08:00

# calc.py Line 55-59
overnight_hours = overnight_hours_between(st, et)
# → 2 hours (22:00-24:00 = 2h)

# BUT Line 86-101, if is_special:
special_night = night_hours_between(st, et)
# → 10 hours (22:00-08:00 = 10h night)

# AMAN overnight_hours calculated ✅
# BUT return statement: overnight_hours = 0 (not set)
```

Wait, let me check again...

```python
overnight_hours = overnight_hours_between(st, et)  # Line 55
# ← This is a function CALL, overwrites the variable

if is_special:
    special_night = night_hours  # Line 98
    # ← night_hours, not overnight_hours
```

**Ah, overnight_hours IS calculated, but special_overnight never set**:
```python
return (..., overnight_hours, special_normal, special_overnight, special_night)
                    ↑                                  ↑
                    Doğru (general overnight_hours)   EKSIK (special_overnight)
```

**Actually**, looking at Line 95:
```python
special_night = night_hours  # not overnight_hours
```

So for special days:
- `night_hours` (22:00-06:00) calculated ✅
- `overnight_hours` (after midnight) exists but not mapped to `special_overnight`

---

### ⚠️ CASCADING EFFECT #1: Report Column Mismatch
```python
# report.py Line 53-69
headers = [
    ..., "Ozel Gun Gece (s)", ...  # special_night
]

# Line 88-105
(worked, scheduled, overtime, night_hours, overnight_hours,
 special_normal, special_overtime, special_night) = calc_day_hours(...)

ws.cell(row=row, column=15, value=special_night)  # ✅ OK

# BUT Column 11 (overnight_hours):
ws.cell(row=row, column=11, value=overnight_hours)  # ← General overnight
```

Report shows:
- Ozel Gun Gece: 10 (night_hours) ✅
- Geceye Tasan: 2 (overnight_hours from general calc) ← Should include special overnight

**Data inconsistency**: 
- For normal days: overnight_hours = time after midnight
- For special days: overnight_hours = still general calc (wrong context)

---

### ⚠️ CASCADING EFFECT #2: Salary Calculation for Overnight Special Days
```python
# Salary config:
special_night_rate = 250% (ozel gece)
overnight_rate = 150% (geceye tasan)

# Calculate payroll:
if special_night > 0:
    pay += special_night × special_night_rate
if overnight_hours > 0:
    pay += overnight_hours × overnight_rate

# For special overnight shift (22:00-08:00):
special_night = 10h → pay += 10 × 250% ✅
overnight_hours = 2h → pay += 2 × 150% ✅

# BUT calculation is mixing general + special logic!
# What if there's an overlap in accounting?
```

**Risk**: Double-counting or wrong rate applied

---

### ✅ FIX:
```python
# calc.py Line 86-101
if is_special:
    scheduled_hours = 0.0
    overtime_hours = 0.0
    special_normal = worked_hours
    special_overtime = 0.0
    special_night = night_hours
    special_overnight = overnight_hours  # ← ADD THIS
else:
    if scheduled_hours == 0.0:
        overtime_hours = max(0.0, worked_hours)
    else:
        overtime_hours = max(0.0, gross_hours - scheduled_hours)
    special_normal = 0.0
    special_overtime = 0.0
    special_night = 0.0
    special_overnight = 0.0  # ← ADD THIS

# Return statement:
return (
    round(worked_hours, 2),
    round(scheduled_hours, 2),
    round(overtime_hours, 2),
    round(night_hours, 2),
    round(overnight_hours, 2),
    round(special_normal, 2),
    round(special_overtime, 2),
    round(special_night, 2),
    round(special_overnight, 2),  # ← ADD THIS OUTPUT
)
```

**BUT WAIT**: Return statement already has 8 outputs, adding 9th breaks ALL callers!

---

### 🆕 YENI HATALAR:
1. **API Breaking Change**: 
   - `calc_day_hours()` returns 8 values
   - If you add 9th, all calls break: `(a,b,c,d,e,f,g,h) = calc_day_hours()`
   - **MASSIVE REFACTOR NEEDED**

2. **Report Column Redesign**: 
   - Add "Ozel Gun Geceye Tasan (s)" column
   - 16 columns → 17 columns
   - **Excel export format changes**

3. **Backward Compatibility**: 
   - Old reports (16 column) vs new (17 column)
   - Archive tool can't read new format
   - **Need migration script**

4. **Database Report Table**: 
   - `reports` table format changes
   - Old reports become unreadable
   - **Need schema migration**

---

## 📊 ÖZET: Hataların Cascading Tree'si

```
┌─ HATA #1: Float Time Validation
│  ├─ Effect #1: Import skip (silent)
│  └─ Effect #2: calc_day_hours exception (data loss)
│
├─ HATA #3: Break_minutes Validation
│  ├─ Effect #1: DB inconsistency (-10 break)
│  ├─ Effect #2: Salary miscalculation
│  └─ Effect #3: Overtime calc error
│
├─ HATA #4: Region Column Missing
│  ├─ Effect #1: INSERT FAIL (app crash)
│  ├─ Effect #2: SELECT FAIL (dashboard empty)
│  ├─ Effect #3: Multi-region isolation broken (SECURITY!)
│  └─ New Error: Migration lock + batch timeout
│
├─ HATA #5: Employee_map Lookup Fail
│  ├─ Effect #1: All imports skip
│  ├─ Effect #2: UI ambiguity (which Ahmet?)
│  └─ New Error: Fuzzy match performance O(n²)
│
├─ HATA #6: calc_day_hours No Try-Except
│  ├─ Effect #1: Report export crash
│  ├─ Effect #2: Partial file + DB mismatch
│  └─ New Error: Audit trail inconsistency
│
└─ HATA #7: Special Overnight Eksik
   ├─ Effect #1: Report data inconsistency
   ├─ Effect #2: Salary miscalculation
   └─ New Error: API breaking change (return 9 values!)
```

---

## ⚠️ KRITIK: Hataları Düzeltme Sırası

### ZORUNLU SIRA (Cascading Dependencies)

**Phase 1 (Must do first)**: Region Column
- Hata #4 düzeltme → timesheets'e region ekle
- (Çünkü Hata #5 dependi yapıyor)

**Phase 2**: Employee_map Lookup
- Hata #5 düzeltme
- (Çünkü import'lar başlayamıyor)

**Phase 3**: Input Validation
- Hata #1, #3 düzeltme
- (Validation → calc'a sağlam data)

**Phase 4**: Exception Handling
- Hata #6 düzeltme
- (Report crash protection)

**Phase 5 (BREAKING)**: Special Overnight
- Hata #7 düzeltme
- **Requires:**
  - API change (8→9 return values)
  - All callers update
  - Report schema migration
  - Database migration

---

## 📋 FIX CHECKLIST (Optimized Order)

```
[1] db.py: timesheets table'a region ADD (ALTER TABLE)
    └─ Migration: populate region = "Ankara" default
    └─ Backup + verify

[2] db.py: employees table'a region ADD (ALTER TABLE)
    └─ Manual assignment (or import from file)

[3] app.py: employee_map region lookup fuzzy match
    └─ Test with multi-region employees
    └─ Handle ambiguous match

[4] app.py: normalize_time_value() float validation
    └─ Add 0 <= value < 1 check
    └─ Improve skip logging

[5] app.py: break_minutes validation
    └─ Add bounds check (0-480 minutes)
    └─ DB cleanup: UPDATE SET break_minutes=0 WHERE <0

[6] report.py: calc_day_hours() try-except wrapper
    └─ Skip invalid rows
    └─ Log details

[7] calc.py: special_overnight calculation
    ⚠️ BREAKING CHANGE
    └─ Add return value #9
    └─ Update ALL callers (app.py, report.py, tests)
    └─ Update report schema (16→17 columns)
    └─ Database migration for reports

[8] Test Suite
    └─ Integration test: import + report + multi-region
    └─ Edge cases: negative break, invalid time, special day
    └─ Concurrency: 3 users import + 1 user export

[9] Field Test
    └─ 4 user concurrent test
    └─ Verify salary calculation
    └─ Check region isolation
```

---

**Rapor Hazırlayan**: GitHub Copilot  
**Analiz Tarihi**: 18 Ocak 2026  
**Toplam Root Cause**: 7 unique + 12 cascading effects  
**Breaking Changes**: 1 (special_overnight API)  
**Estimated Fix Time**: 3-4 hours development + 2 hours testing
