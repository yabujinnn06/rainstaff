# 🌧️ RainStaff ERP - Matrix Edition

Modern, minimal ve güvenli iç denetim ve yönetim sistemi.

## 🎨 Özellikler

### Matrix Teması
- Siyah arka plan
- Yeşil Matrix yağmuru animasyonu
- Neon yeşil (#00ff41) renk şeması
- Courier New monospace font
- Hiç emoji/ikon yok - Sadece temiz metin

### Modüller
- 👥 **Çalışan Yönetimi** - Dropdown ile mesai detayları
- ⏰ **Puantaj Sistemi** - Otomatik fazla mesai hesaplama
- 📦 **Stok Yönetimi** - Dropdown ile seri numaraları
- 📊 **Raporlama** - Excel export/import
- 🚗 **Araç Takibi** - Bakım ve kontrol sistemi

### Güvenlik
- JWT token bazlı authentication
- Rol bazlı yetkilendirme (Admin, Yönetici, Çalışan)
- Şifreli veritabanı
- Login sayfasında şifre listesi yok

## 🚀 Deployment (Render.com)

### 1. GitHub Repository Oluştur

```bash
cd C:\Users\rainwater\Desktop\puantaj\puantaj_app\server
git init
git add .
git commit -m "Initial commit - RainStaff ERP Matrix Edition"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADINIZ/rainstaff-erp.git
git push -u origin main
```

### 2. Render.com'da Deploy

1. https://render.com adresine git
2. "New +" → "Web Service" seç
3. GitHub repository'nizi bağlayın
4. Ayarlar:
   - **Name:** rainstaff-erp
   - **Region:** Frankfurt (veya en yakın)
   - **Branch:** main
   - **Root Directory:** (boş bırak)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

5. **Add Disk** (ÖNEMLİ - Veritabanı için):
   - **Name:** rainstaff-data
   - **Mount Path:** /data
   - **Size:** 1 GB

6. "Create Web Service" butonuna tıkla

### 3. Deploy Sonrası

Site URL'niz: `https://rainstaff-erp.onrender.com`

**İlk Giriş:**
- Admin: `admin` / `748774`

## 💻 Lokal Geliştirme

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Sunucuyu başlat
python app.py

# Tarayıcıda aç
http://127.0.0.1:5000
```

## 🔐 Kullanıcılar

| Kullanıcı | Şifre | Rol | Bölge |
|-----------|-------|-----|-------|
| admin | 748774 | Admin | Tümü |
| ankara1 | 060106 | User | Ankara |
| izmir1 | 350235 | User | İzmir |
| bursa1 | 160316 | User | Bursa |
| istanbul1 | 340434 | User | İstanbul |

## 📁 Proje Yapısı

```
server/
├── app.py                 # Ana Flask uygulaması
├── puantaj_db.py         # Veritabanı işlemleri
├── calc.py               # Mesai hesaplamaları
├── requirements.txt      # Python bağımlılıkları
├── render.yaml          # Render.com config
├── .gitignore           # Git ignore dosyası
├── templates/           # HTML şablonları
│   ├── login.html
│   ├── modern_dashboard.html
│   ├── 404.html
│   ├── 500.html
│   └── error.html
└── static/              # Statik dosyalar
    └── matrix-rain.js   # Matrix animasyonu
```

## 🛠️ Teknolojiler

- **Backend:** Flask 3.0
- **Database:** SQLite (persistent disk)
- **Frontend:** Vanilla JS, HTML5, CSS3
- **Server:** Gunicorn
- **Hosting:** Render.com (Free tier)

## 📝 Notlar

- Render.com free tier 15 dakika inaktivite sonrası uyur
- İlk istek 30-60 saniye sürebilir (cold start)
- Persistent disk sayesinde veriler korunur
- Otomatik HTTPS sertifikası

## 🎯 Özellikler

✅ Matrix teması (yeşil + siyah)
✅ Hiç emoji/ikon yok
✅ Minimal "RAIN" logosu
✅ Dropdown menüler (çalışan + stok)
✅ Otomatik hesaplamalar
✅ Güvenli login
✅ Responsive tasarım
✅ Excel import/export
✅ Çoklu şube desteği

## 📞 Destek

Sorularınız için: rainwater@rainstaff.com

---

**RainStaff ERP** - Modern İç Denetim Sistemi 🌧️
