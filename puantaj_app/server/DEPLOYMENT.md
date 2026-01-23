# 🚀 RainStaff ERP - Render.com Deployment Rehberi

## ✅ HAZIRLIK TAMAMLANDI!

Sisteminiz Render.com'a deploy edilmeye hazır. Aşağıdaki adımları takip edin.

---

## 📋 Adım 1: Render.com Dashboard

1. https://dashboard.render.com adresine gidin
2. GitHub hesabınızla giriş yapın (zaten bağlı)
3. Mevcut "rainstaff" servisinizi bulun

---

## 🔄 Adım 2: PostgreSQL Veritabanı Ekle

### 2.1 Yeni PostgreSQL Oluştur
1. Dashboard'da "New +" → "PostgreSQL"
2. Ayarlar:
   - **Name:** `rainstaff-db`
   - **Database:** `rainstaff`
   - **User:** `rainstaff`
   - **Region:** `Frankfurt`
   - **Plan:** `Free`
3. "Create Database" butonuna tıkla
4. Veritabanı oluşturulurken bekleyin (~2 dakika)

### 2.2 Database URL'yi Kopyala
1. Oluşturulan veritabanına tıklayın
2. "Internal Database URL" veya "External Database URL" kopyalayın
3. Format: `postgresql://user:password@hostname:5432/database`

---

## 🔗 Adım 3: Web Service'i Güncelle

### 3.1 Environment Variables Ekle
1. Dashboard → "rainstaff" servisinizi seçin
2. "Environment" sekmesine gidin
3. "Add Environment Variable" butonuna tıklayın
4. Şu değişkenleri ekleyin:

```
DATABASE_URL = [Adım 2.2'de kopyaladığınız URL]
SECRET_KEY = [Rastgele güçlü bir şifre, örn: rainstaff2026secure]
FLASK_ENV = production
```

### 3.2 Manual Deploy Başlat
1. "Manual Deploy" → "Deploy latest commit"
2. Deploy loglarını izleyin
3. Build tamamlanana kadar bekleyin (~5-10 dakika)

---

## 🗄️ Adım 4: Veritabanını İlklendir

Deploy tamamlandıktan sonra veritabanı otomatik olarak ilklenecek. Kontrol için:

1. Dashboard → rainstaff-db → "Connect"
2. "PSQL Command" kopyalayın
3. Lokal terminalinizde çalıştırın (psql kurulu olmalı)

```bash
psql postgresql://user:password@hostname:5432/database
```

4. Tabloları kontrol edin:
```sql
\dt
SELECT * FROM users;
\q
```

---

## ✅ Adım 5: Test Et

### 5.1 Siteyi Aç
```
https://rainstaff.onrender.com
```

### 5.2 Login Test
- Kullanıcı: `admin`
- Şifre: `748774`

### 5.3 Kontrol Listesi
- [ ] Login sayfası açılıyor
- [ ] Matrix animasyonu çalışıyor
- [ ] Admin girişi başarılı
- [ ] Dashboard yükleniyor
- [ ] RAIN logosu görünüyor
- [ ] Çalışan dropdown çalışıyor
- [ ] Stok dropdown çalışıyor
- [ ] Logout çalışıyor

---

## 🔄 Gelecek Güncellemeler

Kod değişikliği yaptığınızda:

```bash
cd C:\Users\rainwater\Desktop\puantaj\puantaj_app\server
git add .
git commit -m "Güncelleme açıklaması"
git push
```

Render.com otomatik olarak yeni deploy başlatır!

---

## 🛠️ Sorun Giderme

### Deploy Başarısız
1. Render.com → rainstaff → "Logs" sekmesini kontrol et
2. Hata mesajlarını oku
3. `requirements.txt` dosyasını kontrol et

### Database Connection Error
1. `DATABASE_URL` environment variable doğru mu?
2. PostgreSQL veritabanı "Available" durumunda mı?
3. Internal Database URL kullanıyorsanız External'a geçin

### Site Yavaş / Açılmıyor
- Free tier 15 dakika inaktivite sonrası uyur
- İlk istek 30-60 saniye sürebilir (cold start)
- Normal bir durumdur

### Veritabanı Boş
1. `init_postgres.sql` dosyası var mı kontrol et
2. Deploy loglarında "Database initialized" mesajını ara
3. Manuel olarak SQL'i çalıştır:
```bash
psql $DATABASE_URL < init_postgres.sql
```

---

## 📊 Render.com Free Tier

**Avantajlar:**
✅ 750 saat/ay (1 servis için yeterli)
✅ Otomatik HTTPS
✅ PostgreSQL veritabanı (1GB)
✅ Sınırsız deploy
✅ GitHub otomatik deploy

**Dezavantajlar:**
⚠️ 15 dakika inaktivite sonrası uyur
⚠️ Cold start süresi var (~30 saniye)
⚠️ Shared CPU/RAM

---

## 🎯 Öneriler

1. **Uptime Monitoring:** UptimeRobot ile siteyi 5 dakikada bir ping at (uyumasın)
2. **Custom Domain:** Kendi domain'inizi bağlayabilirsiniz
3. **Backup:** PostgreSQL'den düzenli export alın
4. **Logs:** Render.com loglarını düzenli kontrol edin

---

## 📞 Destek

**Render.com Docs:** https://render.com/docs
**PostgreSQL Docs:** https://www.postgresql.org/docs/

---

**Başarılar!** 🎉

Site URL: https://rainstaff.onrender.com
Admin: admin / 748774
