import os
import sys
import sqlite3
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session, abort
import staff_db as db

# Base directory for absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'server', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'server', 'static'))

app.secret_key = 'rainstaff_secure_key'

# Version Tag for Verification
VERSION = "staff-v3-final-verified"

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# --- UTILS ---

def calculate_dashboard_stats(timesheets, employees):
    """Calculate summary stats for the dashboard"""
    stats = {
        'overtime_hours': 0,
        'worked_hours': 0,
        'night_hours': 0,
        'special_hours': 0
    }
    
    overtime_by_employee = {} # employee_id -> hours
    emp_map = {e[0]: e[1] for e in employees} # id -> name
    
    for ts in timesheets:
        # ts format from staff_db.list_timesheets:
        # (id, emp_id, name, date, start, end, break, special, notes, region)
        try:
            start = datetime.strptime(ts[4], "%H:%M")
            end = datetime.strptime(ts[5], "%H:%M")
            if end < start:
                end += timedelta(days=1)
            
            worked = (end - start).total_seconds() / 3600 - (ts[6] / 60)
            stats['worked_hours'] += worked
            
            # Simple overtime calculation (> 9 hours)
            if worked > 9:
                ov = worked - 9
                stats['overtime_hours'] += ov
                emp_id = ts[1]
                overtime_by_employee[emp_id] = overtime_by_employee.get(emp_id, 0) + ov
                
            if ts[7]: # is_special
                stats['special_hours'] += worked
        except:
            continue
            
    # Find top overtime
    top_overtime = None
    if overtime_by_employee:
        top_emp_id = max(overtime_by_employee, key=overtime_by_employee.get)
        top_overtime = {
            'name': emp_map.get(top_emp_id, "Bilinmiyor"),
            'overtime': overtime_by_employee[top_emp_id]
        }
    
    # Round everything
    for k in stats:
        stats[k] = round(stats[k], 1)
        
    return stats, top_overtime

# --- ROUTES ---

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": VERSION,
        "database": "staff_db",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/diagnostic-final')
def diagnostic():
    try:
        conn = db.get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM employees")
        emp_count = cur.fetchone()[0]
        conn.close()
        return jsonify({
            "status": "ok",
            "db_connected": True,
            "employee_count": emp_count,
            "version": VERSION,
            "db_path": db.DB_PATH
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "version": VERSION}), 500

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.get_user(username)
        if user and db.verify_password(password, user['password_hash']):
            session['user_id'] = username
            session['user_role'] = user['role']
            session['user_region'] = user['region']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Geçersiz kullanıcı adı veya şifre')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        user = db.get_user(session['user_id'])
        employees = db.get_all_employees()
        timesheets = db.get_all_timesheets()
        
        # Calculate stats
        summary, top_overtime = calculate_dashboard_stats(timesheets, employees)
        
        # Safe defaults for dashboard template variables
        alert_counts = {'urgent': 0, 'bad': 0, 'repeat': 0, 'total': 0, 'good': 0}
        oil_counts = {'urgent': 0, 'warning': 0}
        open_faults = []
        quality_alerts = []
        monthly_summary = []
        daily_summary = []
        employee_cards = []
        overtime_leaders = []
        top_faults = []
        vehicle_cards = []
        driver_cards = []
        recent_inspections = []
        
        return render_template('dashboard.html', 
                             user=user,
                             employees=employees,
                             timesheets=timesheets,
                             summary=summary,
                             top_overtime=top_overtime,
                             alert_counts=alert_counts,
                             oil_counts=oil_counts,
                             open_faults=open_faults,
                             quality_alerts=quality_alerts,
                             monthly_summary=monthly_summary,
                             daily_summary=daily_summary,
                             employee_cards=employee_cards,
                             overtime_leaders=overtime_leaders,
                             top_faults=top_faults,
                             vehicle_cards=vehicle_cards,
                             driver_cards=driver_cards,
                             recent_inspections=recent_inspections,
                             last_sync=datetime.now().strftime("%H:%M:%S"),
                             desktop_online=True)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/sync', methods=['POST'])
def sync_upload():
    try:
        if 'db' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
        
        file = request.files['db']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        # Save incoming DB temporarily
        temp_path = os.path.join(db.DB_DIR, f"incoming_{datetime.now().timestamp()}.db")
        file.save(temp_path)
        
        # Merge using the logic in staff_db
        success, message = db.merge_databases(temp_path, db.DB_PATH)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/sync/download', methods=['GET'])
def sync_download():
    # In a real app, add auth here!
    if not os.path.exists(db.DB_PATH):
        return jsonify({'success': False, 'error': 'Master DB not found'}), 404
        
    return send_file(db.DB_PATH, as_attachment=True, download_name='puantaj.db')

# --- ADDITIONAL MODULE ROUTES ---

@app.route('/alerts')
def alerts():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('alerts.html', total_alerts=0)

@app.route('/reports')
def reports():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/stock')
def stock():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('stock.html')

@app.route('/vehicles')
def vehicles():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('vehicle.html', vehicles=[])

@app.route('/drivers')
def drivers():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('driver.html', drivers=[])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
