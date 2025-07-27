"""
Task management service for tracking analysis progress.

This module provides a TaskManager class for handling task storage,
retrieval, and status updates using SQLAlchemy ORM.
"""
import json
from typing import Dict, Any, Optional, List

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None
    sessionmaker = None
    Session = None
    SQLAlchemyError = Exception

from app.core.config import get_settings
from app.models.database import Task


class TaskManager:
    """Manages task storage and retrieval using SQLAlchemy ORM."""
    
    def __init__(self):
        """Initialize task manager with database connection."""
        self.settings = get_settings()
        if SQLALCHEMY_AVAILABLE:
            self.engine = create_engine(self.settings.DATABASE_URL)
            self.SessionLocal = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.SessionLocal = None
            logger.warning("SQLAlchemy not available - task storage disabled")
    
    async def create_task(
        self, 
        task_id: str, 
        repo_url: str, 
        pr_number: Optional[int] = None,
        github_token: Optional[str] = None
    ) -> bool:
        """Create a new task record using ORM.
        
        Args:
            task_id: Unique identifier for the task
            repo_url: GitHub repository URL
            pr_number: Pull request number (optional)
            github_token: GitHub API token (optional)
            
        Returns:
            bool: True if task was created successfully
        """
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.warning("Database not available - task creation skipped")
            return False
            
        try:
            with self.SessionLocal() as session:
                # Check if task already exists
                existing_task = session.query(Task).filter(Task.id == task_id).first()
                if existing_task:
                    logger.info(f"Task {task_id} already exists")
                    return True
                
                # Create new task
                new_task = Task(
                    id=task_id,
                    status="pending",
                    progress=0,
                    repo_url=repo_url,
                    pr_number=pr_number,
                    github_token=github_token,
                    result=None
                )
                
                session.add(new_task)
                session.commit()
                logger.info(f"Created task {task_id} for repo {repo_url}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create task {task_id}: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status from database using ORM.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Dict containing task status information or None if not found
        """
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.warning("Database not available - cannot get task status")
            return None
            
        try:
            with self.SessionLocal() as session:
                task = session.query(Task).filter(Task.id == task_id).first()
                
                if task:
                    return {
                        'task_id': task.id,
                        'status': task.status,
                        'progress': task.progress,
                        'message': task.message,
                        'result': task.result,
                        'error': task.error,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                        'repo_url': task.repo_url,
                        'pr_number': task.pr_number
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return None
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        progress: int = None,
        message: str = None,
        result: Dict[str, Any] = None,
        error: str = None
    ) -> bool:
        """Update task status in database using ORM.
        
        Args:
            task_id: Unique task identifier
            status: New task status
            progress: Task progress percentage (0-100)
            message: Status message
            result: Analysis results (JSON)
            error: Error message if task failed
            
        Returns:
            bool: True if task was updated successfully
        """
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.warning("Database not available - cannot update task")
            return False
            
        try:
            with self.SessionLocal() as session:
                task = session.query(Task).filter(Task.id == task_id).first()
                
                if not task:
                    logger.warning(f"Task not found for update: {task_id}")
                    return False
                
                # Update task fields
                task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                
                session.commit()
                logger.info(f"Task updated: {task_id} -> {status}")
                return True
                    
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False
    
    async def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task results from database.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Dict containing task results or None if not found/completed
        """
        task_info = await self.get_task_status(task_id)
        
        if not task_info:
            return None
            
        if task_info['status'] != 'completed':
            return {
                'task_id': task_id,
                'status': task_info['status'],
                'message': f"Task is {task_info['status']} - results not available yet"
            }
            
        # Parse JSON result
        result = task_info.get('result')
        if result and isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON result for task {task_id}")
                result = {"error": "Failed to parse analysis results"}
        
        return {
            'task_id': task_id,
            'status': task_info['status'],
            'result': result or {},
            'repo_url': task_info.get('repo_url'),
            'pr_number': task_info.get('pr_number'),
            'completed_at': task_info.get('updated_at')
        }
    
    async def list_tasks(self, repo_url: str = None, pr_number: int = None) -> List[Dict[str, Any]]:
        """List tasks from database with optional filtering using ORM.
        
        Args:
            repo_url: Optional repository URL filter
            pr_number: Optional PR number filter
            
        Returns:
            List of task information dictionaries
        """
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.warning("Database not available - cannot list tasks")
            return []
            
        try:
            with self.SessionLocal() as session:
                query = session.query(Task)
                
                # Apply filters if provided
                if repo_url:
                    query = query.filter(Task.repo_url == repo_url)
                if pr_number:
                    query = query.filter(Task.pr_number == pr_number)
                
                # Order by created_at descending and limit to 100
                tasks = query.order_by(Task.created_at.desc()).limit(100).all()
                
                task_list = []
                for task in tasks:
                    task_list.append({
                        'task_id': task.id,
                        'status': task.status,
                        'progress': task.progress,
                        'message': task.message,
                        'repo_url': task.repo_url,
                        'pr_number': task.pr_number,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'updated_at': task.updated_at.isoformat() if task.updated_at else None
                    })
                
                logger.info(f"Listed {len(task_list)} tasks")
                return task_list
                
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
                
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []


# Global task manager instance
task_manager = TaskManager()
