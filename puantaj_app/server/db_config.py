"""
Database Configuration - Supports both SQLite and PostgreSQL
"""
import os
from contextlib import contextmanager

# Check if we're on Render.com (has DATABASE_URL env var)
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    @contextmanager
    def get_conn():
        """PostgreSQL connection"""
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(query, params=None):
        """Execute a query and return results"""
        with get_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            try:
                return cursor.fetchall()
            except:
                return None
    
    def execute_update(query, params=None):
        """Execute an update/insert/delete query"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.rowcount

else:
    import sqlite3
    from contextlib import contextmanager
    
    # SQLite configuration
    APP_NAME = "Rainstaff"
    LOCAL_DB_DIR = os.path.join(os.path.dirname(__file__), "data")
    
    if os.name == 'nt':  # Windows
        APPDATA_DIR = os.path.join(os.environ.get("APPDATA", LOCAL_DB_DIR), APP_NAME, "data")
        DB_DIR = APPDATA_DIR
    else:
        DB_DIR = "/tmp/rainstaff_data"
    
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    
    DB_PATH = os.path.join(DB_DIR, "puantaj.db")
    
    @contextmanager
    def get_conn():
        """SQLite connection"""
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(query, params=None):
        """Execute a query and return results"""
        with get_conn() as conn:
            cursor = conn.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(query, params=None):
        """Execute an update/insert/delete query"""
        with get_conn() as conn:
            cursor = conn.execute(query, params or ())
            return cursor.rowcount

# Database type indicator
DB_TYPE = "PostgreSQL" if USE_POSTGRES else "SQLite"
