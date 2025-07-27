"""
Pydantic schemas for request/response validation.

This module defines all Pydantic models used for API request
and response validation in the AI Code Review Agent.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


class AnalysisType(str, Enum):
    """Enumeration of analysis types."""
    COMPREHENSIVE = "comprehensive"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"


class TaskStatusEnum(str, Enum):
    """Enumeration of task statuses."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FocusArea(str, Enum):
    """Enumeration of analysis focus areas."""
    SECURITY_VULNERABILITIES = "security_vulnerabilities"
    PERFORMANCE_ISSUES = "performance_issues"
    CODE_SMELLS = "code_smells"
    BEST_PRACTICES = "best_practices"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ERROR_HANDLING = "error_handling"
    MAINTAINABILITY = "maintainability"


class PRAnalysisRequest(BaseModel):
    """
    Request model for PR analysis according to assignment requirements.
    
    Attributes:
        repo_url: GitHub repository URL
        pr_number: Pull request number (optional - if not provided, scan entire repo)
        github_token: Optional GitHub token for private repos
        analysis_type: Type of analysis to perform
        focus_areas: Specific areas to focus on during analysis
    """
    repo_url: str = Field(
        ...,
        description="GitHub repository URL",
        example="https://github.com/user/repo"
    )
    pr_number: Optional[int] = Field(
        None,
        gt=0,
        description="Pull request number (optional - scan entire repo if not provided)",
        example=123
    )
    github_token: Optional[str] = Field(
        None,
        description="Optional GitHub token for private repositories"
    )
    analysis_type: Optional[AnalysisType] = Field(
        AnalysisType.COMPREHENSIVE,
        description="Type of analysis to perform"
    )
    focus_areas: Optional[List[FocusArea]] = Field(
        default_factory=list,
        description="Specific areas to focus on during analysis"
    )
    
    @validator("repo_url")
    def validate_repo_url(cls, v: str) -> str:
        """Validate GitHub repository URL format."""
        if not v.startswith(("https://github.com/", "git@github.com:")):
            raise ValueError("Must be a valid GitHub repository URL")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/user/repo",
                "pr_number": 123,
                "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",
                "analysis_type": "comprehensive",
                "focus_areas": ["security_vulnerabilities", "code_smells"]
            }
        }


class AnalysisResponse(BaseModel):
    """
    Response model for analysis request.
    
    Attributes:
        task_id: Unique task identifier
        status: Current task status
        message: Human-readable status message
        repo_url: GitHub repository URL
        pr_number: Pull request number
        created_at: Task creation timestamp
    """
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatusEnum = Field(..., description="Current task status")
    message: str = Field(..., description="Human-readable status message")
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: Optional[int] = Field(None, description="Pull request number (optional)")
    estimated_completion_time: Optional[int] = Field(
        None, 
        description="Estimated completion time in seconds"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "status": "queued",
                "message": "Analysis task started successfully",
                "repo_url": "https://github.com/owner/repository",
                "pr_number": 123,
                "estimated_completion_time": 300,
                "created_at": "2025-01-27T10:30:00Z"
            }
        }


class Finding(BaseModel):
    """
    Individual analysis finding.
    
    Attributes:
        type: Type of finding (e.g., security, performance)
        severity: Severity level (critical, high, medium, low)
        title: Brief title of the finding
        description: Detailed description
        file_path: Path to the affected file
        line_number: Line number where issue occurs
        code_snippet: Relevant code snippet
        suggestion: Suggested fix or improvement
        confidence: Confidence level of the finding (0.0-1.0)
    """
    type: str = Field(..., description="Type of finding")
    severity: str = Field(
        ...,
        description="Severity level",
        pattern="^(critical|high|medium|low)$"
    )
    title: str = Field(..., description="Brief title of the finding")
    description: str = Field(..., description="Detailed description")
    file_path: str = Field(..., description="Path to the affected file")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level of the finding"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "security",
                "severity": "high",
                "title": "SQL Injection Vulnerability",
                "description": "User input is directly concatenated into SQL query",
                "file_path": "src/database.py",
                "line_number": 42,
                "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
                "suggestion": "Use parameterized queries to prevent SQL injection",
                "confidence": 0.95
            }
        }


