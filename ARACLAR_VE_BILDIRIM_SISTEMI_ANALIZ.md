# 🚗 ARAÇLAR MODÜLÜ VE BİLDİRİM SİSTEMİ - KAPSAMLI ANALİZ RAPORU

**Tarih:** 2026-01-26  
**Proje:** Rainstaff ERP  
**Analiz Eden:** BLACKBOXAI  
**Token Bütçesi:** $20

---

## 📊 MEVCUT DURUM ANALİZİ

### ✅ Kullanılan Teknolojiler

**Backend:**
- Flask (Python)
- SQLite Database
- `puantaj_db.py` modülü (KULLANILIYOR ✓)

**Frontend:**
- HTML5, CSS3, JavaScript
- Matrix tema (yeşil, siyah, monospace)
- Responsive design

**Database Dosyası:**
- `puantaj_app/data/puantaj.db` (local)
- `/data/puantaj.db` (Render production)

### 📁 Mevcut Dosya Yapısı

```
puantaj_app/server/
├── app.py                    # Flask routes (puantaj_db kullanıyor)
├── puantaj_db.py            # Database modülü (ANA MODÜL)
├── calc.py                  # Mesai hesaplama
├── templates/
│   ├── modern_dashboard.html  # Ana dashboard (tab'lı)
│   ├── vehicles.html         # Araçlar sayfası (ayrı sayfa)
│   ├── drivers.html          # Sürücüler sayfası
│   ├── vehicle_faults.html   # Arızalar sayfası
│   └── base.html            # Base template
└── static/
    ├── style.css            # Ana CSS
    ├── matrix-fix.css       # Matrix tema
    └── app.js               # JavaScript
```

### 🗄️ Veritabanı Tabloları

**Araçlar İçin Mevcut Tablolar:**
1. `vehicles` - Araç bilgileri
   - Kolonlar: id, plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date, oil_change_date, oil_change_km, oil_interval_km, notes, region

2. `drivers` - Sürücü bilgileri
   - Kolonlar: id, full_name, license_class, license_expiry, phone, notes, region

3. `vehicle_faults` - Arıza kayıtları
   - Kolonlar: id, vehicle_id, title, description, opened_date, closed_date, status, region

4. `vehicle_inspections` - Haftalık kontroller
   - Kolonlar: id, vehicle_id, driver_id, inspection_date, week_start, km, notes, fault_id, fault_status, service_visit

5. `vehicle_service_visits` - Sanayi kayıtları
   - Kolonlar: id, vehicle_id, fault_id, start_date, end_date, reason, cost, notes, region

6. `vehicle_inspection_results` - Kontrol detayları
   - Kolonlar: id, inspection_id, item_key, status, note

**Diğer Tablolar:**
- `employees`, `timesheets`, `users`, `settings`, `stock_inventory`, `deleted_records`

### 🔌 Mevcut API Endpoint'leri

**Araçlar:**
- `GET /vehicles` - Araçlar sayfası (HTML)
- `GET /api/vehicles` - Araç listesi + uyarılar (JSON)
- `GET /drivers` - Sürücüler sayfası (HTML)
- `GET /api/drivers` - Sürücü listesi + uyarılar (JSON)
- `GET /vehicle-faults` - Arızalar sayfası (HTML)
- `GET /api/vehicle-faults` - Arıza listesi (JSON)

**Mevcut Özellikler:**
✅ Araç listesi görüntüleme
✅ Uyarı hesaplama (muayene, sigorta, bakım)
✅ Filtreleme (bölge, durum)
✅ Arama (plaka, marka, model)
✅ Detay görüntüleme (dropdown)
✅ Responsive tasarım

**Eksik Özellikler:**
❌ Dashboard entegrasyonu (ayrı sayfa olarak çalışıyor)
❌ Görsel kartlar
❌ Progress bar'lar (yağ değişimi)
❌ QR kod
❌ PDF export
❌ Yakıt takibi
❌ Lastik takibi
❌ Kaza kayıtları
❌ Timeline görünümü
❌ Push notification sistemi

---

## 🎯 HEDEFLER VE PLANLAMA

### Faz 1: Araçlar Modülü Dashboard Entegrasyonu (2-3 saat)

