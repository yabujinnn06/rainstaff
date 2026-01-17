# Rainstaff Copilot Talimatları

## Mimari Genel Bakış

**Rainstaff** Türk işletmeleri için iki katmanlı puantaj ve filo yönetim sistemidir:
- **Masaüstü Uygulama** ([puantaj_app/app.py](puantaj_app/app.py)): Tkinter arayüzü (~4900 satır); SQLite yerel veritabanı; ana veri kaynağı
- **Web Dashboard** ([server/app.py](server/app.py)): Flask salt-okunur admin paneli; masaüstünden senkronize edilir
- **Senkronizasyon Akışı**: Masaüstü → POST `/sync` (DB dosyasını yükler) → Sunucu DB'yi değiştirir → Dashboard en güncel veriyi okur

### Veri Akışı
1. Masaüstü `%APPDATA%\Rainstaff\data\puantaj.db`'ye yazar (SQLite)
2. Her CRUD işleminden sonra, masaüstü tüm DB'yi sunucuya POST `/sync` ile yükler (`API_KEY` header gerekli)
3. Dashboard sayfa yüklendiğinde sunucu DB'sini okur (her zaman en güncel)
4. **Çift yönlü senkronizasyon yok** – masaüstü yetkili, dashboard sadece okuma

## Ana Bileşenler

### Masaüstü (Tkinter)
- **app.py**: Modern enterprise-grade sekme sistemiyle ana arayüz (~4900 satır); Dashboard-first düzeni
- **Enterprise GUI Tasarım**: SAP Fiori, Dynamics 365, ServiceNow esinli minimal tasarım
  - Renk paleti: Minimal - #0070C0 (tek accent), gri skalası (#FAFAFA, #FFFFFF, #E8E8E8)
  - Segoe UI font ailesi, 10-11pt standart boyut
  - Tutarlı spacing: 8px grid sistemi (8, 16, 24, 32)
  - Göz yormayan: Soft colors, yeterli whitespace, minimal borders
  - Card-based layout: Beyaz içerik kartları, soft gri arka plan
  - Buton boyutları: Ana buton 20x10 padding, normal buton 16x8 padding
  - Input yüksekliği: 10px padding (ipady=10)
  - Treeview satır yüksekliği: 36px (rahat okuma)
- **Sekme Sıralaması**: Dashboard → Puantaj → Çalışanlar → Araçlar → Servis → Raporlar → Yönetim → Ayarlar → Loglar
- **db.py**: SQLite şema + migration'lar + yedekleme/dışa aktarma/içe aktarma; `get_conn()` context manager transaction'ları garanti eder
- **calc.py**: Saat hesaplamaları (normal, fazla mesai, gece vardiyası 22:00-06:00, geceye taşan, özel günler)
- **report.py**: `openpyxl` ile Excel oluşturma; 16 sütunlu sabit düzen, kenarlıklar/renkler/logo ile

