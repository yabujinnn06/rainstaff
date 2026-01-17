"""
Rainstaff v2 - Configuration Management
Centralized configuration with environment variable support
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings with validation"""
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / '.env'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Application
    app_name: str = "Rainstaff ERP"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/rainstaff.db"
    
    # Security
    secret_key: str = "rainstaff-default-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Cloud Sync
    cloud_sync_enabled: bool = False
    cloud_api_url: Optional[str] = None
    cloud_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/rainstaff.log"
    
    @property
    def database_path(self) -> Path:
        """Get database file path"""
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path("./data/rainstaff.db")


# Global settings instance
settings = Settings()


# Create necessary directories
def ensure_directories():
    """Create required directories if they don't exist"""
    directories = [
        settings.database_path.parent,
        Path(settings.log_file).parent,
        Path("./exports"),
        Path("./backups"),
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Regions (fixed list for now)
REGIONS = ["Ankara", "Izmir", "Bursa", "Istanbul", "ALL"]

# Weekday hours (default)
DEFAULT_WEEKDAY_HOURS = 9.0
DEFAULT_SATURDAY_START = "09:00"
DEFAULT_SATURDAY_END = "18:00"
