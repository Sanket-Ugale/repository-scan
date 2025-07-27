"""
Results API routes for retrieving analysis results.

This module provides endpoints for retrieving completed analysis results
in the format specified by the assignment.
"""
from typing import Dict, Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.schemas import AssignmentResults, ErrorResponse
from app.services.task_manager import task_manager

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/results/{task_id}",
    response_model=AssignmentResults,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        400: {"model": ErrorResponse, "description": "Task not completed"},
    },
    summary="Get Analysis Results",
    description="Retrieve the results of a completed analysis task in assignment format."
)
async def get_results(
    task_id: str,
    db: AsyncSession = Depends(get_db)
) -> AssignmentResults:
    """
    Get analysis results for a completed task.
    
    This endpoint returns analysis results in the exact format specified
    by the assignment requirements.
    
    Args:
        task_id: The unique identifier of the analysis task
        db: Database session
        
    Returns:
        AssignmentResults: Task results in assignment format
        
    Raises:
        HTTPException: If task not found or not completed
    """
    try:
        # Get task status from database
        task_data = await task_manager.get_task_status(task_id)
        
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "task_not_found",
                    "message": f"Task {task_id} not found"
                }
            )
        
        # Check if task is completed
        if task_data['status'] != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "task_not_completed",
                    "message": f"Task {task_id} is not completed. Current status: {task_data['status']}",
                    "task_id": task_id,
                    "status": task_data['status']
                }
            )
        
        # Return results in assignment format
        return AssignmentResults(
            task_id=task_id,
            status=task_data['status'],
            results=task_data.get('result')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task results", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "retrieval_failed",
                "message": f"Failed to retrieve results: {str(e)}"
            }
        )
