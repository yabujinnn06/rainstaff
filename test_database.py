import sys
sys.path.insert(0, 'puantaj_app')
import puantaj_db as db

# Initialize database
db.init_db()
print('Database initialized')

# Get connection
with db.get_conn() as conn:
    # List all tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    
    print('\n=== DATABASE TABLES ===')
    for t in tables:
        print(f'  - {t}')
    
    # Count records
    print('\n=== RECORD COUNTS ===')
    
    cursor = conn.execute('SELECT COUNT(*) FROM vehicles')
    print(f'Vehicles: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM drivers')
    print(f'Drivers: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM vehicle_faults')
    print(f'Vehicle Faults: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM vehicle_inspections')
    print(f'Vehicle Inspections: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM vehicle_service_visits')
    print(f'Service Visits: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM employees')
    print(f'Employees: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM timesheets')
    print(f'Timesheets: {cursor.fetchone()[0]}')
    
    cursor = conn.execute('SELECT COUNT(*) FROM stock_inventory')
    print(f'Stock Items: {cursor.fetchone()[0]}')
    
    # Check if notification tables exist
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%notification%';")
    notif_tables = cursor.fetchall()
    
    print('\n=== NOTIFICATION TABLES ===')
    if notif_tables:
        for t in notif_tables:
            print(f'  - {t[0]}')
    else:
        print('  (none - need to create)')
    
    # Sample vehicle data
    print('\n=== SAMPLE VEHICLES ===')
    cursor = conn.execute('SELECT plate, brand, model, km, region FROM vehicles LIMIT 5')
    vehicles = cursor.fetchall()
    if vehicles:
        for v in vehicles:
            print(f'  {v[0]} - {v[1]} {v[2]} ({v[3]} km) - {v[4]}')
    else:
        print('  (no vehicles in database)')
    
    # Check vehicle columns
    print('\n=== VEHICLE TABLE SCHEMA ===')
    cursor = conn.execute('PRAGMA table_info(vehicles)')
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

print('\n=== TEST COMPLETE ===')
