import os
from functools import lru_cache
from typing import List, Optional

# Load dotenv manually to ensure .env files are loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Handle Pydantic v2 compatibility
try:
    from pydantic_settings import BaseSettings
    from pydantic import validator
except ImportError:
    try:
        from pydantic import BaseSettings, validator
    except ImportError:
        # Fallback to basic configuration without validation
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
                    
        def validator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator


class Settings(BaseSettings):
    # Environment Configuration
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Code Review Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = os.environ.get('DATABASE_URL')
    REDIS_URL: str = os.environ.get('REDIS_URL', "redis://localhost:6379/0")

    # GitHub API Configuration
    GITHUB_TOKEN: Optional[str] = os.environ.get('GITHUB_TOKEN')
    GITHUB_WEBHOOK_SECRET: Optional[str] = os.environ.get('GITHUB_WEBHOOK_SECRET')
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get('ANTHROPIC_API_KEY')
    DEFAULT_LLM_PROVIDER: str = os.environ.get('DEFAULT_LLM_PROVIDER', 'ollama')
    DEFAULT_MODEL: str = os.environ.get('DEFAULT_MODEL', 'llama3.2:3b')
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_API_BASE: str = os.environ.get('OLLAMA_API_BASE', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
    
    # Local LLM Configuration (fallback)
    LOCAL_LLM_BASE_URL: Optional[str] = os.environ.get('LOCAL_LLM_BASE_URL', 'http://localhost:4000')
    LOCAL_LLM_API_KEY: Optional[str] = os.environ.get('LOCAL_LLM_API_KEY')
    LOCAL_LLM_MODEL: str = os.environ.get('LOCAL_LLM_MODEL', 'llama3.2:3b')  # Use the same model as Ollama
    
    def __init__(self, **kwargs):
        # Initialize with defaults first
        super().__init__(**kwargs)
        
        # Override with environment variables if available
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', self.ENVIRONMENT)
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', self.OPENAI_API_KEY)
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', self.ANTHROPIC_API_KEY)
        self.DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', self.DEFAULT_LLM_PROVIDER)
        self.DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', self.DEFAULT_MODEL)
        self.OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', self.OLLAMA_BASE_URL)
        self.OLLAMA_API_BASE = os.getenv('OLLAMA_API_BASE', self.OLLAMA_API_BASE)
        self.OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', self.OLLAMA_MODEL)
        self.LOCAL_LLM_BASE_URL = os.getenv('LOCAL_LLM_BASE_URL', self.LOCAL_LLM_BASE_URL)
        self.LOCAL_LLM_API_KEY = os.getenv('LOCAL_LLM_API_KEY', self.LOCAL_LLM_API_KEY)
        self.LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', self.LOCAL_LLM_MODEL)
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.environ.get('CELERY_BROKER_URL', "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.environ.get('CELERY_RESULT_BACKEND', "redis://localhost:6379/2")
    CELERY_TASK_SERIALIZER: str = os.environ.get('CELERY_TASK_SERIALIZER', "json")
    CELERY_RESULT_SERIALIZER: str = os.environ.get('CELERY_RESULT_SERIALIZER', "json")
    CELERY_ACCEPT_CONTENT: List[str] = os.environ.get('CELERY_ACCEPT_CONTENT', ["json"])
    CELERY_TIMEZONE: str = os.environ.get('CELERY_TIMEZONE', "UTC")
    CELERY_ENABLE_UTC: bool = True
    
    # Security Configuration
    SECRET_KEY: str = os.environ.get('SECRET_KEY', "your-super-secret-key-change-in-production")
    ALGORITHM: str = os.environ.get('ALGORITHM', "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', "INFO")
    LOG_FORMAT: str = os.environ.get('LOG_FORMAT', "json")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Task Configuration
    MAX_RETRY_ATTEMPTS: int = 3
    TASK_TIMEOUT_SECONDS: int = 600
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("DEFAULT_LLM_PROVIDER")
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        valid_providers = {"openai", "anthropic", "ollama", "local"}
        if v.lower() not in valid_providers:
            raise ValueError(f"DEFAULT_LLM_PROVIDER must be one of {valid_providers}")
        return v.lower()
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is not using default value in production."""
        if v == "your-super-secret-key-change-in-production":
            import os
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("SECRET_KEY must be changed in production")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
