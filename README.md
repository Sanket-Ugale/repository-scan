# AI Code Review Agent

A sophisticated AI-powered code review agent that analyzes GitHub repositories and pull requests using advanced language models to provide comprehensive feedback on code quality, security, performance, and best practices.

## 🚀 Features

- **Repository & PR Analysis**: Analyze entire GitHub repositories or specific pull requests
- **AI-Powered Reviews**: Uses OpenAI, Anthropic, or local Ollama models for intelligent code analysis
- **Asynchronous Processing**: Built with FastAPI and Celery for scalable background processing
- **Comprehensive Analysis**: Covers security vulnerabilities, performance issues, code quality, and style violations
- **Multi-Language Support**: Python, JavaScript/TypeScript, HTML, CSS, Java, C/C++, and more
- **RESTful API**: Clean API v1 endpoints for integrating with CI/CD pipelines and GitHub webhooks
- **Docker Support**: Fully containerized with Docker Compose for easy deployment
- **Real-time Status**: Track analysis progress with real-time status updates and detailed results

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
│   PostgreSQL    │    │     Redis       │    │   Ollama LLM    │
│   (Database)    │    │  (Task Queue)   │    │   (llama3.2)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 API Endpoints (v1)

### Core Analysis Endpoints

#### POST `/api/v1/analysis/analyze-pr`
Submit a GitHub repository or pull request for analysis.

**Repository Analysis (without PR number):**
```json
{
  "repo_url": "https://github.com/sanketugale/vuln_LLM",
  "analysis_type": "comprehensive"
}
```

**Pull Request Analysis (with PR number):**
```json
{
  "repo_url": "https://github.com/user/repo",
  "pr_number": 123,
  "analysis_type": "comprehensive",
  "github_token": "optional_token"
}
```

**Response:**
```json
{
  "task_id": "5101cb2aed4ad598",
  "status": "queued",
  "message": "Repository analysis task queued successfully",
  "repo_url": "https://github.com/sanketugale/vuln_LLM",
  "pr_number": null,
  "estimated_completion_time": 300,
  "created_at": "2025-07-27T14:49:50.355951"
}
```

#### GET `/api/v1/analysis/status/{task_id}`
Check the status and progress of an analysis task.

**Response:**
```json
{
  "task_id": "5101cb2aed4ad598",
  "status": "completed",
  "progress": 100,
  "message": "Repository analysis completed successfully",
  "result": {
    "files": [
      {
        "name": "vulnerable-llm-example.py",
        "issues": [
          {
            "type": "security",
            "line": 15,
            "description": "API_KEY hardcoded, vulnerable to theft",
            "suggestion": "Use environment variables for sensitive data"
          }
        ]
      }
    ],
    "summary": {
      "total_files": 1,
      "total_issues": 14,
      "critical_issues": 8
    }
  },
  "error": null,
  "created_at": "2025-07-27T12:25:39.477202",
  "updated_at": "2025-07-27T14:51:46.762533",
  "repo_url": "https://github.com/sanketugale/vuln_LLM",
  "pr_number": null
}
```

#### GET `/api/v1/analysis/results/{task_id}`
Retrieve detailed analysis results for a completed task.

#### GET `/api/v1/analysis/tasks`
List all analysis tasks with optional filtering by repository or PR number.

**Query Parameters:**
- `repo_url`: Filter by repository URL
- `pr_number`: Filter by pull request number

### Webhook & Health Endpoints

#### POST `/webhook`
GitHub webhook handler for automatic PR analysis.

#### GET `/health`
Service health check endpoint.

#### GET `/`
Root endpoint with basic service information.

## 🛠 Technology Stack

- **Python 3.11+** - Modern Python with async support
- **FastAPI** - High-performance async web framework
- **Celery** - Distributed task queue for background processing
- **Redis** - In-memory data store for task queue and caching
- **PostgreSQL** - Relational database for task persistence
- **Ollama + LLM** - Local LLM integration (llama3.2:3b model)
- **LiteLLM** - Universal LLM API interface
- **Docker** - Containerization and orchestration
- **Pydantic** - Data validation and settings management
- **SQLAlchemy** - Async ORM for database operations
- **pytest** - Comprehensive testing framework