**1.1. Dashboard'a Tab Ekleme**
- `modern_dashboard.html`'e "ARAÇLAR" tab'ı ekle
- Mevcut tab'lar: Overview, Çalışanlar, Puantaj, Stok, Raporlar
- Yeni: **Araçlar** tab'ı

**1.2. API Endpoint'leri Hazırlama**
- `/api/vehicles` - Zaten var ✓
- `/api/vehicle-stats` - İstatistikler için yeni endpoint
- `/api/vehicle-timeline/<vehicle_id>` - Timeline için yeni endpoint

**1.3. Frontend Geliştirme**
- Araç kartları (grid layout)
- Durum göstergeleri (yeşil/sarı/kırmızı)
- Progress bar (yağ değişimi)
- Filtreleme ve arama
- Detay modal

**Dosyalar:**
- ✏️ `puantaj_app/server/templates/modern_dashboard.html` - Tab ve UI ekle
- ✏️ `puantaj_app/server/app.py` - Yeni API endpoint'leri ekle

---

### Faz 2: Gelişmiş Özellikler (3-4 saat)

**2.1. Yakıt Takibi**
- Yeni tablo: `vehicle_fuel_records`
  - Kolonlar: id, vehicle_id, date, km, liters, cost, station, notes, region
- API: `/api/vehicle-fuel/<vehicle_id>`
- UI: Yakıt geçmişi, tüketim analizi

**2.2. Lastik Takibi**
- Yeni tablo: `vehicle_tire_records`
  - Kolonlar: id, vehicle_id, date, km, position, brand, cost, notes, region
- API: `/api/vehicle-tires/<vehicle_id>`
- UI: Lastik geçmişi

**2.3. Kaza Kayıtları**
- Yeni tablo: `vehicle_accidents`
  - Kolonlar: id, vehicle_id, date, location, description, damage_cost, insurance_claim, notes, region
- API: `/api/vehicle-accidents/<vehicle_id>`
- UI: Kaza geçmişi

**2.4. QR Kod ve PDF Export**
- QR kod oluşturma (her araç için unique)
- PDF rapor (araç özeti, geçmiş, uyarılar)
- Kütüphaneler: `qrcode`, `jsPDF`

**Dosyalar:**
- ✏️ `puantaj_app/puantaj_db.py` - Yeni tablolar ve fonksiyonlar
- ✏️ `puantaj_app/server/app.py` - Yeni API endpoint'leri
- ✏️ `puantaj_app/server/templates/modern_dashboard.html` - UI güncellemeleri

---

### Faz 3: Push Notification Sistemi (4-5 saat)

**3.1. Backend Notification Service**

**Yeni Tablo: `notification_subscriptions`**
```sql
CREATE TABLE notification_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

**Yeni Tablo: `notification_logs`**
```sql
CREATE TABLE notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    sent_at TEXT NOT NULL,
    status TEXT DEFAULT 'sent'
);
```

**Bildirim Türleri:**
- `data_entry` - Veri girişi yapıldı
- `vehicle_inspection_due` - Muayene yaklaşıyor
- `vehicle_insurance_due` - Sigorta yaklaşıyor
- `vehicle_maintenance_due` - Bakım yaklaşıyor
- `vehicle_oil_change_due` - Yağ değişimi yaklaşıyor
- `vehicle_fault_opened` - Yeni arıza açıldı
- `vehicle_fault_closed` - Arıza kapatıldı
- `vehicle_service_started` - Sanayi girişi
- `vehicle_service_completed` - Sanayi çıkışı
- `employee_added` - Yeni çalışan eklendi
- `timesheet_added` - Yeni puantaj eklendi
- `stock_low` - Stok azaldı

**Backend Fonksiyonlar:**
```python
# puantaj_app/puantaj_db.py
def save_notification_subscription(user_id, endpoint, p256dh, auth)
def get_user_subscriptions(user_id)
def delete_subscription(subscription_id)
def log_notification(user_id, type, title, message, data)
def get_notification_logs(user_id, limit=50)

