"""
Rainstaff v2 - Sync Service
Handle multi-tenant synchronization with conflict resolution
Desktop client → Cloud API sync operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import requests
from loguru import logger

from backend.models.messaging import SyncLog
from backend.models.audit import AuditLog
from backend.models.employee import Employee
from backend.models.timesheet import Timesheet
from backend.models.vehicle import Vehicle
from backend.models.driver import Driver
from shared.auth import AuthContext
from shared.config import AppConfig


class CloudSyncClient:
    """HTTP client for cloud sync API"""
    
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.headers = {'X-API-Token': api_token, 'Content-Type': 'application/json'}
    
    def push_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """Push local changes to cloud"""
        try:
            response = requests.post(
                f"{self.api_url}/api/sync/push",
                headers=self.headers,
                json={'entities': entities},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Push failed: {e}")
            raise
    
    def pull_entities(self, entity_type: Optional[str] = None, since: Optional[str] = None) -> List[Dict]:
        """Pull updates from cloud"""
        try:
            params = {}
            if entity_type:
                params['entity_type'] = entity_type
            if since:
                params['since'] = since
            
            response = requests.get(
                f"{self.api_url}/api/sync/pull",
                headers=self.headers,
                params=params,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result.get('entities', [])
        except Exception as e:
            logger.error(f"Pull failed: {e}")
            raise
    
    def send_message(self, data: Dict) -> Dict[str, Any]:
        """Send cross-region message"""
        try:
            response = requests.post(
                f"{self.api_url}/api/messages/send",
                headers=self.headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Send message failed: {e}")
            raise
    
    def get_inbox(self, username: str) -> List[Dict]:
        """Get inbox messages"""
        try:
            response = requests.get(
                f"{self.api_url}/api/messages/inbox",
                headers=self.headers,
                params={'username': username},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return result.get('messages', [])
        except Exception as e:
            logger.error(f"Get inbox failed: {e}")
            raise
    
    def heartbeat(self, username: str, status: str = 'online', device_info: Optional[str] = None) -> Dict[str, Any]:
        """Send presence heartbeat"""
        try:
            response = requests.post(
                f"{self.api_url}/api/presence/heartbeat",
                headers=self.headers,
                json={
                    'username': username,
                    'status': status,
                    'device_info': device_info,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            raise
    
    def get_online_users(self) -> List[Dict]:
        """Get online users in region"""
        try:
            response = requests.get(
                f"{self.api_url}/api/presence/online",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return result.get('users', [])
        except Exception as e:
            logger.error(f"Get online users failed: {e}")
            raise


class SyncService:
    """Multi-tenant sync service with conflict resolution"""
    
    @staticmethod
    def detect_conflicts(
        db: Session,
        entity_type: str,
        entity_id: int,
        local_updated_at: str,
        remote_updated_at: str
    ) -> bool:
        """Check if there's a conflict between local and remote versions"""
        try:
            local_dt = datetime.fromisoformat(local_updated_at)
            remote_dt = datetime.fromisoformat(remote_updated_at)
            
            # Conflict if both modified after last sync and different
            return abs((local_dt - remote_dt).total_seconds()) > 1  # 1 second tolerance
        except Exception as e:
            logger.error(f"Conflict detection error: {e}")
            return False
    
    @staticmethod
    def resolve_conflict(
        auth: AuthContext,
        db: Session,
        entity_type: str,
        entity_id: int,
        local_data: Dict,
        remote_data: Dict,
        strategy: str = "newer_wins"
    ) -> Tuple[Dict, str]:
        """
        Resolve sync conflict
        
        Strategies:
        - newer_wins: Use the most recently updated version
        - local_wins: Always prefer local changes
        - remote_wins: Always prefer remote changes
        - manual: Store both, require manual resolution
        """
        
        if strategy == "newer_wins":
            local_updated = datetime.fromisoformat(local_data.get("updated_at", "1970-01-01"))
            remote_updated = datetime.fromisoformat(remote_data.get("updated_at", "1970-01-01"))
            
            winner_data = local_data if local_updated > remote_updated else remote_data
            resolution = "local_wins" if local_updated > remote_updated else "remote_wins"
            
        elif strategy == "local_wins":
            winner_data = local_data
            resolution = "local_wins"
            
        elif strategy == "remote_wins":
            winner_data = remote_data
            resolution = "remote_wins"
            
        else:  # manual
            winner_data = local_data  # Keep local until manual resolution
            resolution = "manual_required"
        
        # Log conflict
        sync_log = SyncLog(
            user_id=auth.user_id,
            username=auth.username,
            region=auth.region,
            sync_type="conflict",
            entity_type=entity_type,
            entity_id=entity_id,
            status="conflict",
            conflict_data=json.dumps({
                "local": local_data,
                "remote": remote_data,
                "strategy": strategy,
            }),
            resolution=resolution,
            completed_at=datetime.utcnow().isoformat(),
        )
        db.add(sync_log)
        
        logger.warning(
            f"Sync conflict resolved: {entity_type} ID={entity_id}, "
            f"strategy={strategy}, resolution={resolution}"
        )
        
        return winner_data, resolution
    
    @staticmethod
    def log_sync(
        auth: AuthContext,
        db: Session,
        sync_type: str,
        entity_type: str,
        status: str,
        records_affected: int = 0,
        entity_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log sync operation"""
        sync_log = SyncLog(
            user_id=auth.user_id,
            username=auth.username,
            region=auth.region,
            sync_type=sync_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            records_affected=records_affected,
            completed_at=datetime.utcnow().isoformat(),
        )
        
        if error:
            sync_log.conflict_data = json.dumps({"error": error})
        
        db.add(sync_log)
        logger.info(
            f"Sync logged: {sync_type} {entity_type}, status={status}, "
            f"records={records_affected}, region={auth.region}"
        )
    
    @staticmethod
    def get_sync_history(
        auth: AuthContext,
        db: Session,
        limit: int = 50
    ) -> List[SyncLog]:
        """Get sync history for current user/region"""
        query = db.query(SyncLog).filter(SyncLog.user_id == auth.user_id)
        
        if not auth.can_view_all_regions:
            query = query.filter(SyncLog.region == auth.region)
        
        return query.order_by(SyncLog.started_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_pending_conflicts(
        auth: AuthContext,
        db: Session
    ) -> List[SyncLog]:
        """Get unresolved conflicts for manual review"""
        query = db.query(SyncLog).filter(
            and_(
                SyncLog.status == "conflict",
                SyncLog.resolution == "manual_required"
            )
        )
        
        if not auth.can_view_all_regions:
            query = query.filter(SyncLog.region == auth.region)
        
        return query.order_by(SyncLog.started_at.desc()).all()
    
    @staticmethod
    def auto_sync_enabled(db: Session) -> bool:
        """Check if auto-sync is enabled in settings"""
        # TODO: Implement settings check
        return True
    
    @staticmethod
    def get_last_sync_time(auth: AuthContext, db: Session) -> Optional[datetime]:
        """Get last successful sync timestamp"""
        last_sync = db.query(SyncLog).filter(
            and_(
                SyncLog.region == auth.region,
                SyncLog.status == "success"
            )
        ).order_by(SyncLog.completed_at.desc()).first()
        
        if last_sync and last_sync.completed_at:
            return datetime.fromisoformat(last_sync.completed_at)
        return None
    
    @staticmethod
    def should_sync(auth: AuthContext, db: Session, interval_minutes: int = 5) -> bool:
        """Check if enough time passed since last sync"""
        if not SyncService.auto_sync_enabled(db):
            return False
        
        last_sync = SyncService.get_last_sync_time(auth, db)
        if not last_sync:
            return True
        
        next_sync = last_sync + timedelta(minutes=interval_minutes)
        return datetime.utcnow() >= next_sync