## 🎯 Supported Analysis Types

The system provides comprehensive analysis across multiple dimensions:

### Security Analysis
- ✅ **Injection Vulnerabilities**: SQL injection, XSS, command injection
- ✅ **Authentication Issues**: Hardcoded credentials, weak authentication
- ✅ **Data Exposure**: Sensitive data leakage, improper access controls
- ✅ **Cryptographic Issues**: Weak encryption, improper key management

### Performance Analysis  
- ✅ **Algorithm Efficiency**: O(n²) loops, inefficient data structures
- ✅ **Memory Management**: Memory leaks, excessive allocations
- ✅ **I/O Optimization**: Blocking calls, redundant requests
- ✅ **Resource Usage**: CPU-intensive operations, threading issues

### Code Quality Analysis
- ✅ **Bug Detection**: Logic errors, null pointer exceptions, race conditions
- ✅ **Style Violations**: PEP 8 compliance, naming conventions, formatting
- ✅ **Code Smells**: Duplicate code, long methods, complex conditionals
- ✅ **Maintainability**: Code organization, readability, documentation

### Multi-Language Support
- ✅ **Python**: Comprehensive analysis with security focus
- ✅ **JavaScript/TypeScript**: Modern JS patterns and security
- ✅ **HTML/CSS**: Structure, accessibility, and security
- ✅ **Java**: Enterprise patterns and security practices
- ✅ **C/C++**: Memory safety and performance optimization
- ✅ **Other Languages**: Go, Rust, PHP, Ruby, and more

## 📋 Prerequisites

- **Python 3.11+** (for local development)
- **Docker and Docker Compose** (for containerized deployment)
- **GitHub Personal Access Token** (for repository access)
- **4GB+ RAM** (for Ollama LLM model)
- **10GB+ disk space** (for Docker images and model storage)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# The project is already set up in your workspace!
cd /path/to/ai-code-review-agent

# Verify Docker is running
docker --version
docker-compose --version
```

### 2. Environment Configuration

```bash
# Copy environment template (if not exists)
cp .env.example .env

# Edit configuration
nano .env
```

**Essential environment variables:**
```env
# GitHub API Access
GITHUB_TOKEN=ghp_your_github_personal_access_token

# LLM Configuration (Ollama is pre-configured)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
DEFAULT_LLM_PROVIDER=ollama

# Database & Queue (Docker defaults work)
DATABASE_URL=postgresql://postgres:password@localhost:5432/code_review_db
REDIS_URL=redis://localhost:6379/0

# Optional: External LLM APIs
OPENAI_API_KEY=sk-your-openai-key (optional)
ANTHROPIC_API_KEY=your-anthropic-key (optional)
```

### 3. Start All Services

```bash
# Start the complete stack
docker-compose up -d

# Check all services are running
docker-compose ps

# View startup logs
docker-compose logs -f
```

**Services started:**
- 🌐 **API Server**: http://localhost:8000
- 🔄 **Celery Worker**: Background task processing
- 🗄️ **PostgreSQL**: Task and result storage
- 📊 **Redis**: Task queue management
- 🤖 **Ollama**: Local LLM (llama3.2:3b model)
- 🌸 **Flower**: Task monitoring at http://localhost:5555

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Test repository analysis
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/sanketugale/vuln_LLM",
    "analysis_type": "comprehensive"
  }'

# Check task status (use task_id from previous response)
curl "http://localhost:8000/api/v1/analysis/status/{task_id}"
```

### 5. Import Postman Collection

Import `AI_Code_Review_Agent_Postman_Collection.json` into Postman for comprehensive API testing with pre-configured requests and automated tests.

## 📊 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **Postman Collection**: Import `AI_Code_Review_Agent_Postman_Collection.json`
- **Collection Guide**: See `POSTMAN_COLLECTION_GUIDE.md`

