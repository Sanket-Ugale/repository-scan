from typing import Dict, Any, Optional
import asyncio
import time

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None

from app.core.config import get_settings
from app.services.task_manager import task_manager
from app.services.github import GitHubService
from app.services.llm import LLMService

if CELERY_AVAILABLE:
    settings = get_settings()
    celery_app = Celery(
        "ai_code_review",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=600,
    )

    @celery_app.task(bind=True, max_retries=3)
    def analyze_pr_task(self, task_id: str, repo_url: str, pr_number: Optional[int] = None, github_token: Optional[str] = None):
        """Analyze a GitHub pull request or repository asynchronously."""
        analysis_type = "pull request" if pr_number else "repository"
        logger.info(f"Starting {analysis_type} analysis task: {task_id}")
        
        try:
            return asyncio.run(analyze_pr_async(task_id, repo_url, pr_number, github_token))
        except Exception as e:
            logger.error(f"{analysis_type.title()} analysis task failed: {task_id}, error: {e}")
            asyncio.run(task_manager.update_task_status(
                task_id=task_id,
                status="failed",
                progress=0,
                message=f"Analysis failed: {str(e)}",
                error=str(e)
            ))
            raise
else:
    celery_app = None
    
    class MockCeleryTask:
        """Mock Celery task when Celery is not available."""
        def delay(self, task_id: str, repo_url: str, pr_number: Optional[int] = None, github_token: Optional[str] = None):
            analysis_type = "pull request" if pr_number else "repository"
            logger.warning(f"Celery not available - mock processing {analysis_type} task {task_id}")
            # Start a background thread to simulate task processing
            import threading
            import time
            
            def mock_process():
                try:
                    time.sleep(5)  # Simulate processing time for repo scan
                    
                    # Mock results in assignment format
                    mock_results = {
                        "files": [
                            {
                                "name": "main.py",
                                "issues": [
                                    {
                                        "type": "style",
                                        "line": 15,
                                        "description": "Line too long (>80 characters)",
                                        "suggestion": "Break line into multiple lines or use shorter variable names"
                                    },
                                    {
                                        "type": "bug",
                                        "line": 23,
                                        "description": "Potential null pointer exception",
                                        "suggestion": "Add null check before accessing object properties"
                                    }
                                ]
                            },
                            {
                                "name": "utils.py", 
                                "issues": [
                                    {
                                        "type": "performance",
                                        "line": 45,
                                        "description": "Inefficient loop operation",
                                        "suggestion": "Use list comprehension instead of explicit loop"
                                    }
                                ]
                            }
                        ],
                        "summary": {
                            "total_files": 2,
                            "total_issues": 3,
                            "critical_issues": 1
                        }
                    }
                    
                    asyncio.run(task_manager.update_task_status(
                        task_id=task_id,
                        status="completed",
                        progress=100,
                        message=f"Mock {analysis_type} analysis completed successfully",
                        result=mock_results
                    ))
                except Exception as e:
                    logger.error(f"Mock task failed: {e}")
                    asyncio.run(task_manager.update_task_status(
                        task_id=task_id,
                        status="failed",
                        progress=0,
                        error=str(e)
                    ))
            
            threading.Thread(target=mock_process, daemon=True).start()
            return {"task_id": task_id}
    
    analyze_pr_task = MockCeleryTask()

