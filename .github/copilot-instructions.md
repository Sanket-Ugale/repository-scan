<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI Code Review Agent - Copilot Instructions

## Project Overview
This is an AI-powered code review agent system built with FastAPI, Celery, and AI models for automated GitHub pull request analysis.

## Architecture Guidelines
- **Backend**: FastAPI with async/await patterns
- **Task Queue**: Celery with Redis backend
- **AI/LLM**: OpenAI, Anthropic, or local Ollama integration
- **Database**: PostgreSQL with SQLAlchemy async
- **Containerization**: Docker and Docker Compose

## Code Style Standards
- Follow PEP 8 strictly
- Use type hints for all functions
- Maximum line length: 88 characters (Black formatter)
- Use descriptive variable and function names
- Prefer composition over inheritance
- Use Pydantic models for data validation

## Key Patterns to Follow

### FastAPI Patterns
- Use dependency injection for database sessions and services
- Implement proper error handling with HTTPException
- Use async/await consistently for I/O operations
- Include comprehensive docstrings for all endpoints
- Use Pydantic models for request/response validation

### Celery Best Practices
- Always use .delay() or .apply_async() for task execution
- Implement proper error handling and retries
- Use task routing for different analysis types
- Store task results with appropriate expiration
- Log task execution details for monitoring

### Error Handling
- Use structured error responses with consistent format
- Implement retry logic for transient failures
- Log errors with proper context using structlog
- Provide meaningful error messages to users

### Security Considerations
- Validate all input data with Pydantic models
- Sanitize GitHub URLs and validate repository access
- Store sensitive data in environment variables
- Implement rate limiting for API endpoints

### AI/LLM Integration
- Create modular tool functions for GitHub API interactions
- Implement proper prompt engineering with clear instructions
- Handle LLM API errors gracefully with fallbacks
- Use structured output parsing (JSON, Pydantic models)
- Implement token usage tracking and cost monitoring

## File Organization
- `app/api/` - FastAPI routes and dependencies
- `app/core/` - Configuration, database, security utilities
- `app/models/` - Pydantic schemas and SQLAlchemy models
- `app/services/` - External API integrations (GitHub, LLM)
- `app/tasks/` - Celery task definitions
- `app/utils/` - Helper functions and utilities

## Testing Guidelines
- Write tests for all public functions and API endpoints
- Use pytest with async support
- Mock external APIs (GitHub, OpenAI) in tests
- Test both success and failure scenarios
- Aim for >80% code coverage

## Environment Variables
All configuration should use environment variables with sensible defaults:
- Database and Redis URLs
- API keys for GitHub, OpenAI, Anthropic
- Celery configuration
- Logging and security settings

## Documentation Requirements
- Add comprehensive docstrings to all classes and functions
- Include examples in docstrings where helpful
- Document API endpoints with OpenAPI/Swagger descriptions
- Use type hints consistently

## Common Issues to Avoid
- Don't use blocking I/O in async functions
- Don't hardcode configuration values
- Don't ignore error handling
- Don't skip input validation
- Don't expose sensitive data in logs

## Performance Considerations
- Use async/await for I/O operations
- Implement connection pooling for databases
- Cache frequently accessed data
- Use background tasks for long-running operations
- Monitor and log performance metrics

When generating code for this project, ensure it follows these patterns and integrates well with the existing architecture.
