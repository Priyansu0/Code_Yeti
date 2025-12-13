"""
CodeYeti Utility Functions

This module provides helper functions used across the application
for code processing, validation, and formatting.
"""

import re
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from codeyeti.config.settings import settings


def count_lines(code: str) -> int:
    """
    Count the number of non-empty lines in code.
    
    Args:
        code: The source code string
        
    Returns:
        Number of non-empty lines
    """
    if not code or not code.strip():
        return 0
    lines = [line for line in code.split('\n') if line.strip()]
    return len(lines)


def is_short_code(code: str) -> bool:
    """
    Determine if code is short (<=30 lines) or long (>30 lines).
    
    Args:
        code: The source code string
        
    Returns:
        True if code has 30 or fewer lines, False otherwise
    """
    return count_lines(code) <= settings.short_code_threshold


def sanitize_code(code: str) -> str:
    """
    Sanitize code by removing potentially dangerous constructs.
    
    Args:
        code: The source code string
        
    Returns:
        Sanitized code string
    """
    dangerous_patterns = [
        r'import\s+os\s*;\s*os\.system',
        r'__import__\s*\(',
        r'exec\s*\(',
        r'eval\s*\(',
        r'compile\s*\(',
        r'open\s*\([^)]*["\']w["\']',
        r'subprocess',
        r'shutil\.rmtree',
        r'os\.remove',
        r'os\.unlink',
    ]
    
    warnings = []
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            warnings.append(f"Warning: Potentially dangerous pattern detected: {pattern}")
    
    return code, warnings


def extract_code_blocks(text: str) -> List[str]:
    """
    Extract code blocks from markdown-formatted text.
    
    Args:
        text: Text containing markdown code blocks
        
    Returns:
        List of extracted code strings
    """
    pattern = r'```(?:python)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches if matches else [text]


def format_error_message(error: Exception) -> str:
    """
    Format an exception into a readable error message.
    
    Args:
        error: The exception object
        
    Returns:
        Formatted error message string
    """
    error_type = type(error).__name__
    error_msg = str(error)
    return f"**{error_type}**: {error_msg}"


def get_file_extension(filepath: str) -> str:
    """
    Get the file extension from a filepath.
    
    Args:
        filepath: Path to the file
        
    Returns:
        File extension including the dot (e.g., '.py')
    """
    return os.path.splitext(filepath)[1].lower()


def is_supported_file(filepath: str) -> bool:
    """
    Check if a file has a supported extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file extension is supported, False otherwise
    """
    ext = get_file_extension(filepath)
    return ext in settings.supported_extensions


def create_metadata(
    filename: str,
    filepath: str,
    chunk_id: int,
    chunk_type: str = "code",
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create metadata dictionary for a code chunk.
    
    Args:
        filename: Name of the source file
        filepath: Full path to the source file
        chunk_id: Unique identifier for the chunk
        chunk_type: Type of chunk (function, class, block, etc.)
        extra: Additional metadata to include
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "filename": filename,
        "filepath": filepath,
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "indexed_at": datetime.now().isoformat()
    }
    
    if extra:
        metadata.update(extra)
    
    return metadata


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to a maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def clean_llm_response(response: str) -> str:
    """
    Clean and format LLM response text.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned response text
    """
    response = response.strip()
    response = re.sub(r'\n{3,}', '\n\n', response)
    return response
