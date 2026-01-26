"""
Test API endpoints for vehicles module
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n=== TESTING /health ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_login():
    """Test login and get session"""
    print("\n=== TESTING /login ===")
    try:
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/login",
            data={"username": "admin", "password": "748774"},
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Login successful!")
            return session
        else:
            print("Login failed!")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_vehicles_api(session):
    """Test /api/vehicles endpoint"""
    print("\n=== TESTING /api/vehicles ===")
    try:
        response = session.get(f"{BASE_URL}/api/vehicles", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Vehicle count: {len(data)}")
        if len(data) > 0:
            print(f"Sample vehicle: {json.dumps(data[0], indent=2)}")
        else:
            print("No vehicles in database")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_drivers_api(session):
    """Test /api/drivers endpoint"""
    print("\n=== TESTING /api/drivers ===")
    try:
        response = session.get(f"{BASE_URL}/api/drivers", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Driver count: {len(data)}")
        if len(data) > 0:
            print(f"Sample driver: {json.dumps(data[0], indent=2)}")
        else:
            print("No drivers in database")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_vehicle_faults_api(session):
    """Test /api/vehicle-faults endpoint"""
    print("\n=== TESTING /api/vehicle-faults ===")
    try:
        response = session.get(f"{BASE_URL}/api/vehicle-faults", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Fault count: {len(data)}")
        if len(data) > 0:
            print(f"Sample fault: {json.dumps(data[0], indent=2)}")
        else:
            print("No faults in database")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_vehicles_page(session):
    """Test /vehicles page"""
    print("\n=== TESTING /vehicles PAGE ===")
    try:
        response = session.get(f"{BASE_URL}/vehicles", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Page loaded successfully!")
            # Check if page contains expected elements
            html = response.text
            checks = [
                ("ARAÇ LİSTESİ" in html, "Title found"),
                ("vehicles-table" in html, "Table element found"),
                ("loadVehicles" in html, "JavaScript function found"),
                ("/api/vehicles" in html, "API endpoint referenced"),
            ]
            for check, desc in checks:
                print(f"  {'✓' if check else '✗'} {desc}")
            return response.status_code == 200
        else:
            print("Page load failed!")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("RAINSTAFF API TEST SUITE")
    print("=" * 60)
    
    # Test health
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Server is not running!")
        print("Please start the server with: cd puantaj_app/server && python app.py")
        return
    
    # Test login
    session = test_login()
    
    if not session:
        print("\n❌ Login failed!")
        return
    
    # Test API endpoints
    vehicles_ok = test_vehicles_api(session)
    drivers_ok = test_drivers_api(session)
    faults_ok = test_vehicle_faults_api(session)
    page_ok = test_vehicles_page(session)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Health Check:     {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"Login:            {'✓ PASS' if session else '✗ FAIL'}")
    print(f"Vehicles API:     {'✓ PASS' if vehicles_ok else '✗ FAIL'}")
    print(f"Drivers API:      {'✓ PASS' if drivers_ok else '✗ FAIL'}")
    print(f"Faults API:       {'✓ PASS' if faults_ok else '✗ FAIL'}")
    print(f"Vehicles Page:    {'✓ PASS' if page_ok else '✗ FAIL'}")
    print("=" * 60)
    
    all_pass = all([health_ok, session, vehicles_ok, drivers_ok, faults_ok, page_ok])
    if all_pass:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

if __name__ == "__main__":
    main()
