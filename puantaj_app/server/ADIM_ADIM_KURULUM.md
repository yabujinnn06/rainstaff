# 🎯 RainStaff - Render.com Kurulum Rehberi (Resimli)

## 📌 ÖNEMLİ: Bu adımları sırayla takip edin!

---

## ADIM 1: Render.com'a Giriş

1. Tarayıcınızda şu adresi açın: **https://dashboard.render.com**
2. GitHub hesabınızla giriş yapın
3. Dashboard'u görmelisiniz

---

## ADIM 2: PostgreSQL Veritabanı Oluştur

### 2.1 Yeni Veritabanı Başlat
1. Dashboard'da sağ üstte **"New +"** butonuna tıklayın
2. Açılan menüden **"PostgreSQL"** seçin

### 2.2 Veritabanı Ayarları
Şu bilgileri girin:

```
Name: rainstaff-db
Database: rainstaff
User: rainstaff
Region: Frankfurt (EU Central)
PostgreSQL Version: 16 (en son)
Datadog API Key: (boş bırak)
Plan: Free
```

### 2.3 Oluştur
- **"Create Database"** butonuna tıklayın
- Veritabanı oluşturulurken bekleyin (~2-3 dakika)
- Durum "Available" olana kadar bekleyin

### 2.4 Database URL'yi Kopyala
1. Oluşturulan **"rainstaff-db"** veritabanına tıklayın
2. Sayfanın üst kısmında **"Internal Database URL"** göreceksiniz
3. Yanındaki **"Copy"** ikonuna tıklayın
4. URL'yi bir yere yapıştırın (Not Defteri'ne)

**URL formatı şöyle olacak:**
```
postgresql://rainstaff:UZUN_ŞİFRE@dpg-xxxxx-a.frankfurt-postgres.render.com/rainstaff
```

---

## ADIM 3: Web Service'e Dön

1. Sol menüden **"Dashboard"** tıklayın
2. **"rainstaff"** servisinizi bulun ve tıklayın
3. Sol menüden **"Environment"** sekmesine gidin

---

## ADIM 4: Environment Variables Ekle

### 4.1 DATABASE_URL Ekle
1. **"Add Environment Variable"** butonuna tıklayın
2. Şu bilgileri girin:

```
Key: DATABASE_URL
Value: [ADIM 2.4'te kopyaladığınız URL'yi buraya yapıştırın]
```

3. **"Save Changes"** tıklayın

### 4.2 SECRET_KEY Ekle
1. Tekrar **"Add Environment Variable"** tıklayın
2. Şu bilgileri girin:

```
Key: SECRET_KEY
Value: rainstaff2026secure
```

3. **"Save Changes"** tıklayın

### 4.3 FLASK_ENV Ekle
1. Tekrar **"Add Environment Variable"** tıklayın
2. Şu bilgileri girin:

```
Key: FLASK_ENV
Value: production
```

3. **"Save Changes"** tıklayın

---

## ADIM 5: Manuel Deploy Başlat

### 5.1 Deploy Sayfasına Git
1. Sol menüden **"Manual Deploy"** sekmesine gidin
2. Sağ üstte **"Clear build cache & deploy"** butonuna tıklayın

### 5.2 Deploy'u İzle
1. **"Logs"** sekmesine gidin
2. Deploy loglarını izleyin
3. Şu mesajları göreceksiniz:
   ```
   ==> Downloading dependencies
   ==> Installing dependencies
   ==> Building...
   ==> Starting service
   ==> Your service is live 🎉
   ```

### 5.3 Bekleyin
- Deploy süresi: **5-10 dakika**
- "Deploy succeeded" mesajını bekleyin
- Durum: **"Live"** olmalı

---

## ADIM 6: Veritabanını İlklendir

### 6.1 Shell'e Bağlan
1. Sol menüden **"Shell"** sekmesine gidin
2. Sağ üstte **"Connect"** butonuna tıklayın
3. Bir terminal açılacak

### 6.2 SQL Dosyasını Çalıştır
Terminal'de şu komutu yazın:

```bash
python -c "import puantaj_db; puantaj_db.init_db()"
```

Enter'a basın. Şu mesajı görmelisiniz:
```
Database initialized successfully
```

---

## ADIM 7: Siteyi Test Et

### 7.1 Siteyi Aç
1. Sol menüden **"Settings"** sekmesine gidin
2. En üstte sitenizin URL'si var:
   ```
   https://rainstaff.onrender.com
   ```
3. Bu URL'ye tıklayın veya yeni sekmede açın

### 7.2 Login Test
- **Kullanıcı:** admin
- **Şifre:** 748774

### 7.3 Kontrol Listesi
- [ ] Login sayfası açıldı
- [ ] Matrix animasyonu çalışıyor
- [ ] RAIN logosu görünüyor
- [ ] Admin girişi başarılı
- [ ] Dashboard yüklendi
- [ ] Çalışan dropdown çalışıyor
- [ ] Stok dropdown çalışıyor

---

## ✅ TAMAMLANDI!

Siteniz artık canlı: **https://rainstaff.onrender.com**

---

## 🔧 Sorun Giderme

### "Deploy Failed" Hatası
1. **Logs** sekmesinde hata mesajını okuyun
2. Genellikle şu hatalar olur:
   - `DATABASE_URL` yanlış → Tekrar kopyalayıp yapıştırın
   - `requirements.txt` hatası → GitHub'da dosya var mı kontrol edin

### "Application Error" Sayfası
1. **Logs** sekmesinde son satırlara bakın
2. `DATABASE_URL` environment variable ekli mi kontrol edin
3. PostgreSQL veritabanı "Available" durumunda mı kontrol edin

### Site Açılmıyor / Yavaş
- İlk açılış 30-60 saniye sürebilir (cold start)
- 15 dakika kullanılmazsa uyur
- Tekrar açıldığında yine 30-60 saniye bekleyin

### Login Çalışmıyor
1. Shell'de veritabanını kontrol edin:
```bash
python -c "import puantaj_db; print(puantaj_db.list_users())"
```

2. Kullanıcılar yoksa tekrar init edin:
```bash
python -c "import puantaj_db; puantaj_db.init_db()"
```

---

## 📞 Yardım

Sorun yaşarsanız:
1. **Logs** sekmesindeki son 50 satırı kopyalayın
2. Hata mesajını paylaşın
3. Hangi adımda takıldığınızı söyleyin

---

**Başarılar!** 🚀
