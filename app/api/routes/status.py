from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.schemas import TaskStatusResponse, ErrorResponse
from app.services.task_manager import task_manager
from app.utils.helpers import validate_pr_number

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get Task Status",
    description="Retrieve the current status and progress of an analysis task."
)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskStatusResponse:
    logger.info("Task status requested", task_id=task_id)
    
    try:
        task_status = await task_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "task_not_found",
                    "message": f"Task {task_id} not found",
                    "task_id": task_id
                }
            )
        
        logger.info(
            "Task status retrieved",
            task_id=task_id,
            status=task_status.get("status"),
            progress=task_status.get("progress", 0)
        )
        
        return TaskStatusResponse(**task_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get task status",
            error=str(e),
            task_id=task_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "status_retrieval_failed",
                "message": "Failed to retrieve task status",
                "task_id": task_id
            }
        )


@router.get(
    "/results/{task_id}",
    summary="Get Analysis Results",
    description="Retrieve the analysis results for a completed task."
)
async def get_analysis_results(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Analysis results requested", task_id=task_id)
    
    try:
        results = await task_manager.get_task_results(task_id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "task_not_found",
                    "message": f"Task {task_id} not found",
                    "task_id": task_id
                }
            )
        
        if results.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "error": "task_not_completed",
                    "message": f"Task {task_id} is not completed yet",
                    "task_id": task_id,
                    "status": results.get("status", "unknown")
                }
            )
        
        logger.info("Analysis results retrieved", task_id=task_id)
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get analysis results",
            error=str(e),
            task_id=task_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "results_retrieval_failed",
                "message": "Failed to retrieve analysis results",
                "task_id": task_id
            }
        )


@router.get(
    "/tasks",
    response_model=List[TaskStatusResponse],
    summary="List Tasks",
    description="List analysis tasks, optionally filtered by repository and PR number."
)
async def list_tasks(
    repo_url: Optional[str] = Query(None, description="GitHub repository URL filter"),
    pr_number: Optional[int] = Query(None, description="Pull request number filter"),
    db: AsyncSession = Depends(get_db),
) -> List[TaskStatusResponse]:

    logger.info(
        "Task list requested",
        repo_url=repo_url,
        pr_number=pr_number
    )
    
    try:
        # Validate PR number if provided
        if pr_number is not None and not validate_pr_number(pr_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_pr_number",
                    "message": "PR number must be a positive integer",
                }
            )
        
        # Query database for tasks matching criteria
        tasks = await task_manager.list_tasks(repo_url=repo_url, pr_number=pr_number)
        
        logger.info(
            "Task list retrieved",
            count=len(tasks) if tasks else 0,
            repo_url=repo_url,
            pr_number=pr_number
        )
        
        return tasks or []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list tasks",
            error=str(e),
            repo_url=repo_url,
            pr_number=pr_number
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "task_list_failed",
                "message": "Failed to retrieve task list"
            }
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the analysis service."
)
async def health_check():
    try:
        # Check service health
        health_status = {
            "status": "healthy",
            "service": "AI Code Review Agent",
            "version": "1.0.0",
            "components": {
                "database": "connected",
                "task_queue": "operational",
                "llm_service": "available"
            }
        }
        
        logger.info("Health check performed", status="healthy")
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "health_check_failed",
                "message": "Service health check failed"
            }
        )