### GUI İyileştirmeleri (Ocak 2026)
- ❌ **Kullanım rehberi kaldırıldı** - Modern ERP sisteminde gereksiz
- ✅ **Modern header**: 64px yükseklik, beyaz arka plan, minimal logo (32px), kullanıcı bilgisi sağ üstte
- ✅ **Loading ekranı**: Minimalist, 360x200px, soft animasyon
- ✅ **Login ekranı**: 400x420px, card-based, büyük input alanları (ipady=10)
- ✅ **Renk paleti**: Enterprise minimal - tek accent (#0070C0), gri skala
- ✅ **Pencere boyutu**: 1280x800 (minimum 1024x720) - modern widescreen için optimize
- ✅ **Sekmeler**: Emoji yok - temiz metin, büyük padding (24x12)
- ✅ **Butonlar**: Tutarlı boyut - accent 20x10, normal 16x8
- ✅ **Font boyutları**: 10-11pt standart, başlıklar 18pt
- ✅ **Tablo satırları**: 36px yükseklik, rahat okuma

### Veritabanı Şeması (SQLite)
**Ana tablolar**:
- `employees`, `timesheets` (puantaj = timesheet/devam kaydı)
- `shift_templates` (varsayılan saatler: hafta içi 9s, Cumartesi özel başlangıç/bitiş)
- `vehicles`, `drivers`, `vehicle_inspections`, `vehicle_inspection_results`, `vehicle_faults`, `vehicle_service_visits`
- `users` (rol: admin/user; bölge: Ankara/Izmir/Bursa/Istanbul/ALL)
- `settings` (şirket adı, sync URL/token, logo yolu, hafta içi saatler, vb.)
- `reports` (arşivlenmiş Excel dışa aktarmaları)

**Kritik sütun**: Her tabloda erişim kontrolü için `region TEXT` var ([db.py:ensure_schema](puantaj_app/db.py)'da migration ile eklendi).

### Sunucu (Flask)
- **Route'lar**: `/dashboard`, `/alerts`, `/reports`, `/reports/weekly/<plate>/<week_start>`, `/vehicle/<plate>`, `/driver/<id>`, `/employee/<id>`
- **Kimlik Doğrulama**: Session tabanlı giriş; varsayılan kullanıcılar (ankara1/060106, izmir1/350235, admin/748774); [server/app.py](server/app.py)'de `DEFAULT_USERS`'a bakın
- **Bölge Filtresi**: Admin olmayan kullanıcılar sadece kendi bölgelerini görür; admin dropdown ile tüm bölgeleri görebilir
- **Template'ler**: `_sidebar.html` (tüm sayfalarda sabit sidebar), mobil uyumlu

## Projeye Özel Kalıplar

### Tarih/Saat Normalizasyonu (KRİTİK)
```python
# Şema her zaman ISO formatı kullanır: YYYY-MM-DD, HH:MM
# Girdi parsing'i esnektir ("05.01.2026" veya "2026-01-05" kabul eder)

# calc.py
def parse_date(value):  # "%Y-%m-%d" veya "%d.%m.%Y" kabul eder
def parse_time(value)   # Sadece "%H:%M" kabul eder

# app.py
def normalize_date(value):  # Her zaman "YYYY-MM-DD" döner
def normalize_time(value)   # Her zaman "HH:MM" döner

# DB insert'ten önce MUTLAKA normalize edin; ham kullanıcı girdisini asla kaydetmeyin
```

### Veritabanı Transaction'ları için Context Manager
```python
# db.py kalıbı (başarıda autocommit, hatada rollback)
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Kullanım: with get_conn() as conn: ...
```

### Bölge Tabanlı Erişim Kontrolü
```python
# Admin olmayan kullanıcılar: WHERE region = current_region
# Admin: "Kayit Bolge" (kayıt bölgesi) ve "Goruntuleme Bolge" (görüntüleme bölge filtresi) ayarlayabilir
# Sabit kodlanmış bölgeler: ["Ankara", "Izmir", "Bursa", "Istanbul"] + admin için "ALL"
# Görüntüleme dropdown'unda admin için "Tum Bolgeler" var

# app.py örnek
if not self.is_admin:
    WHERE region = ?  # Mevcut kullanıcının bölgesini bağla
```

### Araç Haftalık Kontrol Listesi
```python
# 9 maddelik kontrol listesi (masaüstü ve sunucuda aynı)
VEHICLE_CHECKLIST = [
    ("body_dent", "Govde ezik/cizik"),
    ("paint_damage", "Boya hasari"),
    ("interior_clean", "Ic temizligi"),
    ("smoke_smell", "Sigara kokusu"),
    ("tire_condition", "Lastik durumu"),
    ("lights", "Far/stop/sinyal"),
    ("glass", "Camlar"),
    ("warning_lamps", "Ikaz lambalari"),
    ("water_level", "Su seviyesi"),
]

# Sonuçlar vehicle_inspection_results'ta saklanır (haftalık rapor mevcut vs önceki haftayı karşılaştırır)
# Kötüleşen/tekrarlanan sorunlar için uyarılar oluşturulur
```

### Saat Hesaplama Özel Durumları
```python
# calc.py: calc_day_hours() 8'li tuple döner
(worked_hours, scheduled_hours, overtime_hours, night_hours, overnight_hours,
 special_normal, special_overtime, special_night)

# Gece saatleri: 22:00-06:00 (ertesi gün örtüşmesini içerir)
# Geceye taşan: gece yarısından sonraki saatler (örn. 08:00 → 02:00 = 2s geceye taşan)
# Özel günler: scheduled_hours=0, tüm çalışma özel sayılır (fazla mesai hesabı yok)
# Hafta içi: scheduled = settings["weekday_hours"] (varsayılan 9)
# Cumartesi: scheduled = hours_between(saturday_start, saturday_end)
# Pazar: scheduled = 0 (tümü fazla mesai)
```

## Yaygın İş Akışları

### Puantaj Kaydı Ekleme
1. Kullanıcı çalışan, tarih, giriş/çıkış saati, mola dakikası, isteğe bağlı özel gün checkbox'ı seçer
2. `normalize_date()` ve `normalize_time()` girdileri doğrular (geçersizse ValueError fırlatır)
3. `calc_day_hours()` 8'li tuple saat dağılımını hesaplar
4. Mevcut kullanıcının bölgesiyle `timesheets` tablosuna insert edilir
5. Masaüstü `sync_to_cloud()` çağırır → DB'yi sunucuya yükler

### Araç Yağ Değişim Takibi
- Araç alanları: `oil_change_km` (son değişim), `oil_interval_km` (varsayılan 14000), `current_km`
- Dashboard uyarıları: `current_km - oil_change_km >= oil_interval_km` ise "Zamanı geldi"; 2000 km içindeyse "Yaklaşıyor"
- [server/app.py:get_oil_alerts](server/app.py)'a bakın

### Excel Rapor Dışa Aktarma
- 16 sütunlu düzen: Çalışan, Bölge, Tarih, Giriş, Çıkış, Mola (dk), Çalışılan (s), Plan (s), Fazla Mesai (s), Gece (s), Geceye Taşan (s), Özel Gün, Özel Gün Normal (s), Özel Gün Fazla (s), Özel Gün Gece (s), Not
- Başlıklar: mavi dolgu (`DCE6F1`), kenarlıklar, şirket logosu (sol üst), başlık satırları birleştirilmiş
- Alt kısımda özet bölümüyle toplamlar eklenir
- [report.py:export_report](puantaj_app/report.py)'a bakın

## Dağıtım ve Build

### Masaüstü Build (PyInstaller)
```powershell
# puantaj_app/ klasöründen
pyinstaller Rainstaff.spec
# Çıktı: build/Rainstaff/Rainstaff.exe (debug için console=True)
# Paketlenen varlıklar: assets/ (logo.ico)
```

### Sunucu Dağıtımı (Render)
- GitHub'a push → Render otomatik olarak `server/` klasöründen deploy eder
- Build: `pip install -r requirements.txt` (Flask, gunicorn)
- Başlatma: `gunicorn app:app` ([Procfile](server/Procfile)'a bakın)
- Ortam değişkenleri: `API_KEY`, `SESSION_SECRET`, `PORT` (varsayılan 5000)
- Uyku önleme: UptimeRobot her 5 dakikada `/health`'e ping atar

### Senkronizasyon Yapılandırması
Masaüstü ayarları (Ayarlar → Bulut Senkron):
- `sync_enabled` = 1/0
- `sync_url` = https://rainstaff.onrender.com (veya özel)
- `sync_token` = sunucu `API_KEY` env var ile eşleşmeli

## Test ve Hata Ayıklama

### Loglar
- Masaüstü: `%APPDATA%\Rainstaff\logs\rainstaff.log` (tüm CRUD işlemleri, sync sonuçları, hatalar)
- Canlı log arayüzü: Masaüstü uygulaması "Loglar" sekmesi (log dosyasını takip eder)
- Sunucu: Render dashboard → Logs sekmesi

### Yaygın Tuzaklar
- **Tarih Formatı**: Her zaman normalize edin; şema ISO `YYYY-MM-DD`; UI Türkçe `DD.MM.YYYY` kabul eder
- **Bölge Filtresi**: Eski veride `None` veya eksik `region` sütununa karşı koruma ekleyin (migration ekler)
- **Tkinter Düzeni**: Aynı parent container'da asla `grid()` ve `pack()` karıştırmayın
- **Sync Hatası**: API_KEY eşleşmesini, ağ bağlantısını, DB dosya boyutunu kontrol edin (Render için <100MB)
- **Dashboard 500**: Render loglarını kontrol edin; muhtemelen migration sonrası eksik import veya şema uyumsuzluğu

### Önemli Hata Ayıklama Dosyaları
- Şema değişiklikleri → [db.py:init_db()](puantaj_app/db.py) migration'ları
- UI akışları → [app.py](puantaj_app/app.py) sekme yenileme metodları (örn. `refresh_timesheets_tab()`)
- Rapor sorunları → [report.py](puantaj_app/report.py) sütun sırası şemayla eşleşmeli
- Dashboard sorguları → [server/app.py](server/app.py) route handler'ları (boş sonuçlara karşı `if not data:` ile koruma)

## Kurallar

- **Dil**: Türkçe UI etiketleri, alan adları, hata mesajları (örn. "Calisan", "Tarih", "Ozel Gun")
- **Tarih Gösterimi**: DB'de ISO; gösterim formatı esnek (UI'da DD.MM.YYYY, dışa aktarmalarda YYYY-MM-DD)
- **Bölgeler**: Sabit kodlanmış liste; dinamik bölge oluşturma yok (migration tüm tablolara region ekler)
- **Excel Dışa Aktarma**: Sabit 16 sütunlu düzen; asla başlık sırasını değiştirmeyin (parsing bozulur)
- **Loglama**: Tüm CRUD işlemleri kullanıcı/bölge bağlamıyla loglanır; `logger.info(f"User {username} added employee {name}")` kullanın

## Düzenleme Yapmadan Önce

1. **Şema Değişiklikleri**: [db.py:init_db()](puantaj_app/db.py)'yi güncelleyin VE geriye dönük uyumluluk için `ensure_schema()`'ya migration ekleyin
2. **Yeni UI Sekmesi**: Masaüstü'ye ekleyin ([app.py](puantaj_app/app.py)) ve salt-okunur görünüm gerekiyorsa Dashboard route'u düşünün
3. **Saat Hesaplamaları**: [calc.py](puantaj_app/calc.py)'de özel durumları test edin (geceye taşan, özel günler, Cumartesi özel saatler)
4. **Sync Değişiklikleri**: Geriye dönük uyumluluğu garanti edin; API_KEY auth ile masaüstü→sunucu gidiş-dönüş test edin
5. **Bölgesel Veri**: Bölgeye göre tutarlı filtreleme yapın; asla bölge varsayımları sabit kodlamayın (admin hepsini görür, kullanıcılar sadece kendilerininkini)

## Hızlı Referans

- **Yedekleme**: Masaüstü → Ayarlar → Veri Yönetimi → Yedek Al (`%APPDATA%\Rainstaff\backups\`'te saklanır)
- **Varsayılan Kullanıcılar**: [db.py](puantaj_app/db.py) ve [server/app.py](server/app.py)'de `DEFAULT_USERS`'a bakın
- **Bağımlılıklar**: Masaüstü (openpyxl, Pillow, tkcalendar, requests); Sunucu (Flask, gunicorn)
- **Veri Konumu**: Masaüstü DB `%APPDATA%\Rainstaff\data\puantaj.db`'de; Sunucu DB `server/data/puantaj.db`'de

---

Detaylı mimari için [README.md](README.md)'ye bakın. Bilinen sorunlar/riskler için [puantaj_app/ANALIZ_RAPORU.md](puantaj_app/ANALIZ_RAPORU.md)'ye bakın.
