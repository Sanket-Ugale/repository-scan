"""
Helper utilities and common functions.

This module contains utility functions that are used
across the AI Code Review Agent application.
"""
import hashlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.core.config import get_settings


def generate_task_id(repo_url: str, pr_number: Optional[int] = None) -> str:
    """
    Generate a unique task ID for analysis.
    
    Args:
        repo_url: GitHub repository URL
        pr_number: Pull request number (optional)
        
    Returns:
        str: Unique task ID
    """
    if pr_number is not None:
        content = f"{repo_url}#{pr_number}"
    else:
        content = f"{repo_url}#repo_scan"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse GitHub repository URL to extract owner and repo name.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Optional[Dict[str, str]]: Dict with 'owner' and 'repo' keys if valid,
                                 None otherwise
    """
    # Handle various GitHub URL formats
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+)',
        r'git@github\.com:([^/]+)/([^/]+)\.git',
        r'https://github\.com/([^/]+)/([^/]+)\.git'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            # Remove .git suffix if present
            repo = repo.rstrip('.git')
            return {"owner": owner, "repo": repo}
    
    return None


def sanitize_github_url(url: str) -> Optional[str]:
    """
    Sanitize and validate GitHub repository URL.
    
    Args:
        url: GitHub repository URL to sanitize
        
    Returns:
        Optional[str]: Sanitized URL if valid, None otherwise
    """
    parsed = parse_github_url(url)
    if not parsed:
        return None
    
    # Return canonical HTTPS format
    return f"https://github.com/{parsed['owner']}/{parsed['repo']}"


def validate_pr_number(pr_number: Any) -> bool:
    """
    Validate that PR number is a positive integer.
    
    Args:
        pr_number: PR number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        num = int(pr_number)
        return num > 0
    except (ValueError, TypeError):
        return False


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: File name
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    if '.' not in filename:
        return ''
    
    return filename.split('.')[-1].lower()


def get_programming_language(filename: str) -> str:
    """
    Determine programming language from filename.
    
    Args:
        filename: File name
        
    Returns:
        str: Programming language name
    """
    extension_map = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'jsx': 'javascript',
        'tsx': 'typescript',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'cs': 'csharp',
        'go': 'go',
        'rs': 'rust',
        'rb': 'ruby',
        'php': 'php',
        'swift': 'swift',
        'kt': 'kotlin',
        'scala': 'scala',
        'sh': 'shell',
        'bash': 'shell',
        'zsh': 'shell',
        'sql': 'sql',
        'yml': 'yaml',
        'yaml': 'yaml',
        'json': 'json',
        'xml': 'xml',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'sass': 'sass',
        'md': 'markdown',
        'rst': 'restructuredtext',
        'dockerfile': 'dockerfile',
    }
    
    extension = extract_file_extension(filename)
    return extension_map.get(extension, 'text')


def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for LLM processing.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a natural boundary (newline or space)
        if end < len(text):
            # Look for newline within the last 100 characters
            newline_pos = text.rfind('\n', start, end)
            if newline_pos > start + chunk_size - 100:
                end = newline_pos
            else:
                # Look for space within the last 50 characters
                space_pos = text.rfind(' ', start, end)
                if space_pos > start + chunk_size - 50:
                    end = space_pos
        
        chunks.append(text[start:end])
        start = end - overlap
        
        if start >= len(text):
            break
    
    return chunks


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_text_file(filename: str) -> bool:
    """
    Determine if a file is likely a text file based on extension.
    
    Args:
        filename: File name
        
    Returns:
        bool: True if likely a text file, False otherwise
    """
    text_extensions = {
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'cs', 'go', 'rs',
        'rb', 'php', 'swift', 'kt', 'scala', 'sh', 'bash', 'zsh', 'sql',
        'yml', 'yaml', 'json', 'xml', 'html', 'css', 'scss', 'sass', 'md',
        'rst', 'txt', 'dockerfile', 'gitignore', 'conf', 'cfg', 'ini'
    }
    
    extension = extract_file_extension(filename)
    return extension in text_extensions or filename.startswith('.')


def mask_sensitive_data(data: str, patterns: Optional[List[str]] = None) -> str:
    """
    Mask sensitive data in strings for logging.
    
    Args:
        data: String that may contain sensitive data
        patterns: Additional regex patterns to mask
        
    Returns:
        str: String with sensitive data masked
    """
    # Default patterns for common sensitive data
    default_patterns = [
        r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64 encoded data
        r'[a-fA-F0-9]{32,}',  # Hex encoded data (API keys, tokens)
        r'(?i)(token|key|secret|password)[\s]*[=:]+[\s]*[\'"]?([^\s\'"]+)',
    ]
    
    if patterns:
        default_patterns.extend(patterns)
    
    masked_data = data
    for pattern in default_patterns:
        masked_data = re.sub(pattern, '[MASKED]', masked_data)
    
    return masked_data
