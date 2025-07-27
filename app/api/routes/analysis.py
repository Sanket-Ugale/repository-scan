from typing import Dict, List, Optional, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_github_service, get_llm_service
from app.models.schemas import (
    PRAnalysisRequest,
    AnalysisResponse,
    ErrorResponse
)
from app.services.github import GitHubService
from app.services.llm import LLMService
from app.services.task_manager import task_manager
from app.tasks.celery_tasks import analyze_pr_task
from app.utils.helpers import generate_task_id, validate_pr_number, sanitize_github_url

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/api/v1/analysis/analyze-pr",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze GitHub Pull Request",
    description="Submit a GitHub pull request for AI-powered code review analysis."
)
async def analyze_pr(
    request: PRAnalysisRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    github_service: GitHubService = Depends(get_github_service),
    llm_service: LLMService = Depends(get_llm_service)
) -> AnalysisResponse:

    try:
        # Validate PR number if provided
        if request.pr_number is not None and not validate_pr_number(request.pr_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_pr_number",
                    "message": "PR number must be a positive integer"
                }
            )
            
        # Validate and sanitize GitHub URL
        sanitized_url = sanitize_github_url(request.repo_url)
        if not sanitized_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_repo_url",
                    "message": "Invalid GitHub repository URL"
                }
            )
        
        # Generate unique task ID
        task_id = generate_task_id(sanitized_url, request.pr_number)
        
        # Determine analysis type based on whether PR number is provided
        analysis_type = "pull_request" if request.pr_number else "repository"
        
        logger.info(
            "Analysis submitted",
            task_id=task_id,
            repo_url=sanitized_url,
            pr_number=request.pr_number,
            analysis_type=analysis_type,
            has_token=bool(request.github_token)
        )
        
        # Create task in database with github_token
        await task_manager.create_task(
            task_id=task_id,
            repo_url=sanitized_url,
            pr_number=request.pr_number,
            github_token=request.github_token
        )
        
        # Queue analysis task
        analyze_pr_task.delay(
            task_id, 
            sanitized_url, 
            request.pr_number,
            request.github_token
        )
        
        return AnalysisResponse(
            task_id=task_id,
            status="queued",
            message=f"{analysis_type.replace('_', ' ').title()} analysis task queued successfully",
            repo_url=sanitized_url,
            pr_number=request.pr_number,
            estimated_completion_time=300
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit PR analysis", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "submission_failed",
                "message": f"Failed to submit analysis: {str(e)}"
            }
        )


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid webhook"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    }
)
async def github_webhook(
    payload: Dict[str, Any],
    github_service: GitHubService = Depends(get_github_service),
) -> Dict[str, str]:
    logger.info("GitHub webhook received", event_type=payload.get("action"))
    
    try:
        # Process webhook based on event type
        event_type = payload.get("action")
        
        if event_type in ["opened", "synchronize", "reopened"]:
            # PR was opened, updated, or reopened
            pr_data = payload.get("pull_request", {})
            repo_data = payload.get("repository", {})
            
            repo_url = repo_data.get("html_url")
            pr_number = pr_data.get("number")
            
            if repo_url and pr_number:
                # Optionally trigger automatic analysis
                logger.info(
                    "PR event detected",
                    repo_url=repo_url,
                    pr_number=pr_number,
                    event_type=event_type
                )
                
                # You could trigger analysis here if desired
                # analyze_pr_task.delay({
                #     "repo_url": repo_url,
                #     "pr_number": pr_number,
                #     "analysis_type": "automatic",
                #     "focus_areas": []
                # })
        
        return {"status": "webhook_processed", "event_type": event_type}
        
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), payload=payload)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "webhook_processing_failed",
                "message": "Failed to process webhook"
            }
        )
