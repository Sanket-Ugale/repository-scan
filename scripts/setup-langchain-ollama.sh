#!/bin/bash

# Setup script for AI Code Review Agent with LangChain and Ollama

echo "🚀 Setting up AI Code Review Agent with LangChain and Ollama..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🔄 Starting services (except Ollama model pull)..."
docker-compose up -d db redis

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

echo "🤖 Starting Ollama service..."
docker-compose up -d ollama

echo "⏳ Waiting for Ollama to be ready..."
sleep 15

echo "📥 Pulling Ollama model (this may take a few minutes)..."
docker-compose exec ollama ollama pull llama3.2:3b

echo "🔍 Verifying Ollama model..."
docker-compose exec ollama ollama list

echo "🚀 Starting all services..."
docker-compose up -d

echo "⏳ Waiting for all services to be ready..."
sleep 10

echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Setup completed!"
echo ""
echo "🌐 Services available at:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Flower (Celery monitoring): http://localhost:5555"
echo "   - Ollama API: http://localhost:11434"
echo ""
echo "🧪 To run tests:"
echo "   docker-compose exec api python -m pytest"
echo ""
echo "📊 To check logs:"
echo "   docker-compose logs -f api"
echo "   docker-compose logs -f ollama"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
