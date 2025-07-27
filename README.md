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

## 🏛️ Design Decisions

### Architecture Patterns

#### **Microservices-Inspired Design**
- **Separation of Concerns**: API layer (FastAPI) separated from background processing (Celery)
- **Scalability**: Each component can be scaled independently based on load
- **Fault Tolerance**: Failure in one component doesn't bring down the entire system

#### **Async-First Approach**
- **Non-blocking I/O**: All database and external API calls use async/await
- **High Concurrency**: Can handle multiple repository analyses simultaneously
- **Resource Efficiency**: Better CPU utilization compared to synchronous alternatives

#### **Task Queue Pattern**
- **Background Processing**: Long-running analysis tasks don't block API responses
- **Reliability**: Tasks are persisted and can survive worker restarts
- **Retry Logic**: Failed tasks are automatically retried with exponential backoff

### Technology Choices

#### **FastAPI over Flask/Django**
- **Performance**: Superior async performance for I/O-heavy operations
- **Type Safety**: Built-in Pydantic integration for request/response validation
- **Documentation**: Automatic OpenAPI/Swagger documentation generation
- **Modern Python**: Leverages Python 3.11+ features like async/await

#### **Celery over Threading/Multiprocessing**
- **Distributed**: Can scale across multiple machines
- **Persistent**: Tasks survive application restarts
- **Monitoring**: Built-in monitoring with Flower
- **Reliability**: Proven in production environments

#### **PostgreSQL over MongoDB/SQLite**
- **ACID Compliance**: Ensures data consistency for task states
- **JSON Support**: Native JSON fields for storing analysis results
- **Performance**: Excellent performance for complex queries
- **Async Support**: Works well with asyncpg driver

#### **Ollama over Cloud LLMs Only**
- **Privacy**: Code analysis happens locally, no data sent to external services
- **Cost**: No per-token charges for analysis
- **Reliability**: No dependency on external API availability
- **Flexibility**: Can switch models without changing code

#### **Redis over Database Queue**
- **Speed**: In-memory operations are faster than disk-based queues
- **Features**: Built-in pub/sub for real-time updates
- **Reliability**: Persistence options available
- **Ecosystem**: Well-integrated with Celery

### Data Flow Design

#### **Repository Analysis Pipeline**
1. **Input Validation**: GitHub URL validation and repository access verification
2. **File Discovery**: Intelligent file filtering based on language and size
3. **Content Extraction**: Efficient file reading with size limits
4. **AI Analysis**: Structured prompts for consistent analysis results
5. **Result Processing**: Categorization and priority scoring of issues

#### **Error Handling Strategy**
- **Graceful Degradation**: Partial results if some files fail to analyze
- **Retry Logic**: Transient failures are retried automatically
- **Detailed Logging**: Comprehensive error context for debugging
- **User Feedback**: Clear error messages for user-facing issues

### Security Design

#### **Input Sanitization**
- **URL Validation**: Strict GitHub URL pattern matching
- **Content Limits**: File size and repository size restrictions
- **Token Handling**: Secure storage and transmission of GitHub tokens

#### **Least Privilege**
- **Container Security**: Non-root containers with minimal permissions
- **API Access**: Rate limiting and authentication where needed
- **Database Access**: Connection pooling with connection limits

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

## 🔧 Project Setup Instructions

### Development Environment Setup

#### **Option 1: Docker Development (Recommended)**

This is the fastest way to get started with a complete development environment.

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-code-review-agent

# 2. Create environment configuration
cp .env.example .env
# Edit .env file with your settings (see Configuration section below)

# 3. Start all services
docker-compose up -d

# 4. Verify setup
curl http://localhost:8000/health
```

#### **Option 2: Local Development**

For development with local Python environment and external services.

```bash
# 1. Clone and navigate
git clone <repository-url>
cd ai-code-review-agent

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start external services (Redis, PostgreSQL, Ollama)
docker-compose up -d db redis ollama

# 5. Configure environment
cp .env.example .env
# Edit .env with local service URLs

# 6. Initialize database
python scripts/init_database.py

# 7. Start services
# Terminal 1: API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
celery -A app.tasks.celery_tasks worker --loglevel=info

# Terminal 3: Flower monitoring (optional)
celery -A app.tasks.celery_tasks flower
```

### Configuration Guide

#### **Essential Environment Variables**

Create a `.env` file in the project root with these required settings:

```env
# GitHub Integration (Required for repository access)
GITHUB_TOKEN=ghp_your_github_personal_access_token

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/code_review_db

# Redis Configuration (Task Queue)
REDIS_URL=redis://localhost:6379/0

# LLM Configuration (Ollama is default)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
DEFAULT_LLM_PROVIDER=ollama

