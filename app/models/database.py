"""
SQLAlchemy ORM models for database entities.

This module defines the database models using SQLAlchemy ORM
for better type safety and easier database operations.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Task(Base):
    """SQLAlchemy ORM model for tasks table."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, default="pending")
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    repo_url = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=True)
    github_token = Column(String, nullable=True)  # Added for assignment compliance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "repo_url": self.repo_url,
            "pr_number": self.pr_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
