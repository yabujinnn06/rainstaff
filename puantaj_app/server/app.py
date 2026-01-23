"""
Rainstaff Web Dashboard & Sync Server
Flask application with auto-sync support
"""

import os
import sys
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import puantaj_db as db

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')


# Decorator to mark endpoints as public (exempt from auth)
def public_endpoint(f):
    f.is_public = True
    return f


# Define public endpoints BEFORE importing protected routes
@app.route('/health', methods=['GET'])
@public_endpoint
def health():
    """Health check endpoint (public, no auth)"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'ver': 'staff-v2'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/auto-sync', methods=['GET', 'HEAD', 'POST'])
@public_endpoint
def auto_sync():
    """
    Automatic sync trigger (for cron jobs / UptimeRobot)
    PUBLIC ENDPOINT - No authentication required
    """
    try:
        return jsonify({
            'success': True,
            'action': 'auto-sync',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/diagnostic-final')
@public_endpoint
def diagnostic_final():
    """Temporary debug endpoint to check auth logic"""
    try:
        username = request.args.get('u', 'admin')
        password = request.args.get('p', '748774')
        
        user = db.get_user(username)
        if not user:
            return jsonify({'status': 'user_not_found', 'username': username})
        
        computed = db.hash_password(password)
        stored = user['password_hash']
        
        return jsonify({
            'status': 'match' if computed == stored else 'mismatch',
            'username': username,
            'computed_hash': computed,
            'stored_hash': stored,
            'region': user['region'],
            'db_file': getattr(db, '__file__', 'unknown'),
            'ver': 'staff-v2'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'db_file': getattr(db, '__file__', 'unknown'),
            'ver': 'staff-v2'
        }), 500


# ============================================================================
# SYNC ENDPOINTS (Public - No Authentication Required)
# ============================================================================

@app.route('/sync/reset', methods=['POST'])
@public_endpoint
def sync_reset():
    """
    Reset server database - delete all data so fresh upload can happen.
    Use with caution! Requires secret key.
    """
    try:
        # Simple security - require a reset key
        reset_key = request.headers.get('X-Reset-Key', '')
        if reset_key != 'rainstaff2026reset':
            return jsonify({'error': 'Invalid reset key'}), 403
        
        db_path = db.DB_PATH
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Reinitialize empty database
        db.init_db()
        
        return jsonify({
            'success': True,
            'action': 'database_reset',
            'message': 'Server database has been reset',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sync', methods=['POST'])
@public_endpoint
def sync_upload():
    """
    Upload database file from desktop app with merge support.
    Respects deleted_records table to prevent deleted data from reappearing.
    """
    try:
        # Accept both 'db' and 'file' keys for backwards compatibility
        if 'db' in request.files:
            file = request.files['db']
        elif 'file' in request.files:
            file = request.files['file']
        else:
            return jsonify({'error': 'No file provided'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        db_path = db.DB_PATH
        print(f"DEBUG: Sync Upload Target Path: {db_path}") # Log to server console
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Save incoming DB to temp location
        temp_path = db_path + ".incoming"
        file.save(temp_path)
        print(f"DEBUG: Saved incoming file to {temp_path}, size: {os.path.getsize(temp_path)}")
        
        # If master DB doesn't exist, just use incoming as master
        if not os.path.exists(db_path):
            os.rename(temp_path, db_path)
            return jsonify({
                'success': True,
                'action': 'sync_upload_new',
                'timestamp': datetime.now().isoformat()
            }), 200

        # Ensure master DB schema is up to date (creates deleted_records if missing)
        db.init_db()
        
        # Merge incoming DB into master
        try:
            debug_logs = _merge_databases(temp_path, db_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'action': 'sync_upload_merged',
            'debug_logs': debug_logs,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _merge_databases(incoming_path, master_path):
    """
    Merge incoming database into master, respecting deletions.
    Returns a list of debug log strings.
    """
    logs = []
    incoming_conn = sqlite3.connect(incoming_path)
    master_conn = sqlite3.connect(master_path)
    
    try:
        # Ensure deleted_records table exists in both DBs
        for conn in [incoming_conn, master_conn]:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deleted_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    deleted_at TEXT NOT NULL,
                    deleted_by TEXT
                );
            """)
        master_conn.commit()
        
        # 1. Get deleted records from incoming
        deleted = set()
        try:
            cursor = incoming_conn.execute("SELECT table_name, record_id FROM deleted_records")
            rows = cursor.fetchall()
            logs.append(f"Incoming deleted_records count: {len(rows)}")
            for row in rows:
                deleted.add((row[0], row[1]))
                logs.append(f"Incoming deleted: {row[0]} #{row[1]}")
        except sqlite3.OperationalError:
            logs.append("No deleted_records table in incoming")
        
        # 2. Apply deletions to master and track them
        for table_name, record_id in deleted:
            # Delete from master
            master_conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            # Record deletion in master's deleted_records
            master_conn.execute(
                "INSERT OR IGNORE INTO deleted_records (table_name, record_id, deleted_at) VALUES (?, ?, ?)",
                (table_name, record_id, datetime.now().isoformat())
            )
            logs.append(f"Applied deletion to master: {table_name} #{record_id}")
        
        # 3. Get existing deleted records from master (to skip during merge)
        master_deleted = set()
        try:
            cursor = master_conn.execute("SELECT table_name, record_id FROM deleted_records")
            rows = cursor.fetchall()
            logs.append(f"Master deleted_records count: {len(rows)}")
            for row in rows:
                master_deleted.add((row[0], row[1]))
        except sqlite3.OperationalError:
            pass
        
        # Combine both deletion sets
        all_deleted = deleted | master_deleted
        
        # 4. Merge timesheets from incoming (skip deleted)
        try:
            cursor = incoming_conn.execute(
                "SELECT id, employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region FROM timesheets"
            )
            count = 0
            skipped = 0
            for row in cursor.fetchall():
                record_id = row[0]
                if ("timesheets", record_id) in all_deleted:
                    skipped += 1
                    continue  # Skip deleted record
                # Upsert: Insert or replace
                master_conn.execute(
                    "INSERT OR REPLACE INTO timesheets (id, employee_id, work_date, start_time, end_time, break_minutes, is_special, notes, region) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    row
                )
                count += 1
            logs.append(f"Merged timesheets: {count} inserted/updated, {skipped} skipped (deleted)")
        except sqlite3.OperationalError as e:
            logs.append(f"Error merging timesheets: {e}")
        
        # 5. Merge employees from incoming (skip deleted)
        try:
            cursor = incoming_conn.execute(
                "SELECT id, full_name, identity_no, department, title, region FROM employees"
            )
            count = 0
            skipped = 0
            for row in cursor.fetchall():
                record_id = row[0]
                if ("employees", record_id) in all_deleted:
                    skipped += 1
                    continue  # Skip deleted record
                master_conn.execute(
                    "INSERT OR REPLACE INTO employees (id, full_name, identity_no, department, title, region) VALUES (?, ?, ?, ?, ?, ?)",
                    row
                )
                count += 1
            logs.append(f"Merged employees: {count} inserted/updated, {skipped} skipped (deleted)")
        except sqlite3.OperationalError as e:
            logs.append(f"Error merging employees: {e}")
        
        master_conn.commit()
        return logs
    
    finally:
        incoming_conn.close()
        master_conn.close()


