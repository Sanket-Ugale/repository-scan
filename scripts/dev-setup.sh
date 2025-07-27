#!/bin/bash

# Development setup script for AI Code Review Agent

set -e

echo "🚀 Setting up AI Code Review Agent development environment..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Python version: $python_version"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install pre-commit black isort mypy flake8

# Set up pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your API keys and configuration"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs temp ssl

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'docker-compose up -d' to start services"
echo "3. Run 'source venv/bin/activate' to activate virtual environment"
echo "4. Run 'uvicorn app.main:app --reload' to start development server"
echo ""
echo "🔗 Useful commands:"
echo "  - Start all services: docker-compose up -d"
echo "  - View logs: docker-compose logs -f"
echo "  - Run tests: pytest"
echo "  - Format code: black . && isort ."
echo "  - Type check: mypy app/"
