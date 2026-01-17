"""
Rainstaff v2 - Main Application Entry Point
"""

import flet as ft
from loguru import logger
import sys

from shared.config import settings, ensure_directories
from backend.database import init_database
from frontend.app import RainstaffApp


def setup_logging():
    """Configure logging"""
    ensure_directories()
    
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")


def main(page: ft.Page):
    """Main entry point for Flet app"""
    # Initialize application
    app = RainstaffApp(page)
    app.initialize()


if __name__ == "__main__":
    # Setup
    setup_logging()
    
    # Initialize database
    try:
        init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Run Flet app
    logger.info("Starting Flet UI...")
    ft.run(
        main,
        name=settings.app_name,
        assets_dir="assets",
    )