@app.route('/sync/download', methods=['GET'])
@public_endpoint
def sync_download():
    """
    Download current database from server
    Returns: SQLite DB file (binary)
    """
    try:
        db_path = db.DB_PATH
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        with open(db_path, 'rb') as f:
            db_content = f.read()
        
        return db_content, 200, {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename=puantaj.db'
        }
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# AUTHENTICATION CHECK (Protect Dashboard/Admin Routes)
# ============================================================================

@app.before_request
def check_auth():
    """Check authentication - explicitly whitelist public endpoints"""
    # Always allow static files
    if request.endpoint == 'static':
        return

    # Check if endpoint is exempt from auth
    if request.endpoint and request.endpoint in app.view_functions:
        view_func = app.view_functions[request.endpoint]
        if getattr(view_func, 'is_public', False):
            return

    # Hardcoded whitelist fallback (legacy support)
    public_endpoints = {'static', 'auto_sync', 'health', 'sync_upload', 'sync_download', 'login', 'index', 'debug_auth', 'sync_reset'}
    
    if request.endpoint in public_endpoints:
        return  # Public endpoint - no auth required
    
    # All other routes require authentication
    if request.endpoint and 'user_id' not in session:
        return redirect(url_for('login'))


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@public_endpoint
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        try:
            user = db.get_user(username)
            if user and db.verify_password(password, user['password_hash']):
                session['user_id'] = username
                session['user_role'] = user['role']
                session['user_region'] = user['region']
                return redirect(url_for('dashboard'))
        except Exception:
            pass
        
        return render_template('login.html', error='Invalid credentials')
    
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
        
        return render_template('modern_dashboard.html', 
                             user=user,
                             employees=employees,
                             timesheets=timesheets)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/api/employee-overtime')
