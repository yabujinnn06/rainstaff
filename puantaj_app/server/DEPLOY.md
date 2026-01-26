# 🚀 RainStaff ERP - Deployment Rehberi

## Adım 1: GitHub Repository Oluştur

### 1.1 GitHub'da Yeni Repo Oluştur
1. https://github.com adresine git
2. Sağ üstte "+" → "New repository"
3. Repository adı: `rainstaff-erp`
4. Description: "Matrix themed ERP system for internal management"
5. Public veya Private seç
6. **Initialize this repository with a README** seçeneğini IŞARETLEME
7. "Create repository" butonuna tıkla

### 1.2 Git Kurulumu Kontrol
```bash
git --version
```

Eğer Git yüklü değilse: https://git-scm.com/download/win

### 1.3 Lokal Repository Oluştur ve Push Et

Terminal'de (PowerShell veya CMD) şu komutları çalıştır:

```bash
# Server klasörüne git
cd C:\Users\rainwater\Desktop\puantaj\puantaj_app\server

# Git repository başlat
git init

# Tüm dosyaları ekle
git add .

# İlk commit
git commit -m "Initial commit - RainStaff ERP Matrix Edition"

# Ana branch'i main yap
git branch -M main

# GitHub repository'nizi bağlayın (KULLANICI_ADINIZ'ı değiştirin)
git remote add origin https://github.com/KULLANICI_ADINIZ/rainstaff-erp.git

# Push et
git push -u origin main
```

**NOT:** GitHub kullanıcı adı ve token isteyecek. Token oluşturmak için:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" → "Generate new token (classic)"
3. Note: "RainStaff Deploy"
4. Expiration: 90 days
5. Scopes: `repo` seçeneğini işaretle
6. "Generate token" butonuna tıkla
7. Token'ı kopyala ve güvenli bir yerde sakla

## Adım 2: Render.com'da Deploy

### 2.1 Render.com Hesabı Oluştur
1. https://render.com adresine git
2. "Get Started" → GitHub ile giriş yap
3. GitHub hesabınızı bağlayın

### 2.2 Web Service Oluştur
1. Dashboard'da "New +" → "Web Service"
2. GitHub repository'nizi seç: `rainstaff-erp`
3. "Connect" butonuna tıkla

### 2.3 Ayarları Yapılandır

**Basic Settings:**
- **Name:** `rainstaff-erp` (veya istediğiniz isim)
- **Region:** `Frankfurt` (veya size en yakın)
- **Branch:** `main`
- **Root Directory:** (boş bırak)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Instance Type:**
- **Plan:** `Free` (0$/ay)

### 2.4 Environment Variables (Opsiyonel)
"Advanced" → "Add Environment Variable":
- `PYTHON_VERSION` = `3.11.0`
- `PORT` = `10000`

### 2.5 Persistent Disk Ekle (ÖNEMLİ!)
"Advanced" → "Add Disk":
- **Name:** `rainstaff-data`
- **Mount Path:** `/data`
- **Size:** `1 GB`

**NOT:** Bu disk veritabanınızı saklar. Olmadan her deploy'da veriler silinir!

### 2.6 Deploy Et
1. "Create Web Service" butonuna tıkla
2. Deploy başlayacak (5-10 dakika sürer)
3. Logları izleyin

## Adım 3: Deploy Sonrası

### 3.1 Site URL'niz
Deploy tamamlandığında URL'niz:
```
https://rainstaff.onrender.com
```
(veya seçtiğiniz isim)

### 3.2 İlk Giriş
- Kullanıcı: `admin`
- Şifre: `748774`

### 3.3 Test Et
1. Login sayfasını aç
2. Admin ile giriş yap
3. Dashboard'u kontrol et
4. Çalışan dropdown'ını test et
5. Stok dropdown'ını test et

## Adım 4: Güncelleme (Update)

Kod değişikliği yaptığınızda:

```bash
cd C:\Users\rainwater\Desktop\puantaj\puantaj_app\server

# Değişiklikleri ekle
git add .

# Commit
git commit -m "Açıklama buraya"

# Push
git push
```

Render.com otomatik olarak yeni deploy başlatır!

## 🔧 Sorun Giderme

### Deploy Başarısız Olursa
1. Render.com loglarını kontrol et
2. `requirements.txt` dosyasını kontrol et
3. `app.py` dosyasında syntax hatası var mı kontrol et

### Site Açılmıyorsa
1. Render.com dashboard'da "Events" sekmesini kontrol et
2. "Logs" sekmesinde hata mesajlarını oku
3. Disk mount edilmiş mi kontrol et

### Veritabanı Sıfırlanıyorsa
- Persistent disk eklenmiş mi kontrol et
- Mount path `/data` olmalı
- `puantaj_db.py` dosyasında `DB_DIR` doğru mu kontrol et

### Cold Start (İlk Yükleme Yavaş)
- Render.com free tier 15 dakika inaktivite sonrası uyur
- İlk istek 30-60 saniye sürebilir
- Normal bir durumdur

## 📊 Render.com Free Tier Limitleri

- ✅ 750 saat/ay (1 servis için yeterli)
- ✅ Otomatik HTTPS
- ✅ 1 GB persistent disk
- ✅ Sınırsız deploy
- ⚠️ 15 dakika inaktivite sonrası uyur
- ⚠️ Cold start süresi var

## 🎯 Öneriler

1. **Custom Domain:** Render.com'da kendi domain'inizi bağlayabilirsiniz
2. **Monitoring:** Uptime Robot gibi servislerle site'yi aktif tutabilirsiniz
3. **Backup:** Düzenli veritabanı yedekleri alın
4. **Security:** Production'da güçlü şifreler kullanın

## 📞 Yardım

Sorun yaşarsanız:
1. Render.com documentation: https://render.com/docs
2. GitHub Issues: Repository'nizde issue açın
3. Render.com support: support@render.com

---

**Başarılar!** 🚀
