"""
Rainstaff v2 - Cloud Sync Server API
Render free tier üzerinde çalışan Flask API
Multi-tenant senkronizasyon ve SSE real-time bildirimler
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps
from contextlib import contextmanager

from flask import Flask, request, jsonify, Response, stream_with_context
from werkzeug.security import generate_password_hash, check_password_hash
from loguru import logger
import queue
import time

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max upload

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'rainstaff_cloud.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# SSE message queues (per region)
sse_queues: Dict[str, List[queue.Queue]] = {
    'Ankara': [],
    'Izmir': [],
    'Bursa': [],
    'Istanbul': [],
    'ALL': [],
}


# ============================================================================
# Database Context Manager
# ============================================================================

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


# ============================================================================
# Database Schema
# ============================================================================

def init_database():
    """Initialize cloud database schema"""
    logger.info("Initializing cloud database...")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # API tokens (per region)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                region TEXT NOT NULL,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP
            )
        """)
        
        # Sync history (track all sync operations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                sync_type TEXT NOT NULL,
                records_affected INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                sync_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sync_completed_at TIMESTAMP
            )
        """)
        
        # Entity snapshots (store latest data from each region)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region, entity_type, entity_id)
            )
        """)
        
        # Messages (cross-region messaging)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_region TEXT NOT NULL,
                sender_username TEXT NOT NULL,
                receiver_region TEXT,
                receiver_username TEXT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                is_read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Presence (online status)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                username TEXT NOT NULL,
                status TEXT DEFAULT 'online',
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_info TEXT,
                UNIQUE(region, username)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_region, receiver_username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presence_activity ON presence(last_activity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_lookup ON entity_snapshots(region, entity_type, entity_id)")
        
        conn.commit()
        logger.info("Database initialized successfully")


# ============================================================================
# Authentication
# ============================================================================

def require_api_token(f):
    """Decorator to require valid API token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token:
            return jsonify({'error': 'API token required'}), 401
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT region, name, is_active FROM api_tokens WHERE token = ?",
                (token,)
            )
            row = cursor.fetchone()
            
            if not row or not row['is_active']:
                return jsonify({'error': 'Invalid or inactive token'}), 401
            
            # Update last used
            cursor.execute(
                "UPDATE api_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE token = ?",
                (token,)
            )
            conn.commit()
            
            # Pass region to handler
            request.region = row['region']
            request.token_name = row['name']
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# SSE Helpers
# ============================================================================

def broadcast_sse(region: str, event_type: str, data: Dict[str, Any]):
    """Broadcast SSE message to all clients in region"""
    logger.debug(f"Broadcasting SSE to {region}: {event_type}")
    
    message = {
        'type': event_type,
        'data': data,
        'timestamp': datetime.now().isoformat(),
    }
    
    # Send to specific region
    for q in sse_queues.get(region, []):
        try:
            q.put_nowait(message)
        except queue.Full:
            logger.warning(f"Queue full for region {region}")
    
    # Also send to ALL subscribers (admins)
    for q in sse_queues.get('ALL', []):
        try:
            q.put_nowait(message)
        except queue.Full:
            pass


# ============================================================================
# API Routes
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (for Render keep-alive)"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if DB_PATH.exists() else 'missing',
    })


@app.route('/api/sync/push', methods=['POST'])
@require_api_token
def sync_push():
    """
    Receive data from desktop client and merge into cloud database
    
    Request body:
    {
        "entities": [
            {"type": "employee", "id": 1, "data": {...}, "updated_at": "2026-01-10T12:00:00"},
            {"type": "timesheet", "id": 5, "data": {...}, "updated_at": "2026-01-10T12:05:00"},
        ]
    }
    """
    region = request.region
    data = request.get_json()
    
    if not data or 'entities' not in data:
        return jsonify({'error': 'Missing entities in request'}), 400
    
    entities = data['entities']
    logger.info(f"Sync push from {region}: {len(entities)} entities")
    
    conflicts = []
    merged = 0
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for entity in entities:
            entity_type = entity['type']
            entity_id = entity['id']
            entity_data = entity['data']
            updated_at = entity['updated_at']
            
            # Check for conflicts (existing version is newer)
            cursor.execute("""
                SELECT version, updated_at, data 
                FROM entity_snapshots 
                WHERE region = ? AND entity_type = ? AND entity_id = ?
            """, (region, entity_type, entity_id))
            
            existing = cursor.fetchone()
            
            if existing:
                existing_time = datetime.fromisoformat(existing['updated_at'])
                incoming_time = datetime.fromisoformat(updated_at)
                
                # Conflict: server version is newer
                if existing_time > incoming_time + timedelta(seconds=1):
                    conflicts.append({
                        'type': entity_type,
                        'id': entity_id,
                        'local_updated': updated_at,
                        'remote_updated': existing['updated_at'],
                        'remote_data': json.loads(existing['data']),
                    })
                    continue
            
            # Merge: upsert entity snapshot
            cursor.execute("""
                INSERT INTO entity_snapshots (region, entity_type, entity_id, data, version, updated_at)
                VALUES (?, ?, ?, ?, 1, ?)
                ON CONFLICT(region, entity_type, entity_id) DO UPDATE SET
                    data = excluded.data,
                    version = version + 1,
                    updated_at = excluded.updated_at
            """, (region, entity_type, entity_id, json.dumps(entity_data), updated_at))
            
            merged += 1
        
        # Log sync
        cursor.execute("""
            INSERT INTO sync_history (region, sync_type, records_affected, status)
            VALUES (?, 'push', ?, ?)
        """, (region, merged, 'success' if not conflicts else 'partial'))
        
        conn.commit()
    
    # Broadcast update notification
    if merged > 0:
        broadcast_sse(region, 'data_updated', {
            'count': merged,
            'source_region': region,
        })
    
    return jsonify({
        'status': 'success',
        'merged': merged,
        'conflicts': conflicts,
        'total': len(entities),
    })


@app.route('/api/sync/pull', methods=['GET'])
@require_api_token
def sync_pull():
    """
    Send latest data to desktop client
    
    Query params:
    - entity_type: employee, timesheet, vehicle, driver (optional, all if not specified)
    - since: ISO timestamp (optional, all if not specified)
    """
    region = request.region
    entity_type = request.args.get('entity_type')
    since = request.args.get('since')
    
    logger.info(f"Sync pull from {region}: type={entity_type}, since={since}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT entity_type, entity_id, data, version, updated_at FROM entity_snapshots WHERE region = ?"
        params = [region]
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if since:
            query += " AND updated_at > ?"
            params.append(since)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        entities = [
            {
                'type': row['entity_type'],
                'id': row['entity_id'],
                'data': json.loads(row['data']),
                'version': row['version'],
                'updated_at': row['updated_at'],
            }
            for row in rows
        ]
    
    return jsonify({
        'status': 'success',
        'entities': entities,
        'count': len(entities),
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/messages/send', methods=['POST'])
@require_api_token
def send_message():
    """Send message (cross-region or broadcast)"""
    region = request.region
    data = request.get_json()
    
    required = ['sender_username', 'subject', 'body']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (
                sender_region, sender_username, receiver_region, receiver_username,
                subject, body, priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            region,
            data['sender_username'],
            data.get('receiver_region'),
            data.get('receiver_username'),
            data['subject'],
            data['body'],
            data.get('priority', 'normal'),
        ))
        message_id = cursor.lastrowid
        conn.commit()
    
    # Broadcast notification
    target_region = data.get('receiver_region', 'ALL')
    broadcast_sse(target_region, 'new_message', {
        'id': message_id,
        'from': f"{data['sender_username']} ({region})",
        'subject': data['subject'],
        'priority': data.get('priority', 'normal'),
    })
    
    return jsonify({'status': 'success', 'message_id': message_id})


@app.route('/api/messages/inbox', methods=['GET'])
@require_api_token
def get_inbox():
    """Get messages for current region/user"""
    region = request.region
    username = request.args.get('username')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, sender_region, sender_username, subject, body, priority, 
                   is_read, read_at, created_at
            FROM messages
            WHERE (receiver_region = ? AND receiver_username = ?)
               OR (receiver_region IS NULL AND receiver_username IS NULL)
            ORDER BY created_at DESC
            LIMIT 100
        """, (region, username))
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
    
    return jsonify({'status': 'success', 'messages': messages})