### API Endpoints Summary

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/v1/analysis/analyze-pr` | POST | Start repository/PR analysis | Repository or PR submission |
| `/api/v1/analysis/status/{task_id}` | GET | Get task status and progress | Real-time analysis tracking |
| `/api/v1/analysis/results/{task_id}` | GET | Get detailed analysis results | Completed analysis data |
| `/api/v1/analysis/tasks` | GET | List all analysis tasks | Task management |
| `/webhook` | POST | GitHub webhook handler | Automated PR analysis |
| `/health` | GET | Service health check | System monitoring |
| `/` | GET | API information | Basic service info |

### Response Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 202 | Accepted | Analysis task queued |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Task/resource not found |
| 500 | Internal Error | Server processing error |

### Task Status Flow

```
queued → processing → completed
   ↓        ↓           ↓
pending → analyzing → success
   ↓        ↓           ↓
   ←────── failed ──────
```

## 🔧 Development Setup

### Local Development Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Set up pre-commit hooks (if configured)
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Start only the database and Redis for development
docker-compose up -d db redis ollama

# Run database migrations
python scripts/migrate_db.py

# Initialize database tables  
python scripts/init_database.py
```

### Running Services Locally

```bash
# Terminal 1: Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A app.tasks.celery_tasks worker --loglevel=info

# Terminal 3: Start Celery beat scheduler (optional)
celery -A app.tasks.celery_tasks beat --loglevel=info

# Terminal 4: Start Flower monitoring (optional)
celery -A app.tasks.celery_tasks flower
```

### Development Tools

```bash
# Code formatting
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
pylint app/

# Security scanning
bandit -r app/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/test_api/
pytest tests/test_services/
pytest tests/test_tasks/

# Run integration tests
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Verbose output
pytest -v --tb=short
```

### Test Coverage Goals

Current test coverage status:
- **API Routes**: ✅ 85%+ coverage
- **Core Services**: ✅ 90%+ coverage  
- **Task Processing**: ✅ 80%+ coverage
- **Utilities**: ✅ 95%+ coverage
- **Overall Target**: 🎯 85%+ coverage

### Development Workflow

1. **Feature Development**:
   ```bash
   git checkout -b feature/new-analysis-type
   # Make changes
   pytest tests/
   black app/ tests/
   git commit -m "Add new analysis type"
   ```

2. **Integration Testing**:
   ```bash
   # Test with real repositories
   python scripts/test_analysis.py
   
   # Test API endpoints
   pytest tests/test_integration/
   ```

3. **Performance Testing**:
   ```bash
   # Load testing with multiple concurrent requests
   python scripts/load_test.py
   
   # Memory profiling
   python -m memory_profiler scripts/profile_analysis.py
   ```

## 📝 Usage Examples

### 1. Repository Security Analysis

Analyze an entire repository for security vulnerabilities:

```python
import requests
import time

# Submit repository for analysis
response = requests.post("http://localhost:8000/api/v1/analysis/analyze-pr", json={
    "repo_url": "https://github.com/sanketugale/vuln_LLM",
    "analysis_type": "comprehensive"
})

task_info = response.json()
task_id = task_info["task_id"]
print(f"Analysis started: {task_id}")

# Monitor progress
while True:
    status_response = requests.get(f"http://localhost:8000/api/v1/analysis/status/{task_id}")
    result = status_response.json()
    
    print(f"Status: {result['status']} ({result.get('progress', 0)}%)")
    
    if result["status"] == "completed":
        # Print analysis summary
        summary = result["result"]["summary"]
        print(f"\n📊 Analysis Complete!")
        print(f"Files analyzed: {summary['total_files']}")
        print(f"Total issues: {summary['total_issues']}")
        print(f"Critical issues: {summary['critical_issues']}")
        
        # Print detailed findings
        for file_result in result["result"]["files"]:
            print(f"\n📄 {file_result['name']}")
            for issue in file_result["issues"][:3]:  # Show first 3 issues
                print(f"  🔍 {issue['type'].upper()}: {issue['description']}")
                print(f"     Line {issue['line']}: {issue['suggestion']}")
        break
    
    time.sleep(5)  # Check every 5 seconds
```

### 2. Pull Request Analysis

Analyze specific pull request changes:

```bash
# Analyze PR #123 in a repository
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/facebook/react",
    "pr_number": 123,
    "analysis_type": "comprehensive"
  }'
```

### 3. Private Repository with Authentication

