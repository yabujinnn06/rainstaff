# Rainstaff v2 - Multi-Tenant ERP Sistemi

Modern, masaüstü-öncelikli çok kiracılı İK ve Filo Yönetim sistemi. Birden fazla şubede (Bursa, Istanbul, Izmir, Ankara) **eş zamanlı kullanım** için tasarlandı.

## 🎯 Özellikler

### ✅ Tamamlanan
- **RBAC Yetkilendirme**: 5 rol (Super Admin → Viewer), 55+ granüler izin
- **Bölgesel İzolasyon**: Her şube sadece kendi verilerini görür (admin hariç)
- **Program İçi Mesajlaşma**: Bölgeler arası mesajlaşma + sistem bildirimleri
- **Çevrimiçi Durum**: 5 dakika heartbeat ile presence tracking
- **Cloud Senkronizasyon**: Çakışma çözümü (4 strateji) + conflict logging
- **SSE Real-Time**: Server-Sent Events ile canlı bildirimler (Render free tier uyumlu)
- **Dark Theme**: Material Design 3, enterprise minimal

### 🔜 Geliştirilmekte
- Çalışan listesi + CRUD
- Puantaj takip ekranı
- Araç ve sürücü yönetimi
- Dashboard KPI kartları
- Excel raporlar

## 🏗️ Mimari

**Desktop-First + Cloud Sync Model**

```
rainstaff-v2/
├── backend/              # İş mantığı ve veri katmanı
│   ├── models/          # SQLAlchemy ORM modelleri
│   ├── services/        # İş mantığı servisleri
│   └── database.py      # Veritabanı bağlantısı
├── frontend/            # Flet UI katmanı
│   ├── views/          # Sayfa görünümleri
│   ├── components/     # Yeniden kullanılabilir bileşenler
│   └── app.py          # Ana Flet uygulaması
├── shared/             # Paylaşılan kodlar
│   ├── auth.py        # Kimlik doğrulama ve yetkilendirme
│   ├── config.py      # Yapılandırma yönetimi
│   └── utils.py       # Yardımcı fonksiyonlar
└── main.py            # Uygulama giriş noktası
```

## Özellikler

### Rol Tabanlı Yetkilendirme (RBAC)
- **Super Admin**: Tüm sistem yönetimi, kullanıcı oluşturma/silme
- **Admin**: Bölge yönetimi, raporlama, veri dışa aktarma
- **Manager**: Onay süreçleri, takım yönetimi
- **User**: Veri girişi, kendi kayıtları
- **Viewer**: Sadece okuma yetkisi

### Modüller
1. **HR (İnsan Kaynakları)**
   - Çalışan yönetimi
   - Puantaj takibi
   - Vardiya planlama
   - İzin yönetimi

2. **Fleet (Filo Yönetimi)**
   - Araç envanteri
   - Sürücü atama
   - Periyodik bakım
   - Muayene takibi
   - Arıza kayıtları

3. **Reports (Raporlar)**
   - Excel dışa aktarma
   - Özelleştirilebilir raporlar
   - Grafik ve analizler

4. **Audit (Denetim Logları)**
   - Tüm işlem kayıtları
   - Kullanıcı aktiviteleri
   - Değişiklik geçmişi

## Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını yapılandır
cp .env.example .env

# Veritabanını oluştur
python -m backend.database init

# Uygulamayı çalıştır
python main.py
```

## Teknoloji Stack

- **UI**: Flet (Flutter-based Python framework)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Auth**: JWT + bcrypt
- **Database**: SQLite (local) + PostgreSQL (cloud option)
- **Export**: openpyxl
- **Logging**: loguru

## Güvenlik

- Bcrypt ile şifrelenmiş parolalar
- JWT token tabanlı oturum yönetimi
- Granüler izin kontrolleri
- Audit log ile tam izlenebilirlik
- SQL injection koruması (ORM)

## Cloud Sync

Desktop-first mimari ile Render ücretsiz tier'da çalışır:
- Minimal API footprint
- Batch sync (anlık değil)
- Offline çalışma desteği
- Conflict resolution

## Lisans

Proprietary - Rainstaff © 2026