async def analyze_pr_async(task_id: str, repo_url: str, pr_number: Optional[int] = None, github_token: Optional[str] = None):
    """Async function to analyze PR or repository using real GitHub and LLM processing."""
    github_service = GitHubService()
    llm_service = LLMService()
    
    try:
        analysis_type = "pull request" if pr_number else "repository"
        
        if pr_number:
            # PR Analysis Flow
            await task_manager.update_task_status(
                task_id=task_id, status="processing", progress=10,
                message="Fetching pull request data from GitHub...")
            
            logger.info(f"Fetching PR data for {repo_url}/pull/{pr_number}")
            
            # Check if PR exists
            pr_exists = await github_service.check_pr_exists(repo_url, pr_number)
            if not pr_exists:
                raise Exception(f"Pull request not found: {repo_url}/pull/{pr_number}. Please check the URL and PR number.")
            
            # Get PR information
            pr_info = await github_service.get_pull_request_info(repo_url, pr_number)
            if not pr_info:
                raise Exception(f"Failed to fetch PR information for {repo_url}/pull/{pr_number}")
            
            logger.info(f"PR info retrieved: {pr_info['title']}, changed files: {pr_info['changed_files']}")
            
            # Get PR files with diffs
            await task_manager.update_task_status(
                task_id=task_id, status="processing", progress=25,
                message="Analyzing file changes and diffs...")
            
            pr_files = await github_service.get_pr_files(repo_url, pr_number)
            if not pr_files:
                raise Exception("No files found in the pull request")
            
            logger.info(f"Found {len(pr_files)} changed files")
            files_to_analyze = pr_files
            
        else:
            # Repository Scanning Flow
            await task_manager.update_task_status(
                task_id=task_id, status="processing", progress=10,
                message="Scanning repository structure...")
            
            logger.info(f"Scanning repository {repo_url}")
            
            # Get repository information
            repo_info = await github_service.get_repository_info(repo_url)
            if not repo_info:
                raise Exception(f"Failed to fetch repository information for {repo_url}")
            
            logger.info(f"Repository info retrieved: {repo_info.get('name', 'Unknown')}")
            
            # Step 2: Get repository files for scanning
            await task_manager.update_task_status(
                task_id=task_id, status="processing", progress=25,
                message="Fetching repository files for analysis...")
            
            # Get repository files
            repo_files = await github_service.get_repo_files(repo_url)
            if not repo_files:
                raise Exception("No files found in the repository")
            
            logger.info(f"Found {len(repo_files)} files to analyze")
            files_to_analyze = repo_files
        
        # Step 3: Analyze code with LLM
        await task_manager.update_task_status(
            task_id=task_id, status="processing", progress=50,
            message="Analyzing code with AI...")
        
        analyzed_files = []
        total_issues = 0
        critical_issues = 0
        
        # Process each file
        for i, file_info in enumerate(files_to_analyze):
            progress = 50 + (i * 30 // len(files_to_analyze))
            await task_manager.update_task_status(
                task_id=task_id, status="processing", progress=progress,
                message=f"Analyzing file: {file_info.get('filename', file_info.get('name', 'unknown'))}")
            
            filename = file_info.get('filename', file_info.get('name', ''))
            
            # Skip binary files and certain file types
            if not _is_analyzable_file(filename):
                continue
            
            logger.info(f"Analyzing file: {filename}")
            
            if pr_number:
                # For PR analysis, use diff content
                if not file_info.get('patch'):  # Skip files without code changes
                    continue
                
                file_content = await github_service.get_file_content(
                    repo_url, filename, pr_info['head_sha']
                )
                
                analysis_context = {
                    "filename": filename,
                    "diff": file_info['patch'],
                    "file_content": file_content,
                    "pr_title": pr_info['title'],
                    "pr_description": pr_info.get('body', ''),
                    "language": _detect_language(filename),
                    "analysis_type": "pr_diff"
                }
                
                # Analyze with LLM
                analysis_result = await llm_service.analyze_code_diff(
                    diff_content=file_info['patch'],
                    file_content=file_content,
                    filename=filename,
                    context=analysis_context
                )
            else:
                # For repository scanning, get full file content
                default_branch = repo_info.get('default_branch', 'main')
                file_content = await github_service.get_file_content(
                    repo_url, filename, ref=default_branch
                )
                
                if not file_content or len(file_content.strip()) == 0:
                    continue
                
                analysis_context = {
                    "filename": filename,
                    "file_content": file_content,
                    "language": _detect_language(filename),
                    "analysis_type": "full_file"
                }
                
                # Analyze with LLM for security vulnerabilities, code quality, etc.
                analysis_result = await llm_service.analyze_file_content(
                    file_content=file_content,
                    file_path=filename,
                    programming_language=_detect_language(filename),
                    analysis_type="comprehensive"
                )
            
            if analysis_result and (analysis_result.get('issues') or analysis_result.get('findings')):
                # Handle different response formats from LLM service
                issues = analysis_result.get('issues') or []
                if 'findings' in analysis_result and not issues:
                    # Convert findings to assignment format
                    issues = []
                    for finding in analysis_result['findings']:
                        issue = {
                            "type": finding.get('type', 'code_quality'),
                            "line": finding.get('line_number'),
                            "description": finding.get('description', ''),
                            "suggestion": finding.get('suggestion', '')
                        }
                        issues.append(issue)
                
                analyzed_files.append({
                    "name": filename,
                    "issues": issues
                })
                
                total_issues += len(issues)
                critical_issues += len([issue for issue in issues 
                                     if issue.get('severity') in ['critical', 'high'] or 
                                        issue.get('type') in ['security', 'bug']])
        
        # Step 4: Generate final report
        await task_manager.update_task_status(
            task_id=task_id, status="processing", progress=85,
            message="Generating comprehensive analysis report...")
        
        # Create summary in assignment format
        results = {
            "files": analyzed_files,
            "summary": {
                "total_files": len(analyzed_files),
                "total_issues": total_issues,
                "critical_issues": critical_issues
            }
        }
        
        if pr_number:
            results["pr_info"] = {
                "title": pr_info['title'],
                "author": pr_info['author'],
                "changed_files": pr_info['changed_files'],
                "additions": pr_info['additions'],
                "deletions": pr_info['deletions']
            }
        
        # Complete task
        await task_manager.update_task_status(
            task_id=task_id, status="completed", progress=100,
            message=f"{analysis_type.title()} analysis completed successfully", 
            result=results)
        
        logger.info(f"{analysis_type.title()} analysis completed: {task_id}, found {total_issues} issues across {len(analyzed_files)} files")
        return results
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"PR analysis failed for {task_id}: {e}", exc_info=True)
        await task_manager.update_task_status(
            task_id=task_id, status="failed", progress=0,
            message=error_msg, error=str(e))
        raise


