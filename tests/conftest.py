"""
Test configuration and fixtures.

This module provides pytest configuration and common fixtures
for testing the AI Code Review Agent.
"""
import asyncio
import pytest
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import get_settings


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    This fixture creates an in-memory SQLite database for testing
    and provides a clean database session for each test.
    """
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    await engine.dispose()


@pytest.fixture
def test_client(test_db: AsyncSession) -> TestClient:
    """
    Create a test client with overridden dependencies.
    
    Args:
        test_db: Test database session
        
    Returns:
        TestClient: FastAPI test client
    """
    # Import dependencies
    from app.api.dependencies import get_async_session, get_github_service, get_llm_service
    
    # Create app without lifespan to avoid database initialization issues
    from fastapi import FastAPI
    from app.api.routes import analysis, status, results
    
    # Create minimal app for testing
    app = FastAPI(title="Test App")
    
    # Include routers
    app.include_router(analysis.router, prefix="", tags=["analysis"])
    app.include_router(status.router, prefix="", tags=["status"])
    app.include_router(results.router, prefix="", tags=["results"])
    
    # Add root endpoint for testing
    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {
            "message": "AI Code Review Agent is running",
            "version": "test",
            "status": "healthy"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "test"}
    
    # Override dependencies
    def override_get_db():
        return None
    
    def override_github_service():
        return MockGitHubService()
    
    def override_llm_service():
        return MockLLMService()
    
    app.dependency_overrides[get_async_session] = override_get_db
    app.dependency_overrides[get_github_service] = override_github_service
    app.dependency_overrides[get_llm_service] = override_llm_service
    
    # Create client without automatic lifespan management
    client = TestClient(app, base_url="http://testserver")
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pr_data() -> dict:
    """Sample PR data for testing."""
    return {
        "repo_url": "https://github.com/test/repository",
        "pr_number": 123,
        "analysis_type": "comprehensive",
        "focus_areas": ["security_vulnerabilities", "code_quality"]
    }


@pytest.fixture
def sample_github_pr_info() -> dict:
    """Sample GitHub PR information for testing."""
    return {
        "number": 123,
        "title": "Add new feature",
        "body": "This PR adds a new feature to the application",
        "state": "open",
        "author": "testuser",
        "created_at": "2025-01-27T10:00:00Z",
        "updated_at": "2025-01-27T10:30:00Z",
        "base_branch": "main",
        "head_branch": "feature/new-feature",
        "base_sha": "abc123",
        "head_sha": "def456",
        "commits": 3,
        "additions": 150,
        "deletions": 20,
        "changed_files": 5,
        "mergeable": True,
        "draft": False,
        "labels": ["enhancement"],
        "assignees": [],
        "reviewers": [],
        "html_url": "https://github.com/test/repository/pull/123"
    }


@pytest.fixture
def sample_analysis_result() -> dict:
    """Sample analysis result for testing."""
    return {
        "task_id": "test_task_123",
        "status": "completed",
        "repo_url": "https://github.com/test/repository",
        "pr_number": 123,
        "results": {
            "summary": "Analysis completed successfully",
            "findings": [
                {
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
            ],
            "metrics": {
                "files_analyzed": 5,
                "lines_of_code": 500,
                "execution_time_seconds": 30.5
            },
            "recommendations": [
                "Implement input validation for all user inputs",
                "Add error handling for database operations"
            ]
        },
        "error": None,
        "created_at": "2025-01-27T10:00:00Z",
        "completed_at": "2025-01-27T10:30:00Z",
        "progress": 100
    }


class MockGitHubService:
    """Mock GitHub service for testing."""
    
    async def check_pr_exists(self, repo_url: str, pr_number: int) -> bool:
        return True
    
    async def get_pull_request_info(self, repo_url: str, pr_number: int) -> dict:
        return {
            "number": pr_number,
            "title": "Test PR",
            "base_sha": "abc123",
            "head_sha": "def456",
            "additions": 100,
            "deletions": 10,
            "changed_files": 3
        }
    
    async def get_pull_request_files(self, repo_url: str, pr_number: int) -> list:
        return [
            {
                "filename": "test.py",
                "status": "modified",
                "is_text_file": True,
                "additions": 50,
                "deletions": 5
            }
        ]
    
    async def get_commit_diff(self, repo_url: str, base_sha: str, head_sha: str) -> str:
        return """
--- a/test.py
+++ b/test.py
@@ -1,3 +1,6 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+
+def goodbye():
+    print("Goodbye!")
"""


class MockLLMService:
    """Mock LLM service for testing."""
    
    async def analyze_file_content(
        self, 
        file_content: str, 
        file_path: str,
        programming_language: str,
        analysis_type: str = "comprehensive", 
        focus_areas: list = None
    ) -> dict:
        """Analyze file content."""
        return {
            "summary": f"Mock analysis completed for {file_path}",
            "findings": [
                {
                    "type": "quality",
                    "severity": "medium",
                    "title": "Mock finding",
                    "description": "This is a mock finding for testing",
                    "file_path": file_path,
                    "line_number": 1,
                    "suggestion": "This is a mock suggestion",
                    "confidence": 0.8
                }
            ]
        }
    
    async def analyze_code_diff(self, diff_content: str, analysis_type: str = "comprehensive", focus_areas: list = None) -> dict:
        """Analyze code diff."""
        return {
            "summary": "Mock analysis completed",
            "findings": [
                {
                    "type": "quality",
                    "severity": "medium",
                    "title": "Mock finding",
                    "description": "This is a mock finding for testing",
                    "file_path": "test.py",
                    "line_number": 1,
                    "suggestion": "This is a mock suggestion",
                    "confidence": 0.8
                }
            ]
        }
    
    async def generate_summary(self, all_findings: list, pr_info: dict) -> dict:
        """Generate analysis summary."""
        return {
            "summary": "Mock summary generated",
            "recommendations": ["Mock recommendation"],
            "quality_score": 8.5
        }