# puantaj_app/server/notification_service.py (YENİ DOSYA)
def send_push_notification(subscription, title, message, data)
def send_to_user(user_id, title, message, data)
def send_to_all_users(title, message, data)
def check_vehicle_alerts_and_notify()  # Cron job için
```

**API Endpoint'leri:**
```python
POST /api/notifications/subscribe    # Kullanıcı bildirim izni veriyor
POST /api/notifications/unsubscribe  # Kullanıcı bildirimi iptal ediyor
GET  /api/notifications/logs         # Bildirim geçmişi
POST /api/notifications/test         # Test bildirimi gönder
```

**3.2. Frontend Service Worker**

**Yeni Dosya: `puantaj_app/server/static/sw.js`**
```javascript
// Service Worker for push notifications
self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.message,
        icon: '/static/logo.png',
        badge: '/static/badge.png',
        vibrate: [200, 100, 200],
        data: data.data,
        actions: data.actions || []
    };
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/dashboard')
    );
});
```

**3.3. Frontend Notification Manager**

**Yeni Dosya: `puantaj_app/server/static/notifications.js`**
```javascript
class NotificationManager {
    constructor() {
        this.publicKey = 'YOUR_VAPID_PUBLIC_KEY';
    }

    async requestPermission() {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            await this.subscribe();
        }
        return permission;
    }

    async subscribe() {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: this.urlBase64ToUint8Array(this.publicKey)
        });
        
        // Send subscription to server
        await fetch('/api/notifications/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subscription)
        });
    }

    async unsubscribe() {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
            await subscription.unsubscribe();
            await fetch('/api/notifications/unsubscribe', { method: 'POST' });
        }
    }

    urlBase64ToUint8Array(base64String) {
        // Conversion logic
    }
}
```

**3.4. VAPID Keys Oluşturma**

```python
# Yeni dosya: puantaj_app/server/generate_vapid_keys.py
from py_vapid import Vapid

vapid = Vapid()
vapid.generate_keys()

print("VAPID_PUBLIC_KEY:", vapid.public_key.decode())
print("VAPID_PRIVATE_KEY:", vapid.private_key.decode())
print("VAPID_CLAIMS:", {"sub": "mailto:admin@rainstaff.com"})
```

**3.5. Notification Settings UI**

Dashboard'a bildirim ayarları paneli:
- Bildirim izni ver/kaldır butonu
- Bildirim türlerini seç (checkboxlar)
- Test bildirimi gönder butonu
- Bildirim geçmişi

---

## 📋 UYGULAMA PLANI

### Adım 1: Araçlar Dashboard Entegrasyonu

**1.1. modern_dashboard.html'e Tab Ekle**
```html
<button class="nav-tab" onclick="showTab('vehicles')">ARAÇLAR</button>
```

**1.2. Araçlar Tab İçeriği**
```html
<div id="vehicles" class="tab-content">
    <!-- Stats Grid -->
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Toplam Araç</h3>
            <div class="value" id="total-vehicles">-</div>
        </div>
        <div class="stat-card">
            <h3>Kritik Uyarı</h3>
            <div class="value" id="critical-vehicles">-</div>
        </div>
        <div class="stat-card">
            <h3>Yaklaşan İşlemler</h3>
            <div class="value" id="warning-vehicles">-</div>
        </div>
        <div class="stat-card">
            <h3>Normal Durum</h3>
            <div class="value" id="normal-vehicles">-</div>
        </div>
    </div>

    <!-- Vehicle Cards Grid -->
    <div id="vehicles-grid" class="vehicles-grid">
        <!-- Araç kartları buraya gelecek -->
    </div>
</div>
```

**1.3. CSS Stilleri**
```css
.vehicles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.vehicle-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}

.vehicle-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--primary-color);
}

.vehicle-card.critical::before {
    background: #ff4444;
    box-shadow: 0 0 10px #ff4444;
}

.vehicle-card.warning::before {
    background: #ff9800;
}

.vehicle-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 255, 65, 0.2);
}

.vehicle-plate {
    font-size: 24px;
    font-weight: 700;
    color: var(--primary-color);
    font-family: 'Courier New', monospace;
    margin-bottom: 10px;
}

.vehicle-info {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 15px;
}

.vehicle-alerts {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.alert-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    font-size: 12px;
}

.oil-progress {
    margin-top: 15px;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #333;
    border: 1px solid var(--primary-color);
    border-radius: 0;
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s;
    box-shadow: 0 0 10px var(--primary-color);
}

.progress-fill.warning {
    background: #ff9800;
    box-shadow: 0 0 10px #ff9800;
}

.progress-fill.critical {
    background: #ff4444;
    box-shadow: 0 0 10px #ff4444;
}
```

**1.4. JavaScript Fonksiyonları**
```javascript
function loadVehiclesTab() {
    fetch('/api/vehicles')
        .then(res => res.json())
        .then(data => {
            renderVehicleCards(data);
            updateVehicleStats(data);
        });
}

