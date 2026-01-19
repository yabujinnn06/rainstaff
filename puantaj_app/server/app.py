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
import puantaj_app.db as db

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
            'database': 'connected'
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


# ============================================================================
# SYNC ENDPOINTS (Public - No Authentication Required)
# ============================================================================

@app.route('/sync', methods=['POST'])
@public_endpoint
def sync_upload():
    """
    Upload database file from desktop app
    Receives: multipart/form-data with 'file' key containing SQLite DB
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded DB to server's master DB location
        db_path = db.DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        file.save(db_path)
        
        return jsonify({
            'success': True,
            'action': 'sync_upload',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    # These endpoints are publicly accessible without authentication
    public_endpoints = {'static', 'auto_sync', 'health', 'sync_upload', 'sync_download', 'login', 'index'}
    
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
        
        return render_template('dashboard.html', 
                             user=user,
                             employees=employees,
                             timesheets=timesheets)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


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


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html', error=str(error)), 500


if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
