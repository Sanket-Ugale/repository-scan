#!/bin/bash

# AI Code Review Agent - Dependency Installation Script
# This script helps install dependencies step by step to handle version conflicts

echo "AI Code Review Agent - Installing Dependencies"
echo "============================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip

# Install minimal dependencies first
echo "Installing core dependencies..."
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart

# Install dependencies group by group
echo "Installing data validation dependencies..."
pip install pydantic==2.5.0 pydantic-settings==2.1.0

echo "Installing database dependencies..."
pip install sqlalchemy==2.0.23 alembic==1.12.1 || echo "Database deps failed - continuing..."

echo "Installing async processing dependencies..."
pip install celery==5.3.4 redis==5.0.1 || echo "Celery deps failed - continuing..."

echo "Installing HTTP client dependencies..."
pip install httpx==0.25.2 requests==2.31.0 || echo "HTTP deps failed - continuing..."

echo "Installing AI/LLM dependencies..."
pip install openai==1.3.7 anthropic==0.8.1 || echo "AI deps failed - continuing..."
pip install litellm==1.74.8 || echo "LiteLLM failed - continuing..."

echo "Installing GitHub API dependencies..."
pip install PyGithub==2.1.1 || echo "GitHub deps failed - continuing..."

echo "Installing additional dependencies..."
pip install aiohttp==3.9.1 || echo "aiohttp failed - continuing..."

echo "Installing optional security dependencies..."
pip install python-jose[cryptography] passlib[bcrypt] || echo "Security deps failed - continuing..."

echo "Installing optional logging dependencies..."
pip install structlog || echo "Structlog failed - continuing..."

echo "Installing database driver..."
pip install psycopg2-binary==2.9.9 || pip install asyncpg || echo "Database drivers failed - continuing..."

echo "Installing development dependencies..."
pip install pytest pytest-asyncio pytest-mock || echo "Test deps failed - continuing..."

echo ""
echo "Installation complete! Some optional dependencies may have failed."
echo "The application should still work with core functionality."
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To test the setup:"
echo "  python -c 'from app.main import app; print(\"App imported successfully!\")'"