# Optional: External LLM APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Security
SECRET_KEY=your-super-secret-key-at-least-32-characters
ALGORITHM=HS256

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development
```

#### **GitHub Token Setup**

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of private repositories
   - `public_repo` - Access public repositories
   - `read:org` - Read organization membership
4. Copy the token and add to `.env` file

#### **Service Port Configuration**

| Service | Default Port | Environment Variable | Purpose |
|---------|--------------|---------------------|---------|
| FastAPI | 8000 | `API_PORT` | Main API server |
| PostgreSQL | 5432 | `DATABASE_URL` | Task and result storage |
| Redis | 6379 | `REDIS_URL` | Task queue |
| Ollama | 11434 | `OLLAMA_BASE_URL` | Local LLM service |
| Flower | 5555 | `FLOWER_PORT` | Task monitoring |

### Verification Steps

After setup, verify your installation:

```bash
# 1. Check service health
curl http://localhost:8000/health

# 2. Test repository analysis
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "analysis_type": "comprehensive"
  }'

# 3. Check Docker services
docker-compose ps

# 4. View service logs
docker-compose logs -f api
```

### Troubleshooting Setup Issues

#### **Common Issues & Solutions**

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Docker not running | `docker-compose` command fails | Start Docker Desktop/daemon |
| Port conflicts | "Port already in use" error | Change ports in `docker-compose.yml` |
| GitHub token invalid | 401/403 errors on analysis | Verify token and permissions |
| Ollama model missing | LLM analysis fails | Wait for model download (first run) |
| Database connection | Database errors in logs | Check PostgreSQL service status |

#### **Reset and Clean Install**

If you encounter persistent issues:

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Development Tools Setup

#### **Code Quality Tools**

```bash
# Install development dependencies
pip install black isort flake8 mypy pytest

# Set up pre-commit hooks (optional)
pre-commit install

# Run code formatting
black app/ tests/
isort app/ tests/

# Run type checking
mypy app/

# Run tests
pytest --cov=app
```

#### **IDE Configuration**

**VS Code Extensions:**
- Python
- Docker
- REST Client
- GitLens

**PyCharm Settings:**
- Enable async/await support
- Configure Black as code formatter
- Set up pytest as test runner

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

The project includes a comprehensive Postman collection for API testing:

**Collection Location**: `./AI_Code_Review_Agent_Postman_Collection.json` (in project root)

**Import Instructions**:
1. Open Postman application
2. Click "Import" button (top left)
3. Select "Upload Files" tab
4. Choose `AI_Code_Review_Agent_Postman_Collection.json` from the project directory
5. Click "Import" to add all pre-configured requests

**What's Included**:
- ✅ All API endpoints with example requests
- ✅ Environment variables for easy server switching
- ✅ Automated tests for response validation
- ✅ Real GitHub repository examples
- ✅ Error handling test cases

Import `AI_Code_Review_Agent_Postman_Collection.json` into Postman for comprehensive API testing with pre-configured requests and automated tests.

## 📊 API Documentation

### Interactive Documentation & Testing

#### **Live API Documentation**
- **Swagger UI**: http://localhost:8000/api/v1/docs
  - Interactive API explorer with request/response examples
  - Try out endpoints directly from the browser
  - Comprehensive schema documentation
- **ReDoc**: http://localhost:8000/api/v1/redoc
  - Clean, readable API documentation
  - Detailed parameter descriptions
  - Code examples in multiple languages

#### **Postman Collection Testing**
- **Collection File**: `./AI_Code_Review_Agent_Postman_Collection.json`
- **Collection Guide**: See `POSTMAN_COLLECTION_GUIDE.md` for detailed usage
- **Features**:
  - Pre-configured requests for all endpoints
  - Environment variables for server switching
  - Automated response validation tests
  - Real repository examples for testing

#### **API Base URL**
```
Development: http://localhost:8000/api/v1
Production:  https://your-domain.com/api/v1
```

### Core API Endpoints

#### **Analysis Management**

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/analysis/analyze-pr` | POST | Submit repository/PR for analysis | Optional GitHub token |
| `/api/v1/analysis/status/{task_id}` | GET | Get real-time task status | None |
| `/api/v1/analysis/results/{task_id}` | GET | Retrieve detailed analysis results | None |
| `/api/v1/analysis/tasks` | GET | List and filter analysis tasks | None |

#### **System Endpoints**

| Endpoint | Method | Description | Purpose |
|----------|--------|-------------|---------|
| `/webhook` | POST | GitHub webhook handler | Automated PR analysis |
| `/health` | GET | Service health check | System monitoring |
| `/` | GET | API information and status | Basic service info |

### Request/Response Examples

#### **Analyze Repository**
```bash
POST /api/v1/analysis/analyze-pr
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repository",
  "analysis_type": "comprehensive",
  "github_token": "optional_token_for_private_repos"
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "abc123def456",
  "status": "queued",
  "message": "Repository analysis task queued successfully",
  "repo_url": "https://github.com/user/repository",
  "estimated_completion_time": 300,
  "created_at": "2025-01-27T10:30:00Z"
}
```

#### **Check Task Status**
```bash
GET /api/v1/analysis/status/abc123def456
```