```bash
# Use GitHub token for private repos
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-org/private-repo",
    "analysis_type": "comprehensive",
    "github_token": "ghp_your_personal_access_token"
  }'
```

### 4. GitHub Webhook Integration

Set up automatic analysis for new PRs:

```bash
# Configure GitHub webhook
# URL: https://your-domain.com/webhook
# Content type: application/json
# Events: Pull requests

# Webhook payload example
{
  "action": "opened",
  "pull_request": {
    "number": 42,
    "base": {
      "repo": {
        "full_name": "owner/repository"
      }
    }
  }
}
```

### 5. Batch Task Management

```python
# List all analysis tasks
all_tasks = requests.get("http://localhost:8000/api/v1/analysis/tasks").json()

# Filter by repository
vuln_tasks = requests.get(
    "http://localhost:8000/api/v1/analysis/tasks",
    params={"repo_url": "https://github.com/sanketugale/vuln_LLM"}
).json()

# Filter by PR number
pr_tasks = requests.get(
    "http://localhost:8000/api/v1/analysis/tasks",
    params={"pr_number": 42}
).json()
```

### 6. Real-world Example Output

Analysis of `vuln_LLM` repository found **14 issues** across **1 file**:

```
📄 vulnerable-llm-example.py
🔍 SECURITY: API_KEY hardcoded, vulnerable to theft
   Line 23: Store sensitive information securely using environment variables

🔍 SECURITY: Plugin code execution without validation poses risk  
   Line 31: Implement plugin validation and sandboxing mechanisms

🔍 PERFORMANCE: Direct string concatenation can be slow
   Line 15: Use parameterized queries for better performance

🔍 BUG: The system_prompt variable is not properly sanitized
   Line 15: Sanitize user input using proper escaping techniques

🔍 STYLE: Variable names don't follow naming convention
   Line 15: Use snake_case consistently throughout codebase
```

## 🔍 Analysis Features

### Comprehensive Analysis Types

| Analysis Type | Description | Use Case |
|---------------|-------------|----------|
| `comprehensive` | Full analysis of all aspects | Complete code review |
| `security` | Focus on security vulnerabilities | Security audits |
| `performance` | Focus on performance issues | Optimization reviews |
| `quality` | Focus on code quality and style | Code standards compliance |

### Issue Categories

The system identifies and categorizes issues into:

- **🔴 Security**: Vulnerabilities, injection attacks, data exposure
- **🟡 Performance**: Inefficient algorithms, memory leaks, I/O issues
- **🔵 Bug**: Logic errors, null pointers, exception handling
- **🟣 Style**: Naming conventions, formatting, PEP 8 compliance
- **🟢 Quality**: Code smells, maintainability, documentation

### Real Analysis Results

Here are real results from analyzing test repositories:

#### vuln_LLM Repository Analysis
```json
{
  "summary": {
    "total_files": 1,
    "total_issues": 14,
    "critical_issues": 8
  },
  "issues_by_type": {
    "security": 5,
    "performance": 2,
    "bug": 3,
    "style": 2,
    "quality": 2
  }
}
```

#### accc Repository Analysis (HTML)
```json
{
  "summary": {
    "total_files": 1,
    "total_issues": 4,
    "critical_issues": 1
  },
  "issues_found": [
    "Security: Mixed inline and external resources",
    "Performance: External stylesheet recommendation",
    "Style: Inconsistent naming conventions"
  ]
}
```

## 📈 Monitoring & Operations

### Service Health Monitoring

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed service status
curl http://localhost:8000/api/v1/analysis/tasks | jq '.[] | {task_id, status, repo_url}'

# Check Docker services
docker-compose ps
```

### Celery Task Monitoring with Flower

Access the Flower web interface for real-time task monitoring:
- **URL**: http://localhost:5555
- **Features**: Task history, worker status, real-time monitoring
- **Metrics**: Task success/failure rates, processing times

### Log Management

```bash
# View API logs
docker-compose logs -f api

# View Celery worker logs  
docker-compose logs -f celery-worker

# View Ollama LLM logs
docker-compose logs -f ollama

# View all service logs
docker-compose logs -f

