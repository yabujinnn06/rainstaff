"""
Seed test data for vehicles module
Matrix-themed test data
"""
import sys
sys.path.insert(0, 'puantaj_app')
import puantaj_db as db
from datetime import datetime, timedelta

def seed_vehicles():
    """Add test vehicles"""
    print("\n=== SEEDING VEHICLES ===")
    
    vehicles = [
        # (plate, brand, model, year, km, inspection_date, insurance_date, maintenance_date, 
        #  oil_change_date, oil_change_km, oil_interval_km, notes, region)
        ("34 ABC 123", "Toyota", "Corolla", "2020", 45000, 
         (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),  # Critical: 5 days
         (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),  # Warning: 25 days
         (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),  # Normal: 60 days
         (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
         40000, 10000, "Matrix takip sistemi aktif", "Ankara"),
        
        ("06 XYZ 456", "Ford", "Transit", "2019", 78000,
         (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),  # EXPIRED!
         (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),   # Critical: 3 days
         (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),  # Warning: 15 days
         (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
         70000, 10000, "Yüksek km, yakın takip gerekli", "Ankara"),
        
        ("35 DEF 789", "Mercedes", "Sprinter", "2021", 32000,
         (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),  # Normal
         (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'), # Normal
         (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),  # Normal
         (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
         28000, 15000, "Yeni araç, düzenli bakım", "Istanbul"),
        
        ("16 GHI 012", "Volkswagen", "Caddy", "2018", 95000,
         (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),   # Critical: 2 days
         (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d'),   # Warning: 8 days
         (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),  # Warning: 30 days
         (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
         85000, 10000, "Yağ değişimi acil!", "Bursa"),
        
        ("41 JKL 345", "Renault", "Master", "2022", 18000,
         (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), # Normal
         (datetime.now() + timedelta(days=200)).strftime('%Y-%m-%d'), # Normal
         (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),  # Normal
         (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
         15000, 15000, "Sıfır gibi, Matrix koruması altında", "Izmir"),
    ]
    
    for v in vehicles:
        try:
            db.add_vehicle(*v)
            print(f"  ✓ Added: {v[0]} - {v[1]} {v[2]}")
        except Exception as e:
            print(f"  ✗ Error adding {v[0]}: {e}")

def seed_drivers():
    """Add test drivers"""
    print("\n=== SEEDING DRIVERS ===")
    
    drivers = [
        # (full_name, license_class, license_expiry, phone, notes, region)
        ("Neo Anderson", "B,C,E", 
         (datetime.now() + timedelta(days=400)).strftime('%Y-%m-%d'),
         "0555 123 4567", "Matrix'in seçilmiş sürücüsü", "Ankara"),
        
        ("Trinity", "B,C", 
         (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),  # Warning!
         "0555 234 5678", "Hacker sürücü, dikkatli", "Ankara"),
        
        ("Morpheus", "B,C,D,E", 
         (datetime.now() + timedelta(days=600)).strftime('%Y-%m-%d'),
         "0555 345 6789", "Deneyimli kaptan", "Istanbul"),
        
        ("Agent Smith", "B", 
         (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),  # EXPIRED!
         "0555 456 7890", "Ehliyet yenileme gerekli!", "Bursa"),
        
        ("Oracle", "B,C", 
         (datetime.now() + timedelta(days=200)).strftime('%Y-%m-%d'),
         "0555 567 8901", "Her şeyi bilen sürücü", "Izmir"),
    ]
    
    for d in drivers:
        try:
            db.add_driver(*d)
            print(f"  ✓ Added: {d[0]} - {d[1]}")
        except Exception as e:
            print(f"  ✗ Error adding {d[0]}: {e}")

def seed_faults():
    """Add test vehicle faults"""
    print("\n=== SEEDING VEHICLE FAULTS ===")
    
    # Get vehicles first
    vehicles = db.list_vehicles()
    if not vehicles:
        print("  ✗ No vehicles found, skipping faults")
        return
    
    faults = [
        # (vehicle_id, title, description, opened_date, closed_date, status, region)
        (vehicles[0][0], "Motor Arızası", "Matrix glitch tespit edildi, motor kontrol ünitesi arızalı",
         (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
         None, "Acik", "Ankara"),
        
        (vehicles[1][0], "Fren Sistemi", "Fren balatası aşınmış, acil değişim gerekli",
         (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
         (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
         "Kapali", "Ankara"),
        
        (vehicles[1][0], "Elektrik Arızası", "Far sistemi çalışmıyor, kablo kontrolü yapılacak",
         (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
         None, "Acik", "Ankara"),
        
        (vehicles[3][0], "Klima Arızası", "Klima gazı kaçağı, sistem kontrolü gerekli",
         (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
         (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
         "Kapali", "Bursa"),
    ]
    
    for f in faults:
        try:
            db.add_vehicle_fault(*f)
            print(f"  ✓ Added fault: {f[1]} for vehicle #{f[0]}")
        except Exception as e:
            print(f"  ✗ Error adding fault: {e}")

def main():
    print("=" * 60)
    print("MATRIX VEHICLE TEST DATA SEEDER")
    print("=" * 60)
    
    # Initialize database
    db.init_db()
    
    # Seed data
    seed_vehicles()
    seed_drivers()
    seed_faults()
    
    # Summary
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    
    with db.get_conn() as conn:
        cursor = conn.execute('SELECT COUNT(*) FROM vehicles')
        print(f"Total Vehicles: {cursor.fetchone()[0]}")
        
        cursor = conn.execute('SELECT COUNT(*) FROM drivers')
        print(f"Total Drivers: {cursor.fetchone()[0]}")
        
        cursor = conn.execute('SELECT COUNT(*) FROM vehicle_faults')
        print(f"Total Faults: {cursor.fetchone()[0]}")
    
    print("\n✓ Test data ready for Matrix-themed vehicle system!")

if __name__ == "__main__":
    main()
