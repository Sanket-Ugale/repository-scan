from typing import AsyncGenerator, Optional

# Optional import for structlog
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Depends = None
    HTTPException = None
    status = None
    HTTPBearer = None
    HTTPAuthorizationCredentials = None

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None

from app.core.database import get_async_session
from app.core.security import verify_token
from app.services.github import GitHubService
from app.services.llm import LLMService

# Security scheme
if FASTAPI_AVAILABLE:
    security = HTTPBearer(auto_error=False)
else:
    security = None


async def get_db():
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.warning("Database session unavailable - SQLAlchemy not installed")
        yield None
        return
        
    try:
        async for session in get_async_session():
            yield session
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise


async def get_current_user(credentials=None) -> Optional[str]:
    if not FASTAPI_AVAILABLE:
        logger.warning("Authentication unavailable - FastAPI not installed")
        return None
        
    if not credentials:
        return None
    
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_github_service() -> GitHubService:
    return GitHubService()


async def get_llm_service() -> LLMService:
    return LLMService()


def require_auth(user_id: Optional[str] = None) -> str:
    if not FASTAPI_AVAILABLE:
        logger.warning("Authentication unavailable - FastAPI not installed")
        return ""
        
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id
