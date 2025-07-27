import base64
from typing import Dict, List, Optional, Any

import structlog

# Optional GitHub API import
try:
    from github import Github, PullRequest, Repository
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception

from app.core.config import get_settings
from app.utils.helpers import parse_github_url, is_text_file, format_file_size

logger = structlog.get_logger(__name__)


class GitHubService:
    def __init__(self):
        """Initialize GitHub service with API client."""
        self.logger = logger.bind(service="github")
        
        if not GITHUB_AVAILABLE:
            self.logger.error("PyGithub not available - install with: pip install PyGithub")
            self.github = None
            return
            
        settings = get_settings()
        github_token = settings.GITHUB_TOKEN
        
        # Debug logging
        self.logger.info(f"GitHub token value: '{github_token}', type: {type(github_token)}")
        
        # Check if token is valid (not None and not empty string)
        if github_token and github_token.strip():
            self.github = Github(github_token)
            self.logger.info("GitHub client initialized with authentication token")
        else:
            # Create unauthenticated client for public repositories
            self.github = Github()
            self.logger.warning("GitHub token not configured - using unauthenticated access with rate limits")
    
    async def check_pr_exists(self, repo_url: str, pr_number: int) -> bool:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return False
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return False
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            pr = repo.get_pull(pr_number)
            
            self.logger.info(
                "PR exists and is accessible",
                repo_url=repo_url,
                pr_number=pr_number,
                pr_title=pr.title
            )
            return True
            
        except GithubException as e:
            self.logger.warning(
                "PR not found or not accessible",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return False
        except Exception as e:
            self.logger.error(
                "Error checking PR existence",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return False
    
    async def get_pull_request_info(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return None
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return None
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            pr = repo.get_pull(pr_number)
            
            pr_info = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "base_sha": pr.base.sha,
                "head_sha": pr.head.sha,
                "commits": pr.commits,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "mergeable": pr.mergeable,
                "draft": pr.draft,
                "labels": [label.name for label in pr.labels],
                "assignees": [assignee.login for assignee in pr.assignees],
                "reviewers": [reviewer.login for reviewer in pr.requested_reviewers],
                "html_url": pr.html_url
            }
            
            self.logger.info(
                "PR information retrieved",
                repo_url=repo_url,
                pr_number=pr_number,
                title=pr.title,
                changed_files=pr.changed_files
            )
            
            return pr_info
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR information",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting PR information",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return None
    
    async def get_pull_request_files(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return []
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return []
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                file_info = {
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed, renamed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') else None,
                    "sha": file.sha,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "contents_url": file.contents_url,
                    "is_text_file": is_text_file(file.filename)
                }
                
                # Add previous filename for renamed files
                if hasattr(file, 'previous_filename') and file.previous_filename:
                    file_info["previous_filename"] = file.previous_filename
                
                files.append(file_info)
            
            self.logger.info(
                "PR files retrieved",
                repo_url=repo_url,
                pr_number=pr_number,
                file_count=len(files)
            )
            
            return files
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR files",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return []
        except Exception as e:
            self.logger.error(
                "Unexpected error getting PR files",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return []
    
    async def get_file_content(
        self, 
        repo_url: str, 
        file_path: str, 
        ref: str = "main"
    ) -> Optional[str]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return None
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return None
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            
            # Get file content
            file_content = repo.get_contents(file_path, ref=ref)
            
            if file_content.encoding == "base64":
                content = base64.b64decode(file_content.content).decode('utf-8')
            else:
                content = file_content.content
            
            self.logger.debug(
                "File content retrieved",
                repo_url=repo_url,
                file_path=file_path,
                ref=ref,
                size=len(content)
            )
            
            return content
            
        except GithubException as e:
            self.logger.warning(
                "Failed to get file content",
                repo_url=repo_url,
                file_path=file_path,
                ref=ref,
                error=str(e)
            )
            return None
        except UnicodeDecodeError as e:
            self.logger.warning(
                "File is not UTF-8 encoded",
                repo_url=repo_url,
                file_path=file_path,
                ref=ref,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting file content",
                repo_url=repo_url,
                file_path=file_path,
                ref=ref,
                error=str(e)
            )
            return None
    
    async def get_commit_diff(
        self, 
        repo_url: str, 
        base_sha: str, 
        head_sha: str
    ) -> Optional[str]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return None
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return None
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            
            # Get comparison between commits
            comparison = repo.compare(base_sha, head_sha)
            
            # Build diff content from files
            diff_parts = []
            for file in comparison.files:
                if hasattr(file, 'patch') and file.patch:
                    diff_parts.append(f"--- a/{file.filename}")
                    diff_parts.append(f"+++ b/{file.filename}")
                    diff_parts.append(file.patch)
                    diff_parts.append("")  # Empty line separator
            
            diff_content = "\n".join(diff_parts)
            
            self.logger.info(
                "Commit diff retrieved",
                repo_url=repo_url,
                base_sha=base_sha[:8],
                head_sha=head_sha[:8],
                files_changed=len(comparison.files)
            )
            
            return diff_content
            
        except GithubException as e:
            self.logger.error(
                "Failed to get commit diff",
                repo_url=repo_url,
                base_sha=base_sha[:8],
                head_sha=head_sha[:8],
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting commit diff",
                repo_url=repo_url,
                base_sha=base_sha[:8],
                head_sha=head_sha[:8],
                error=str(e)
            )
            return None
    
    async def get_repository_info(self, repo_url: str) -> Optional[Dict[str, Any]]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return None
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return None
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            
            repo_data = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "languages": dict(repo.get_languages()),
                "default_branch": repo.default_branch,
                "size": repo.size,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "private": repo.private,
                "fork": repo.fork,
                "archived": repo.archived,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "topics": repo.get_topics()
            }
            
            self.logger.info(
                "Repository information retrieved",
                repo_url=repo_url,
                name=repo.name,
                language=repo.language
            )
            
            return repo_data
            
        except GithubException as e:
            self.logger.error(
                "Failed to get repository information",
                repo_url=repo_url,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting repository information",
                repo_url=repo_url,
                error=str(e)
            )
            return None

    async def get_repo_files(self, repo_url: str, ref: str = None, max_files: int = 100) -> List[Dict[str, Any]]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return []

        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return []

            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            
            # Use repository's default branch if no ref specified
            if ref is None:
                ref = repo.default_branch
                self.logger.info(f"Using repository default branch: {ref}")

            files = []
            file_count = 0
            
            def process_contents(contents, path_prefix=""):
                nonlocal file_count
                for content in contents:
                    if file_count >= max_files:
                        break
                    
                    full_path = f"{path_prefix}/{content.name}" if path_prefix else content.name
                    
                    if content.type == "file":
                        # Only include analyzable files
                        if self._is_analyzable_file(full_path):
                            files.append({
                                "filename": full_path,
                                "path": content.path,
                                "sha": content.sha,
                                "size": content.size,
                                "download_url": content.download_url,
                                "type": "file"
                            })
                            file_count += 1
                    elif content.type == "dir" and file_count < max_files:
                        # Recursively process directories (up to a reasonable depth)
                        if full_path.count('/') < 5:  # Limit depth to avoid infinite recursion
                            try:
                                dir_contents = repo.get_contents(content.path, ref=ref)
                                process_contents(dir_contents, content.path)
                            except Exception as e:
                                self.logger.warning(
                                    "Failed to process directory",
                                    directory=content.path,
                                    error=str(e)
                                )
            
            # Start processing from root
            root_contents = repo.get_contents("", ref=ref)
            process_contents(root_contents)
            
            self.logger.info(
                "Repository files retrieved",
                repo_url=repo_url,
                ref=ref,
                file_count=len(files)
            )
            
            return files
            
        except GithubException as e:
            self.logger.error(
                "Failed to get repository files",
                repo_url=repo_url,
                ref=ref,
                error=str(e)
            )
            return []
        except Exception as e:
            self.logger.error(
                "Unexpected error getting repository files",
                repo_url=repo_url,
                ref=ref,
                error=str(e)
            )
            return []
    
    def _is_analyzable_file(self, filename: str) -> bool:
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
        
        # Include README files (even without extensions)
        base_name = filename_lower.split('/')[-1]  # Get just the filename, not path
        if base_name.startswith('readme'):
            return True
        
        # Include other common documentation files
        doc_files = {'license', 'changelog', 'contributing', 'authors', 'contributors', 'notice'}
        if base_name in doc_files:
            return True
        
        return False

    async def get_pr_files(self, repo_url: str, pr_number: int) -> Optional[List[Dict[str, Any]]]:
        if not self.github:
            self.logger.error("GitHub client not initialized")
            return None
        
        try:
            repo_info = parse_github_url(repo_url)
            if not repo_info:
                return None
            
            repo = self.github.get_repo(f"{repo_info['owner']}/{repo_info['repo']}")
            pr = repo.get_pull(pr_number)
            
            # Get the list of files from the PR
            files = pr.get_files()
            
            file_list = []
            for file in files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed, renamed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch  # This contains the diff
                }
                
                # Only include files that have actual code changes
                if file.patch and is_text_file(file.filename):
                    file_list.append(file_info)
            
            self.logger.info(
                "PR files retrieved",
                repo_url=repo_url,
                pr_number=pr_number,
                total_files=len(file_list),
                changed_files=[f['filename'] for f in file_list[:5]]  # Log first 5 files
            )
            
            return file_list
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR files",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting PR files",
                repo_url=repo_url,
                pr_number=pr_number,
                error=str(e)
            )
            return None