def _detect_language(filename: str) -> str:
    """Detect programming language from filename."""
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'react',
        '.tsx': 'react',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.sql': 'sql',
        '.sh': 'bash',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.md': 'markdown'
    }
    
    for ext, lang in extension_map.items():
        if filename.lower().endswith(ext):
            return lang
    
    return 'text'


def _is_analyzable_file(filename: str) -> bool:
    """Check if file is analyzable (not binary, not too large, etc.)."""
    if not filename:
        return False
    
    # Skip common binary file extensions
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.exe', '.dll', '.so', '.dylib', '.a',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.ttf', '.otf', '.woff', '.woff2',
        '.db', '.sqlite', '.sqlite3'
    }
    
    filename_lower = filename.lower()
    for ext in binary_extensions:
        if filename_lower.endswith(ext):
            return False
    
    # Skip hidden files and directories
    if filename.startswith('.') and not filename.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml')):
        return False
    
    # Skip common non-source directories
    skip_patterns = [
        'node_modules/', '__pycache__/', '.git/', '.vscode/', '.idea/',
        'build/', 'dist/', 'target/', 'bin/', 'obj/', 'out/',
        'vendor/', 'deps/', 'coverage/', '.coverage/', '.pytest_cache/',
        'venv/', 'env/', '.env/'
    ]
    
    for pattern in skip_patterns:
        if pattern in filename:
            return False
    
    # Only analyze common source code file extensions
    source_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.sql', '.sh', '.bash', '.zsh', '.yml', '.yaml', '.json', '.xml',
        '.html', '.css', '.scss', '.less', '.md', '.txt', '.config', '.ini'
    }
    
    for ext in source_extensions:
        if filename_lower.endswith(ext):
            return True
    
    return False