function renderVehicleCards(vehicles) {
    const grid = document.getElementById('vehicles-grid');
    let html = '';
    
    vehicles.forEach(v => {
        const status = getVehicleStatus(v.alerts);
        const oilProgress = calculateOilProgress(v);
        
        html += `
            <div class="vehicle-card ${status}">
                <div class="vehicle-plate">${v.plate}</div>
                <div class="vehicle-info">${v.brand} ${v.model} (${v.year})</div>
                <div class="vehicle-info">KM: ${v.km?.toLocaleString() || '-'}</div>
                
                <div class="vehicle-alerts">
                    ${renderAlerts(v.alerts)}
                </div>
                
                ${oilProgress ? `
                    <div class="oil-progress">
                        <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 5px;">
                            YAĞ DEĞİŞİMİ: ${oilProgress.current}/${oilProgress.target} km
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill ${oilProgress.status}" 
                                 style="width: ${oilProgress.percentage}%;"></div>
                        </div>
                    </div>
                ` : ''}
                
                <button onclick="showVehicleDetails(${v.id})" 
                        class="matrix-btn matrix-btn-primary" 
                        style="width: 100%; margin-top: 15px; font-size: 10px;">
                    [ DETAYLAR ]
                </button>
            </div>
        `;
    });
    
    grid.innerHTML = html;
}

function calculateOilProgress(vehicle) {
    if (!vehicle.oil_change_km || !vehicle.oil_interval_km || !vehicle.km) {
        return null;
    }
    
    const current = vehicle.km - vehicle.oil_change_km;
    const target = vehicle.oil_interval_km;
    const percentage = Math.min((current / target) * 100, 100);
    
    let status = 'normal';
    if (percentage >= 90) status = 'critical';
    else if (percentage >= 75) status = 'warning';
    
    return { current, target, percentage, status };
}
```

---

### Faz 3: Push Notification Sistemi (4-5 saat)

**3.1. Gerekli Kütüphaneler**
```txt
# requirements.txt'e ekle
pywebpush==1.14.0
py-vapid==1.8.2
```

**3.2. Backend Notification Service**

**Yeni Dosya: `puantaj_app/server/notification_service.py`**
```python
import json
from pywebpush import webpush, WebPushException
import puantaj_db as db

# VAPID keys (generate_vapid_keys.py ile oluşturulacak)
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {"sub": "mailto:admin@rainstaff.com"}

def send_push_notification(subscription_info, title, message, data=None):
    """Send push notification to a single subscription"""
    try:
        payload = json.dumps({
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })
        
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        return True
    except WebPushException as e:
        print(f"Push failed: {e}")
        # If subscription is invalid, remove it
        if e.response and e.response.status_code in [404, 410]:
            # Subscription expired, remove from DB
            pass
        return False

def send_to_user(user_id, title, message, data=None, notification_type='info'):
    """Send notification to all subscriptions of a user"""
    subscriptions = db.get_user_subscriptions(user_id)
    success_count = 0
    
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub['endpoint'],
            "keys": {
                "p256dh": sub['p256dh'],
                "auth": sub['auth']
            }
        }
        
        if send_push_notification(subscription_info, title, message, data):
            success_count += 1
    
    # Log notification
    db.log_notification(user_id, notification_type, title, message, json.dumps(data))
    
    return success_count

def send_to_all_users(title, message, data=None, notification_type='info'):
    """Send notification to all users with subscriptions"""
    users = db.get_all_users()
    total_sent = 0
    
    for user in users:
        sent = send_to_user(user['id'], title, message, data, notification_type)
        total_sent += sent
    
    return total_sent