# Filter logs by severity
docker-compose logs api | grep ERROR
```

### Performance Metrics

Monitor key performance indicators:

| Metric | Good | Needs Attention |
|--------|------|-----------------|
| Task completion time | < 5 minutes | > 10 minutes |
| Memory usage (Ollama) | < 3GB | > 4GB |
| Queue length | < 5 tasks | > 20 tasks |
| Error rate | < 5% | > 10% |

### Troubleshooting Common Issues

#### API Connection Issues
```bash
# Check if API is responding
curl -I http://localhost:8000/health

# Restart API service
docker-compose restart api
```

#### LLM Analysis Failures
```bash
# Check Ollama model status
curl http://localhost:11434/api/tags

# Restart Ollama service
docker-compose restart ollama

# Check Ollama logs for errors
docker-compose logs ollama | tail -50
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db

# View database logs
docker-compose logs db
```

#### Task Queue Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Clear stuck tasks (use cautiously)
docker-compose exec redis redis-cli FLUSHDB

# Restart Celery worker
docker-compose restart celery-worker
```

## 🔐 Security Considerations

- Store API keys in environment variables, never in code
- Use HTTPS in production
- Implement rate limiting for public endpoints
- Validate and sanitize all GitHub URLs
- Use webhook secrets for GitHub webhook verification
- Run containers as non-root users
- Regularly update dependencies for security patches

## 🚀 Production Deployment

### Docker Production Setup

```bash
# Production deployment with optimized containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With nginx reverse proxy and SSL
docker-compose --profile production up -d

# Scale workers for high load
docker-compose up -d --scale celery-worker=3
```

### Environment Variables for Production

```env
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-super-secret-production-key-min-32-chars
ALGORITHM=HS256

# Database (Use managed service in production)
DATABASE_URL=postgresql://user:password@your-db-host:5432/dbname

# Redis (Use managed service in production) 
REDIS_URL=redis://your-redis-host:6379/0

# GitHub Integration
GITHUB_TOKEN=ghp_production_token_with_appropriate_scopes

# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
DEFAULT_LLM_PROVIDER=ollama

# Performance Tuning
CELERY_WORKER_CONCURRENCY=4
MAX_RETRY_ATTEMPTS=3
TASK_TIMEOUT_SECONDS=600
```

### Load Balancing & Scaling

```bash
# Scale API instances (requires load balancer)
docker-compose up -d --scale api=3

# Scale Celery workers for analysis throughput
docker-compose up -d --scale celery-worker=5

# Monitor resource usage
docker stats
```

### Production Monitoring

1. **Application Monitoring**:
   - Flower dashboard: Monitor Celery tasks
   - API health endpoint: `/health`
   - Custom metrics: Task completion rates, error rates

2. **Infrastructure Monitoring**:
   - Docker container health
   - Database connection pool
   - Redis memory usage
   - Ollama model performance

3. **Alerting Setup**:
   ```bash
   # Example alerting rules
   - Task failure rate > 10%
   - Queue length > 50 tasks
   - API response time > 5 seconds
   - Memory usage > 90%
   ```

### Security Best Practices

1. **API Security**:
   - Use HTTPS in production
   - Implement rate limiting
   - Validate all GitHub URLs
   - Use webhook secrets for GitHub integration

2. **Container Security**:
   - Run containers as non-root users
   - Use specific image tags, not `latest`
   - Regularly update base images
   - Scan images for vulnerabilities

3. **Secrets Management**:
   - Store secrets in environment variables
   - Use secret management services (AWS Secrets Manager, etc.)
   - Rotate API keys regularly
   - Never commit secrets to version control

### Backup & Recovery

```bash
# Database backup
docker-compose exec db pg_dump -U postgres code_review_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres code_review_db < backup.sql

# Redis data backup
docker-compose exec redis redis-cli BGSAVE
```

### Performance Optimization

1. **Database Optimization**:
   - Index frequently queried columns
   - Use connection pooling
   - Monitor slow queries

2. **Celery Optimization**:
   - Tune worker concurrency based on CPU cores
   - Use appropriate task routing
   - Monitor memory usage per worker

3. **LLM Performance**:
   - Use GPU acceleration for Ollama if available
   - Implement result caching for similar queries
   - Monitor model response times

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
