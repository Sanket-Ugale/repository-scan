#!/usr/bin/env python3
"""
Database migration script to add missing columns to tasks table.

This script adds the github_token column to the tasks table if it doesn't exist.
"""
import os
import sys
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import engine, SessionLocal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run database migrations."""
    logger.info("Starting database migration...")
    
    if not engine:
        logger.error("Failed to get database engine")
        return 1
    
    try:
        session = SessionLocal()
        try:
            # Check if github_token column exists
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tasks' AND column_name = 'github_token'
            """))
            
            if result.fetchone():
                logger.info("github_token column already exists")
            else:
                logger.info("Adding github_token column to tasks table...")
                session.execute(text("ALTER TABLE tasks ADD COLUMN github_token TEXT"))
                session.commit()
                logger.info("Successfully added github_token column")
                
            logger.info("Database migration completed successfully")
            return 0
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