class AnalysisResults(BaseModel):
    """
    Complete analysis results.
    
    Attributes:
        summary: High-level summary of the analysis
        findings: List of individual findings
        metrics: Analysis metrics (lines analyzed, files processed, etc.)
        recommendations: Overall recommendations
    """
    summary: str = Field(..., description="High-level summary of the analysis")
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of individual findings"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis metrics"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Overall recommendations"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "summary": "Analysis completed successfully. Found 3 security issues and 2 performance concerns.",
                "findings": [],
                "metrics": {
                    "files_analyzed": 15,
                    "lines_of_code": 1250,
                    "execution_time_seconds": 45.2
                },
                "recommendations": [
                    "Implement input validation for all user inputs",
                    "Add error handling for database operations"
                ]
            }
        }


class AnalysisResult(BaseModel):
    """
    Complete analysis result with task information.
    
    Attributes:
        task_id: Unique task identifier
        status: Current task status
        repo_url: GitHub repository URL
        pr_number: Pull request number
        results: Analysis results (only if completed)
        error: Error message (only if failed)
        created_at: Task creation timestamp
        completed_at: Task completion timestamp
        progress: Task progress percentage (0-100)
    """
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatusEnum = Field(..., description="Current task status")
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull request number")
    results: Optional[AnalysisResults] = Field(
        None,
        description="Analysis results (only if completed)"
    )
    error: Optional[str] = Field(None, description="Error message (only if failed)")
    created_at: datetime = Field(..., description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(
        None,
        description="Task completion timestamp"
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Task progress percentage"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "status": "completed",
                "repo_url": "https://github.com/owner/repository",
                "pr_number": 123,
                "results": {
                    "summary": "Analysis completed successfully",
                    "findings": [],
                    "metrics": {},
                    "recommendations": []
                },
                "error": None,
                "created_at": "2025-01-27T10:30:00Z",
                "completed_at": "2025-01-27T10:35:00Z",
                "progress": 100
            }
        }


class TaskStatus(BaseModel):
    """
    Basic task status information.
    
    Attributes:
        task_id: Unique task identifier
        status: Current task status
        repo_url: GitHub repository URL
        pr_number: Pull request number
        created_at: Task creation timestamp
        progress: Task progress percentage
    """
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatusEnum = Field(..., description="Current task status")
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull request number")
    created_at: datetime = Field(..., description="Task creation timestamp")
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Task progress percentage"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "status": "running",
                "repo_url": "https://github.com/owner/repository",
                "pr_number": 123,
                "created_at": "2025-01-27T10:30:00Z",
                "progress": 65
            }
        }


class TaskStatusResponse(BaseModel):
    """Response model for task status information."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current task status")
    progress: int = Field(default=0, description="Task progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    repo_url: Optional[str] = Field(None, description="Repository URL")
    pr_number: Optional[int] = Field(None, description="Pull request number")


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Attributes:
        error: Error code
        message: Human-readable error message
        task_id: Associated task ID (if applicable)
        details: Additional error details
    """
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "invalid_request",
                "message": "The request could not be processed",
                "task_id": "abc123def456",
                "details": {"field": "validation error details"}
            }
        }


# Assignment-compliant schemas
class FileIssue(BaseModel):
    """Individual issue in a file according to assignment format."""
    type: str = Field(..., description="Type of issue (style, bug, performance, etc.)")
    line: Optional[int] = Field(None, description="Line number where issue occurs")
    description: str = Field(..., description="Description of the issue")
    suggestion: str = Field(..., description="Suggested fix for the issue")


class FileAnalysis(BaseModel):
    """Analysis results for a single file according to assignment format."""
    name: str = Field(..., description="File name")
    issues: List[FileIssue] = Field(default_factory=list, description="List of issues found in the file")


class AnalysisSummary(BaseModel):
    """Summary statistics according to assignment format."""
    total_files: int = Field(..., description="Total number of files analyzed")
    total_issues: int = Field(..., description="Total number of issues found")
    critical_issues: int = Field(..., description="Number of critical issues found")


class AssignmentResults(BaseModel):
    """Results format exactly matching the assignment specification."""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status")
    results: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": "abc123",
                "status": "completed",
                "results": {
                    "files": [
                        {
                            "name": "main.py",
                            "issues": [
                                {
                                    "type": "style",
                                    "line": 15,
                                    "description": "Line too long",
                                    "suggestion": "Break line into multiple lines"
                                },
                                {
                                    "type": "bug",
                                    "line": 23,
                                    "description": "Potential null pointer",
                                    "suggestion": "Add null check"
                                }
                            ]
                        }
                    ],
                    "summary": {
                        "total_files": 1,
                        "total_issues": 2,
                        "critical_issues": 1
                    }
                }
            }
        }
