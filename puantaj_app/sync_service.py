#!/usr/bin/env python
r"""
Standalone Sync Service - 24/7 Background Synchronization
Runs independently of Desktop app, syncs every N minutes
Logs to: %APPDATA%\Rainstaff\logs\sync_service.log
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(db.DB_DIR), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "sync_service.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SYNC_INTERVAL_SECONDS = 180  # 3 minutes
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def load_sync_config():
    """Load sync settings from database."""
    try:
        settings = db.get_all_settings()
        return {
            'enabled': settings.get('sync_enabled', '0') == '1',
            'url': settings.get('sync_url', '').strip(),
            'token': settings.get('sync_token', '').strip(),
            'region': settings.get('admin_entry_region', 'Ankara'),
        }
    except Exception as e:
        logger.error(f"Failed to load sync config: {e}")
        return {'enabled': False, 'url': '', 'token': '', 'region': 'Ankara'}


def perform_sync(sync_url, token, region):
    """
    Execute sync: Upload local DB, download merged DB, backup & replace.
    Returns: (success: bool, message: str)
    """
    try:
        import requests
    except ImportError:
        return False, "requests library not installed"

    if not sync_url or not token:
        return False, "sync_url or sync_token not configured"

    try:
        # Step 1: Upload local DB to server
        with open(db.DB_PATH, "rb") as handle:
            files = {"db": ("puantaj.db", handle, "application/octet-stream")}
            headers = {
                "X-API-KEY": token,
                "X-Region": region,
                "X-Reason": "service_sync"
            }
            url = sync_url.rstrip("/") + "/sync"
            logger.info(f"Uploading DB to {url}...")
            resp = requests.post(url, headers=headers, files=files, timeout=10)

        if resp.status_code != 200:
            return False, f"Upload failed: HTTP {resp.status_code}"

        logger.info(f"Upload successful (HTTP {resp.status_code})")

        # Step 2: Download merged DB from server
        headers = {"X-API-KEY": token}
        download_url = sync_url.rstrip("/") + "/sync/download"
        logger.info(f"Downloading merged DB from {download_url}...")
        
        resp = requests.get(download_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return False, f"Download failed: HTTP {resp.status_code}"

        logger.info(f"Download successful (HTTP {resp.status_code})")

        # Step 3: Backup current local database
        import shutil
        backup_path = db.DB_PATH + ".service_backup"
        if os.path.isfile(db.DB_PATH):
            shutil.copy2(db.DB_PATH, backup_path)
            logger.info(f"Backup created: {backup_path}")

        # Step 4: Write downloaded database as new local DB
        with open(db.DB_PATH, "wb") as f:
            f.write(resp.content)
        
        logger.info(f"Local DB updated successfully")
        return True, "Sync completed"

    except requests.Timeout:
        return False, "Connection timeout"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)[:100]}"
    except Exception as e:
        logger.error(f"Unexpected sync error: {e}\n{traceback.format_exc()}")
        return False, f"Unexpected error: {str(e)[:100]}"


def sync_worker():
    """Main worker loop - runs continuously, syncs every N seconds."""
    logger.info("=" * 60)
    logger.info("Sync Service Started")
    logger.info("=" * 60)
    logger.info(f"DB Path: {db.DB_PATH}")
    logger.info(f"Log Path: {LOG_PATH}")
    logger.info(f"Sync Interval: {SYNC_INTERVAL_SECONDS} seconds")
    
    last_sync_time = 0
    consecutive_failures = 0

    while True:
        try:
            current_time = time.time()
            time_since_last_sync = current_time - last_sync_time

            # Check if it's time to sync
            if time_since_last_sync < SYNC_INTERVAL_SECONDS:
                sleep_time = SYNC_INTERVAL_SECONDS - time_since_last_sync
                time.sleep(min(sleep_time, 10))  # Check every 10 seconds max
                continue

            # Load fresh config
            config = load_sync_config()
            
            if not config['enabled']:
                logger.debug("Sync disabled in settings, skipping")
                time.sleep(30)
                continue

            logger.info(f"Starting sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            success, message = perform_sync(config['url'], config['token'], config['region'])
            
            if success:
                logger.info(f"✓ {message}")
                consecutive_failures = 0
                last_sync_time = current_time
            else:
                consecutive_failures += 1
                logger.warning(f"✗ {message} (attempt {consecutive_failures}/{MAX_RETRIES})")
                
                # Retry logic
                if consecutive_failures < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Sync failed {MAX_RETRIES} times, waiting for next cycle")
                    last_sync_time = current_time
                    consecutive_failures = 0

        except Exception as e:
            logger.error(f"Worker exception: {e}\n{traceback.format_exc()}")
            time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        sync_worker()
    except KeyboardInterrupt:
        logger.info("Sync service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