def check_vehicle_alerts_and_notify():
    """Check for vehicle alerts and send notifications (run daily via cron)"""
    from datetime import datetime, timedelta
    
    vehicles = db.list_vehicles()
    today = datetime.now().date()
    
    for v in vehicles:
        vehicle_id, plate, brand, model, year, km, inspection_date, insurance_date, \
        maintenance_date, oil_change_date, oil_change_km, oil_interval_km, notes, region = v
        
        # Check inspection
        if inspection_date:
            try:
                insp_date = datetime.strptime(inspection_date, '%Y-%m-%d').date()
                days_until = (insp_date - today).days
                
                if days_until == 7:
                    send_to_all_users(
                        f"🚗 Muayene Uyarısı - {plate}",
                        f"{plate} plakalı aracın muayenesi 7 gün içinde sona eriyor!",
                        {"vehicle_id": vehicle_id, "type": "inspection"},
                        "vehicle_inspection_due"
                    )
                elif days_until == 1:
                    send_to_all_users(
                        f"🚨 ACİL: Muayene - {plate}",
                        f"{plate} plakalı aracın muayenesi YARIN sona eriyor!",
                        {"vehicle_id": vehicle_id, "type": "inspection"},
                        "vehicle_inspection_due"
                    )
            except:
                pass
        
        # Check insurance
        if insurance_date:
            try:
                ins_date = datetime.strptime(insurance_date, '%Y-%m-%d').date()
                days_until = (ins_date - today).days
                
                if days_until == 7:
                    send_to_all_users(
                        f"🛡️ Sigorta Uyarısı - {plate}",
                        f"{plate} plakalı aracın sigortası 7 gün içinde sona eriyor!",
                        {"vehicle_id": vehicle_id, "type": "insurance"},
                        "vehicle_insurance_due"
                    )
            except:
                pass
        
        # Check oil change
        if oil_change_km and oil_interval_km and km:
            km_since_change = km - oil_change_km
            remaining = oil_interval_km - km_since_change
            
            if remaining <= 500 and remaining > 0:
                send_to_all_users(
                    f"🛢️ Yağ Değişimi - {plate}",
                    f"{plate} plakalı aracın yağ değişimine {remaining} km kaldı!",
                    {"vehicle_id": vehicle_id, "type": "oil_change"},
                    "vehicle_oil_change_due"
                )
```

**3.3. API Endpoint'leri Ekleme**

**`puantaj_app/server/app.py`'ye ekle:**
```python
import notification_service as notif

@app.route('/api/notifications/subscribe', methods=['POST'])
def api_subscribe_notifications():
    """Subscribe user to push notifications"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        user = db.get_user(session['user_id'])
        
        db.save_notification_subscription(
            user['id'],
            data['endpoint'],
            data['keys']['p256dh'],
            data['keys']['auth']
        )
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/unsubscribe', methods=['POST'])
def api_unsubscribe_notifications():
    """Unsubscribe user from push notifications"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user = db.get_user(session['user_id'])
        db.delete_user_subscriptions(user['id'])
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/test', methods=['POST'])
def api_test_notification():
    """Send test notification"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user = db.get_user(session['user_id'])
        count = notif.send_to_user(
            user['id'],
            "🧪 Test Bildirimi",
            "Rainstaff bildirim sistemi çalışıyor!",
            {"test": True},
            "test"
        )
        return jsonify({'success': True, 'sent': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/logs')
def api_notification_logs():
    """Get notification history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user = db.get_user(session['user_id'])
        logs = db.get_notification_logs(user['id'], limit=50)
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**3.4. Cron Job Setup (Render)**

**`render.yaml`'e ekle:**
```yaml
services:
  - type: web
    name: rainstaff-web
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app:app"
    
  - type: cron
    name: rainstaff-alerts
    env: python
    schedule: "0 9 * * *"  # Her gün saat 09:00
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python check_alerts.py"
```

**Yeni Dosya: `puantaj_app/server/check_alerts.py`**
```python
#!/usr/bin/env python3
"""
Daily cron job to check vehicle alerts and send notifications
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import notification_service as notif

if __name__ == '__main__':
    print("Checking vehicle alerts...")
    notif.check_vehicle_alerts_and_notify()
    print("Done!")
```

---

## 📊 DOSYA DEĞİŞİKLİK PLANI

### Değiştirilecek Dosyalar

1. **`puantaj_app/puantaj_db.py`**
   - Notification tabloları ekle
   - Notification fonksiyonları ekle
   - Yakıt, lastik, kaza tabloları ekle

2. **`puantaj_app/server/app.py`**
   - Notification API endpoint'leri ekle
   - Vehicle stats API ekle
   - Timeline API ekle

3. **`puantaj_app/server/templates/modern_dashboard.html`**
   - Araçlar tab'ı ekle
   - Araç kartları UI ekle
   - Notification settings panel ekle

4. **`puantaj_app
