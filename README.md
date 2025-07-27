# AI Code Review Agent

A sophisticated AI-powered code review agent that analyzes GitHub pull requests using advanced language models to provide comprehensive feedback on code quality, security, performance, and best practices.

## 🚀 Features

- **Automated PR Analysis**: Analyze GitHub pull requests for code quality, security vulnerabilities, and performance issues
- **AI-Powered Reviews**: Uses OpenAI, Anthropic, or local Ollama models for intelligent code analysis
- **Asynchronous Processing**: Built with FastAPI and Celery for scalable background processing
- **Comprehensive Analysis**: Covers security, performance, code quality, maintainability, and documentation
- **RESTful API**: Clean API endpoints for integrating with CI/CD pipelines and GitHub webhooks
- **Docker Support**: Fully containerized with Docker Compose for easy deployment
- **Real-time Status**: Track analysis progress with real-time status updates

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │   GitHub API    │
│   (Web API)     │◄──►│  (Background    │◄──►│   Integration   │
│                 │    │   Analysis)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   AI/LLM APIs   │
│   (Database)    │    │  (Task Queue)   │    │ OpenAI/Anthropic│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## � Assignment API Endpoints

This project implements the exact API endpoints specified in the assignment:

### POST `/analyze-pr`
Submit a GitHub pull request for analysis.

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "pr_number": 123,
  "github_token": "optional_token"
}
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "pending",
  "message": "Pull request analysis task has been queued"
}
```

### GET `/status/<task_id>`
Check the status of an analysis task.

**Response:**
```json
{
  "task_id": "abc123",
  "status": "processing",
  "progress": 65,
  "message": "Analyzing code files..."
}
```

### GET `/results/<task_id>`
Retrieve analysis results (matches assignment output format exactly).

**Response:**
```json
{
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
```

## 🛠 Technology Stack

- **Python 3.8+**
- **FastAPI** - Modern web framework
- **Celery** - Asynchronous task processing
- **Redis** - Task queue and caching
- **PostgreSQL** - Data persistence (optional)
- **AI/LLM APIs** - OpenAI, Anthropic, or Ollama
- **pytest** - Testing framework
- **Docker** - Containerization

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- GitHub Personal Access Token
- OpenAI API Key or Anthropic API Key (optional: Ollama for local LLM)

## 🚀 Quick Start

### 1. Setup the Project

The project is already set up in your workspace! To get started:

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
```env
# GitHub API
GITHUB_TOKEN=your_github_personal_access_token

# AI/LLM Configuration (choose one or more)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database (uses Docker defaults)
DATABASE_URL=postgresql://postgres:password@localhost:5432/code_review_db
REDIS_URL=redis://localhost:6379/0
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Analyze a pull request
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/owner/repository",
    "pr_number": 123,
    "analysis_type": "comprehensive"
  }'
```

## 📊 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analysis/analyze-pr` | POST | Start PR analysis |
| `/api/v1/status/task/{task_id}` | GET | Get task status and results |
| `/api/v1/status/tasks` | GET | List all tasks |
| `/api/v1/analysis/webhook` | POST | GitHub webhook handler |
| `/health` | GET | Service health check |

## 🔧 Development Setup

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A app.tasks.celery_tasks worker --loglevel=info

# Start Celery beat (optional, for scheduled tasks)
celery -A app.tasks.celery_tasks beat --loglevel=info
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_api/
pytest tests/test_services/
pytest -m "not integration"  # Skip integration tests
```

## 📝 Usage Examples

### Basic PR Analysis

```python
import requests

# Start analysis
response = requests.post("http://localhost:8000/api/v1/analysis/analyze-pr", json={
    "repo_url": "https://github.com/facebook/react",
    "pr_number": 12345,
    "analysis_type": "comprehensive",
    "focus_areas": ["security_vulnerabilities", "performance_issues"]
})

task_info = response.json()
task_id = task_info["task_id"]

# Check status
status_response = requests.get(f"http://localhost:8000/api/v1/status/task/{task_id}")
result = status_response.json()

if result["status"] == "completed":
    findings = result["results"]["findings"]
    for finding in findings:
        print(f"{finding['severity']}: {finding['title']}")
        print(f"File: {finding['file_path']}:{finding['line_number']}")
        print(f"Suggestion: {finding['suggestion']}\n")
```

### GitHub Webhook Integration

```bash
# Configure GitHub webhook
# URL: https://your-domain.com/api/v1/analysis/webhook
# Content type: application/json
# Events: Pull requests

# The webhook will automatically trigger analysis for:
# - New pull requests (opened)
# - Updated pull requests (synchronize)
# - Reopened pull requests (reopened)
```

## 🔍 Analysis Types

The system supports different analysis types:

- **comprehensive**: Full analysis including all aspects
- **security**: Focus on security vulnerabilities
- **performance**: Focus on performance issues
- **code_quality**: Focus on code quality and best practices
- **documentation**: Focus on documentation and comments

## 🎯 Focus Areas

You can specify specific focus areas:

- `security_vulnerabilities`: SQL injection, XSS, etc.
- `performance_issues`: Inefficient algorithms, memory leaks
- `code_smells`: Code that works but could be improved
- `best_practices`: Language-specific best practices
- `documentation`: Missing or poor documentation
- `testing`: Test coverage and quality
- `error_handling`: Exception handling patterns
- `maintainability`: Code organization and readability

## 📈 Monitoring

### Celery Monitoring with Flower

Access Flower web interface: http://localhost:5555

### Logs

```bash
# View API logs
docker-compose logs -f api

# View Celery worker logs
docker-compose logs -f celery-worker

# View all logs
docker-compose logs -f
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Service health status
curl http://localhost:8000/api/v1/status/health
```

## 🔐 Security Considerations

- Store API keys in environment variables, never in code
- Use HTTPS in production
- Implement rate limiting for public endpoints
- Validate and sanitize all GitHub URLs
- Use webhook secrets for GitHub webhook verification
- Run containers as non-root users
- Regularly update dependencies for security patches

## 🚀 Deployment

### Production with Docker

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With nginx reverse proxy
docker-compose --profile production up -d
```

### Environment Variables for Production

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:password@your-db-host:5432/dbname
REDIS_URL=redis://your-redis-host:6379/0
```

### Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=3

# Scale API instances (with load balancer)
docker-compose up -d --scale api=2
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the project guidelines
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit with conventional commit messages
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8
- Use Black for code formatting: `black .`
- Use isort for imports: `isort .`
- Use mypy for type checking: `mypy app/`
- Maximum line length: 88 characters

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Comprehensive API docs at `/docs` endpoint

## 🙏 Acknowledgments

- FastAPI for the excellent async web framework
- Celery for reliable task queue management
- OpenAI and Anthropic for powerful AI models
- GitHub for the comprehensive API
- The open-source community for inspiration and tools

---

**Built with ❤️ for better code quality through AI-powered analysis**