@app.route('/api/presence/heartbeat', methods=['POST'])
@require_api_token
def presence_heartbeat():
    """Update user presence"""
    region = request.region
    data = request.get_json()
    
    username = data.get('username')
    status = data.get('status', 'online')
    device_info = data.get('device_info')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO presence (region, username, status, device_info)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(region, username) DO UPDATE SET
                status = excluded.status,
                last_activity = CURRENT_TIMESTAMP,
                device_info = excluded.device_info
        """, (region, username, status, device_info))
        conn.commit()
    
    # Broadcast presence update
    broadcast_sse(region, 'presence_update', {
        'username': username,
        'status': status,
    })
    
    return jsonify({'status': 'success'})


@app.route('/api/presence/online', methods=['GET'])
@require_api_token
def get_online_users():
    """Get online users"""
    region = request.region
    
    cutoff = datetime.now() - timedelta(minutes=5)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, status, last_activity, device_info
            FROM presence
            WHERE region = ? AND last_activity > ?
            ORDER BY last_activity DESC
        """, (region, cutoff.isoformat()))
        
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
    
    return jsonify({'status': 'success', 'users': users})


@app.route('/api/events', methods=['GET'])
@require_api_token
def sse_stream():
    """Server-Sent Events stream for real-time updates"""
    region = request.region
    
    logger.info(f"SSE client connected: {region}")
    
    # Create queue for this client
    q = queue.Queue(maxsize=20)
    sse_queues[region].append(q)
    
    def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'region': region})}\n\n"
            
            # Send heartbeat every 30 seconds
            last_heartbeat = time.time()
            
            while True:
                try:
                    # Non-blocking get with timeout
                    message = q.get(timeout=1)
                    yield f"data: {json.dumps(message)}\n\n"
                except queue.Empty:
                    # Send heartbeat if needed
                    if time.time() - last_heartbeat > 30:
                        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                        last_heartbeat = time.time()
        finally:
            # Cleanup on disconnect
            logger.info(f"SSE client disconnected: {region}")
            if q in sse_queues[region]:
                sse_queues[region].remove(q)
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


# ============================================================================
# Admin Routes (Token Management)
# ============================================================================

@app.route('/admin/tokens/create', methods=['POST'])
def create_token():
    """Create new API token (protected by admin password)"""
    data = request.get_json()
    
    admin_password = data.get('admin_password')
    if admin_password != os.getenv('ADMIN_PASSWORD', 'change-me-in-production'):
        return jsonify({'error': 'Invalid admin password'}), 403
    
    region = data.get('region')
    name = data.get('name')
    
    if not region or not name:
        return jsonify({'error': 'Region and name required'}), 400
    
    # Generate token (simple UUID for now)
    import uuid
    token = str(uuid.uuid4())
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_tokens (token, region, name)
            VALUES (?, ?, ?)
        """, (token, region, name))
        conn.commit()
    
    return jsonify({'status': 'success', 'token': token, 'region': region, 'name': name})


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    # Setup logging
    logger.add(
        'logs/server.log',
        rotation='1 day',
        retention='30 days',
        level='INFO',
    )
    
    # Initialize database
    init_database()
    
    # Run server
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Rainstaff Cloud API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
