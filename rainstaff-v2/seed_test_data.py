"""
Test verisi seed script
5 çalışan + 10 puantaj kaydı oluştur (Ankara, Bursa, Istanbul, Izmir)
"""

from datetime import datetime, timedelta, date
from backend.database import SessionLocal
from backend.models.employee import Employee
from backend.models.timesheet import Timesheet


def seed_test_data():
    """Create test employees and timesheets"""
    db = SessionLocal()
    
    try:
        # Clear existing test data
        db.query(Timesheet).delete()
        db.query(Employee).delete()
        
        # Create employees in different regions
        employees_data = [
            {
                "full_name": "Ahmet Yılmaz",
                "employee_no": "EMP001",
                "position": "Satış Danışmanı",
                "hire_date": date(2023, 1, 15),
                "region": "Ankara",
                "email": "ahmet@rainstaff.com",
                "phone": "+90 312 111 1111",
            },
            {
                "full_name": "Fatma Kaya",
                "employee_no": "EMP002",
                "position": "Muhasebeci",
                "hire_date": date(2022, 6, 1),
                "region": "Bursa",
                "email": "fatma@rainstaff.com",
                "phone": "+90 224 222 2222",
            },
            {
                "full_name": "Mehmet Demir",
                "employee_no": "EMP003",
                "position": "Pazarlama Müdürü",
                "hire_date": date(2021, 3, 10),
                "region": "Istanbul",
                "email": "mehmet@rainstaff.com",
                "phone": "+90 212 333 3333",
            },
            {
                "full_name": "Zeynep Güzel",
                "employee_no": "EMP004",
                "position": "İK Uzmanı",
                "hire_date": date(2023, 9, 1),
                "region": "Izmir",
                "email": "zeynep@rainstaff.com",
                "phone": "+90 232 444 4444",
            },
            {
                "full_name": "Ali Özdemir",
                "employee_no": "EMP005",
                "position": "Operasyon Müdürü",
                "hire_date": date(2020, 11, 20),
                "region": "Bursa",
                "email": "ali@rainstaff.com",
                "phone": "+90 224 555 5555",
            },
        ]
        
        employees = []
        for emp_data in employees_data:
            emp = Employee(**emp_data)
            db.add(emp)
            db.flush()
            employees.append(emp)
        
        db.commit()
        print(f"✓ {len(employees)} çalışan oluşturuldu")
        
        # Create timesheets for the last 10 days
        today = datetime.now().date()
        timesheets_data = []
        
        for i, emp in enumerate(employees):
            for day_offset in range(10):
                work_date = today - timedelta(days=day_offset)
                
                # Skip weekends for most employees
                if work_date.weekday() >= 5 and i < 4:  # 5=Sat, 6=Sun
                    continue
                
                # Varying work times
                if i % 2 == 0:
                    checkin = "08:00"
                    checkout = "17:00"
                else:
                    checkin = "09:00"
                    checkout = "18:00"
                
                # Some overtime on specific days
                if day_offset == 2 and i == 0:
                    checkout = "20:00"  # Overtime
                
                ts = Timesheet(
                    employee_id=emp.id,
                    work_date=work_date,
                    clock_in=checkin,
                    clock_out=checkout,
                    break_minutes=30 if i < 3 else 60,
                    region=emp.region,
                )
                db.add(ts)
                timesheets_data.append(ts)
        
        db.commit()
        print(f"✓ {len(timesheets_data)} puantaj kaydı oluşturuldu")
        
        # Print summary
        print("\n📊 Test Verisi Özeti:")
        for emp in employees:
            ts_count = db.query(Timesheet).filter(Timesheet.employee_id == emp.id).count()
            print(f"  • {emp.full_name} ({emp.region}) - {ts_count} gün puantaj")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
        db.close()
        return False


if __name__ == "__main__":
    print("🌱 Test verisi yükleniyor...")
    if seed_test_data():
        print("\n✅ Test verisi başarıyla yüklendi!")
    else:
        print("\n❌ Test verisi yüklenemedi")
