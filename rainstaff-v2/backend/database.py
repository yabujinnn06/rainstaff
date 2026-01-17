"""
Rainstaff v2 - Database Connection
SQLAlchemy 2.0 database setup
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from shared.config import settings, ensure_directories
from loguru import logger


# Create base class for models
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite"""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager
    Automatically commits on success, rollbacks on error
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database schema"""
    ensure_directories()
    
    # Import all models to register them
    from backend.models import user, employee, timesheet, vehicle, driver, audit
    
    logger.info("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    logger.success("Database schema created successfully")
    
    # Create default super admin if no users exist
    from backend.services.user_service import UserService
    from shared.auth import AuthContext
    from shared.enums import UserRole
    
    with get_db() as db:
        user_count = db.query(user.User).count()
        if user_count == 0:
            logger.info("Creating default super admin...")
            # Create system context for initial setup
            system_auth = AuthContext(
                user_id=0,
                username="system",
                role=UserRole.SUPER_ADMIN,
                region="ALL"
            )
            
            UserService.create_user(
                auth=system_auth,
                db=db,
                username="admin",
                password="admin123",
                full_name="System Administrator",
                role=UserRole.SUPER_ADMIN,
                region="ALL",
                email="admin@rainstaff.local"
            )
            logger.success("Default admin created (username: admin, password: admin123)")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")


def reset_database():
    """Reset database (drop and recreate)"""
    drop_all_tables()
    init_database()
