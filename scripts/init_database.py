#!/usr/bin/env python3
"""
Database initialization and migration script for AI Code Review Agent.
This script creates all necessary database tables.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models.database import Task  # Import the model to register it
from app.core.config import get_settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


async def drop_tables():
    """Drop all database tables (use with caution)."""
    try:
        logger.info("Dropping database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


async def check_database_connection():
    """Check if we can connect to the database."""
    try:
        async with engine.begin() as conn:
            # Simple query to test connection
            result = await conn.execute("SELECT 1")
            logger.info("Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def main():
    """Main migration function."""
    logger.info("Starting database initialization...")
    settings = get_settings()
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Check database connection
    if not await check_database_connection():
        logger.error("Cannot connect to database. Please check your database settings.")
        sys.exit(1)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "drop":
            logger.warning("WARNING: This will drop all tables!")
            confirm = input("Are you sure? Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                await drop_tables()
            else:
                logger.info("Operation cancelled.")
        elif command == "recreate":
            logger.warning("WARNING: This will drop and recreate all tables!")
            confirm = input("Are you sure? Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                await drop_tables()
                await create_tables()
            else:
                logger.info("Operation cancelled.")
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: drop, recreate")
            sys.exit(1)
    else:
        # Default: create tables
        success = await create_tables()
        if success:
            logger.info("Database initialization completed successfully!")
        else:
            logger.error("Database initialization failed!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
