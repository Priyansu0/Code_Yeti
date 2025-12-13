"""
CodeYeti Code Chunker Module

This module handles intelligent code chunking using Python AST
for semantic parsing and regex for other file types.
"""

import ast
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from codeyeti.config.settings import settings


@dataclass
class CodeChunk:
    """
    Represents a chunk of code with metadata.
    
    Attributes:
        content: The code content
        chunk_type: Type of chunk (function, class, block, etc.)
        name: Name of the function/class if applicable
        start_line: Starting line number in original file
        end_line: Ending line number in original file
        docstring: Extracted docstring if available
    """
    content: str
    chunk_type: str
    name: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None


class CodeChunker:
    """
    Chunks code into logical segments using AST analysis for Python
    and regex-based chunking for other file types.
    """
    
    def __init__(self):
        """Initialize the CodeChunker with configuration."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def chunk_file(self, file_data: Dict[str, str]) -> List[Dict]:
        """
        Chunk a file into logical segments based on its type.
        
        Args:
            file_data: Dictionary with file content and metadata
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        extension = file_data.get('extension', '').lower()
        content = file_data.get('content', '')
        filename = file_data.get('filename', 'unknown')
        filepath = file_data.get('filepath', '')
        
        if extension == '.py':
            chunks = self._chunk_python(content)
        elif extension == '.md':
            chunks = self._chunk_markdown(content)
        else:
            chunks = self._chunk_text(content)
        
        result = []
        for idx, chunk in enumerate(chunks):
            result.append({
                'content': chunk.content,
                'chunk_type': chunk.chunk_type,
                'name': chunk.name,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'docstring': chunk.docstring,
                'filename': filename,
                'filepath': filepath,
                'chunk_id': f"{filename}_{idx}"
            })
        
        return result
    
    def _chunk_python(self, code: str) -> List[CodeChunk]:
        """
        Chunk Python code using AST analysis.
        
        Extracts functions, classes, and remaining blocks as separate chunks.
        
        Args:
            code: Python source code
            
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return self._chunk_text(code)
        
        extracted_ranges = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                start = node.lineno - 1
                end = node.end_lineno if hasattr(node, 'end_lineno') else start + 1
                
                func_code = '\n'.join(lines[start:end])
                docstring = ast.get_docstring(node)
                
                chunks.append(CodeChunk(
                    content=func_code,
                    chunk_type='function',
                    name=node.name,
                    start_line=start + 1,
                    end_line=end,
                    docstring=docstring
                ))
                extracted_ranges.append((start, end))
            
            elif isinstance(node, ast.ClassDef):
                start = node.lineno - 1
                end = node.end_lineno if hasattr(node, 'end_lineno') else start + 1
                
                class_code = '\n'.join(lines[start:end])
                docstring = ast.get_docstring(node)
                
                chunks.append(CodeChunk(
                    content=class_code,
                    chunk_type='class',
                    name=node.name,
                    start_line=start + 1,
                    end_line=end,
                    docstring=docstring
                ))
                extracted_ranges.append((start, end))
        
        if not chunks:
            return self._chunk_text(code)
        
        remaining_lines = []
        current_block = []
        current_start = 0
        
        for i, line in enumerate(lines):
            in_extracted = any(start <= i < end for start, end in extracted_ranges)
            
            if not in_extracted and line.strip():
                if not current_block:
                    current_start = i
                current_block.append(line)
            elif current_block:
                block_content = '\n'.join(current_block)
                if len(block_content.strip()) > 10:
                    chunks.append(CodeChunk(
                        content=block_content,
                        chunk_type='block',
                        name='code_block',
                        start_line=current_start + 1,
                        end_line=i,
                        docstring=None
                    ))
                current_block = []
        
        if current_block:
            block_content = '\n'.join(current_block)
            if len(block_content.strip()) > 10:
                chunks.append(CodeChunk(
                    content=block_content,
                    chunk_type='block',
                    name='code_block',
                    start_line=current_start + 1,
                    end_line=len(lines),
                    docstring=None
                ))
        
        chunks.sort(key=lambda x: x.start_line)
        return chunks
    
    def _chunk_markdown(self, content: str) -> List[CodeChunk]:
        """
        Chunk Markdown content by headers and code blocks.
        
        Args:
            content: Markdown content
            
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        lines = content.split('\n')
        
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        code_block_pattern = re.compile(r'^```')
        
        current_chunk = []
        current_start = 0
        current_name = 'document'
        in_code_block = False
        
        for i, line in enumerate(lines):
            if code_block_pattern.match(line):
                in_code_block = not in_code_block
                current_chunk.append(line)
                continue
            
            if not in_code_block:
                header_match = header_pattern.match(line)
                if header_match:
                    if current_chunk:
                        chunk_content = '\n'.join(current_chunk)
                        if chunk_content.strip():
                            chunks.append(CodeChunk(
                                content=chunk_content,
                                chunk_type='section',
                                name=current_name,
                                start_line=current_start + 1,
                                end_line=i,
                                docstring=None
                            ))
                    current_chunk = [line]
                    current_start = i
                    current_name = header_match.group(2)
                    continue
            
            current_chunk.append(line)
        
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content,
                    chunk_type='section',
                    name=current_name,
                    start_line=current_start + 1,
                    end_line=len(lines),
                    docstring=None
                ))
        
        return chunks if chunks else self._chunk_text(content)
    
    def _chunk_text(self, content: str) -> List[CodeChunk]:
        """
        Chunk plain text by size with overlap.
        
        Args:
            content: Text content
            
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        lines = content.split('\n')
        
        chunk_lines = self.chunk_size // 50
        overlap_lines = self.chunk_overlap // 50
        
        i = 0
        chunk_num = 0
        
        while i < len(lines):
            end = min(i + chunk_lines, len(lines))
            chunk_content = '\n'.join(lines[i:end])
            
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content,
                    chunk_type='text',
                    name=f'chunk_{chunk_num}',
                    start_line=i + 1,
                    end_line=end,
                    docstring=None
                ))
                chunk_num += 1
            
            i = end - overlap_lines if end < len(lines) else end
        
        return chunks
    
    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunked content.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with chunk statistics
        """
        stats = {
            'total_chunks': len(chunks),
            'by_type': {},
            'avg_size': 0
        }
        
        total_size = 0
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            if chunk_type not in stats['by_type']:
                stats['by_type'][chunk_type] = 0
            stats['by_type'][chunk_type] += 1
            total_size += len(chunk.get('content', ''))
        
        if chunks:
            stats['avg_size'] = total_size // len(chunks)
        
        return stats
