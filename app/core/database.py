import asyncio
from typing import AsyncGenerator

import structlog
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.database import Base, Task

logger = structlog.get_logger(__name__)

# Database engines and session makers
engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None


def init_db() -> None:
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    settings = get_settings()
    
    # Create synchronous engine for Alembic migrations
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )
    
    # Create asynchronous engine for FastAPI
    async_database_url = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )
    
    # Create session makers
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    logger.info("Database engines initialized")


async def create_tables() -> None:
    if async_engine is None:
        init_db()
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    if SessionLocal is None:
        init_db()
    
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Initialize database on module import
init_db()