**Response (200 OK):**
```json
{
  "task_id": "abc123def456",
  "status": "completed",
  "progress": 100,
  "message": "Analysis completed successfully",
  "result": {
    "summary": {
      "total_files": 15,
      "total_issues": 23,
      "critical_issues": 3
    },
    "files": [...]
  },
  "created_at": "2025-01-27T10:30:00Z",
  "updated_at": "2025-01-27T10:35:00Z"
}
```

### HTTP Status Codes

| Code | Status | Description | When It Occurs |
|------|--------|-------------|----------------|
| 200 | OK | Request successful | Successful GET requests |
| 202 | Accepted | Analysis task queued | Successful POST to analyze-pr |
| 400 | Bad Request | Invalid input parameters | Malformed requests, invalid URLs |
| 404 | Not Found | Resource not found | Task ID doesn't exist |
| 422 | Unprocessable Entity | Validation errors | Invalid request schema |
| 429 | Too Many Requests | Rate limit exceeded | Too many concurrent requests |
| 500 | Internal Server Error | Server processing error | Unexpected server errors |
| 503 | Service Unavailable | Service temporarily down | Maintenance or overload |

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "INVALID_REPOSITORY_URL",
    "message": "The provided repository URL is not valid",
    "details": {
      "field": "repo_url",
      "provided": "invalid-url",
      "expected": "https://github.com/owner/repository"
    }
  },
  "request_id": "req_123456789"
}
```

### Rate Limiting

| Endpoint | Rate Limit | Window | Notes |
|----------|------------|--------|-------|
| `/api/v1/analysis/analyze-pr` | 10 requests | 1 minute | Per IP address |
| `/api/v1/analysis/status/*` | 100 requests | 1 minute | Per IP address |
| `/api/v1/analysis/results/*` | 50 requests | 1 minute | Per IP address |
| `/webhook` | 1000 requests | 1 minute | Per webhook source |

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

## 🚀 Future Improvements

### Short-term Enhancements (v1.1)

#### **Enhanced Analysis Capabilities**
- **Code Complexity Metrics**: Cyclomatic complexity, maintainability index
- **Dependency Analysis**: Outdated packages, security vulnerabilities in dependencies
- **Performance Profiling**: Memory usage patterns, execution time analysis
- **Code Coverage**: Integration with test coverage reports

#### **User Experience Improvements**
- **Web Dashboard**: Browser-based interface for analysis management
- **Real-time Notifications**: WebSocket-based progress updates
- **Analysis History**: Searchable history of past analyses
- **Custom Rules**: User-definable analysis rules and thresholds

#### **Integration Enhancements**
- **GitHub App**: Official GitHub App for seamless integration
- **CI/CD Plugins**: Jenkins, GitLab CI, GitHub Actions plugins
- **IDE Extensions**: VS Code, PyCharm extensions for inline analysis
- **Slack/Teams Integration**: Analysis notifications in team channels

### Medium-term Goals (v2.0)

#### **Advanced AI Features**
- **Multi-Model Analysis**: Combine results from multiple LLM models
- **Code Generation**: Suggest fixes and improvements, not just identify issues
- **Learning System**: Improve analysis quality based on user feedback
- **Context-Aware Analysis**: Consider project-specific patterns and conventions

#### **Enterprise Features**
- **RBAC (Role-Based Access Control)**: Team and permission management
- **SSO Integration**: SAML, OAuth2, Active Directory support
- **Audit Logging**: Comprehensive audit trails for compliance
- **Custom Deployment**: On-premises deployment options

#### **Performance & Scalability**
- **Horizontal Scaling**: Auto-scaling based on analysis load
- **Caching Layer**: Redis-based caching for repeated analyses
- **Result Streaming**: Stream analysis results as they become available
- **Incremental Analysis**: Only analyze changed files in repositories

### Long-term Vision (v3.0+)

#### **AI-Powered Development Assistant**
- **Predictive Analysis**: Predict potential issues before they occur
- **Code Quality Trends**: Track quality metrics over time
- **Team Insights**: Developer productivity and code quality analytics
- **Automated Refactoring**: AI-driven code improvement suggestions

#### **Advanced Language Support**
- **Language-Specific Rules**: Deep analysis for specific languages and frameworks
- **Framework Integration**: Django, React, Spring Boot specific analysis
- **Configuration Analysis**: Docker, Kubernetes, CI/CD configuration review
- **Documentation Analysis**: README, API docs quality assessment

#### **Research & Innovation**
- **Custom Model Training**: Fine-tune models on organization's codebase
- **Vulnerability Database**: Real-time security vulnerability detection
- **Code Similarity Detection**: Detect code clones and similar patterns
- **Architectural Analysis**: System design and architecture recommendations


## 🙏 Acknowledgments

- FastAPI for the excellent async web framework
- Celery for reliable task queue management
- OpenAI and Anthropic for powerful AI models
- GitHub for the comprehensive API
- The open-source community for inspiration and tools

---

**Built with ❤️ for better code quality through AI-powered analysis**