def api_employee_overtime():
    """Get employees with overtime calculation"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Import calc module for overtime calculation
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            import calc
        except ImportError:
            # If calc module not available, return basic data
            employees = db.get_all_employees()
            result = []
            for emp in employees:
                result.append({
                    'id': emp[0],
                    'name': emp[1],
                    'department': emp[3] or '',
                    'title': emp[4] or '',
                    'region': emp[5] or '',
                    'overtime': 0.0
                })
            return jsonify(result), 200
        
        # Get settings for calculation
        settings = db.get_all_settings()
        
        # Calculate overtime for each employee
        employees = db.get_all_employees()
        result = []
        
        for emp in employees:
            emp_id = emp[0]
            timesheets = db.list_timesheets(employee_id=emp_id)
            
            total_overtime = 0.0
            for ts in timesheets:
                try:
                    work_date, start_time, end_time, break_minutes, is_special = ts[3], ts[4], ts[5], ts[6], ts[7]
                    
                    # Calculate overtime
                    _, _, overtime, _, _, _, _, _ = calc.calc_day_hours(
                        work_date, start_time, end_time, break_minutes, settings, is_special
                    )
                    total_overtime += overtime
                except Exception:
                    pass
            
            result.append({
                'id': emp[0],
                'name': emp[1],
                'department': emp[3] or '',
                'title': emp[4] or '',
                'region': emp[5] or '',
                'overtime': round(total_overtime, 2)
            })
        
        # Sort by overtime descending
        result.sort(key=lambda x: x['overtime'], reverse=True)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/alerts')
def alerts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        return render_template('alerts.html')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        return render_template('reports.html')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/stock')
def stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        return render_template('stock.html')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/api/employee-timesheets/<int:emp_id>')
def api_employee_timesheets(emp_id):
    """Get timesheet details for a specific employee with calculations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Import calc module
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            import calc
        except ImportError:
            # Return basic data without calculations
            timesheets = db.list_timesheets(employee_id=emp_id)
            result = []
            for ts in timesheets:
                result.append({
                    'work_date': ts[3],
                    'start_time': ts[4],
                    'end_time': ts[5],
                    'break_minutes': ts[6],
                    'worked_hours': 0.0,
                    'overtime': 0.0,
                    'night_hours': 0.0
                })
            return jsonify(result), 200
        
        # Get settings
        settings = db.get_all_settings()
        
        # Get timesheets
        timesheets = db.list_timesheets(employee_id=emp_id)
        result = []
        
        for ts in timesheets:
            try:
                work_date, start_time, end_time, break_minutes, is_special = ts[3], ts[4], ts[5], ts[6], ts[7]
                
                # Calculate hours
                worked, regular, overtime, night, overnight, special_day, special_night, special_overnight = calc.calc_day_hours(
                    work_date, start_time, end_time, break_minutes, settings, is_special
                )
                
                result.append({
                    'work_date': work_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'break_minutes': break_minutes,
                    'worked_hours': round(worked, 2),
                    'overtime': round(overtime, 2),
                    'night_hours': round(night + overnight, 2)
                })
            except Exception:
                result.append({
                    'work_date': ts[3],
                    'start_time': ts[4],
                    'end_time': ts[5],
                    'break_minutes': ts[6],
                    'worked_hours': 0.0,
                    'overtime': 0.0,
                    'night_hours': 0.0
                })
        
        # Sort by date descending
        result.sort(key=lambda x: x['work_date'], reverse=True)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock-data')
def api_stock_data():
    """Get stock inventory data grouped by stok_kod"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with db.get_conn() as conn:
            cursor = conn.cursor()
            
            # Get all stock records
            cursor.execute("""
                SELECT stok_kod, stok_adi, seri_no, durum, tarih, girdi_yapan, bolge, adet 
                FROM stock_inventory 
                ORDER BY stok_kod, seri_no
            """)
            rows = cursor.fetchall()
        
        # Group by stok_kod
        grouped = {}
        for row in rows:
            stok_kod, stok_adi, seri_no, durum, tarih, girdi_yapan, bolge, adet = row
            if stok_kod not in grouped:
                grouped[stok_kod] = {
                    'stok_adi': stok_adi,
                    'seri_list': []
                }
            grouped[stok_kod]['seri_list'].append({
                'seri_no': seri_no,
                'durum': durum,
                'tarih': tarih,
                'girdi_yapan': girdi_yapan,
                'bolge': bolge,
                'adet': adet
            })
        
        # Convert to list format
        data = []
        for stok_kod, info in grouped.items():
            data.append({
                'stok_kod': stok_kod,
                'stok_adi': info['stok_adi'],
                'seri_count': len(info['seri_list']),
                'seri_list': info['seri_list']
            })
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html', error=str(error)), 500


# Initialize database on module load (required for Gunicorn/Render)
try:
    db.init_db()
    print("Database initialized successfully on startup.")
except Exception as e:
    print(f"Error initializing database on startup: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
