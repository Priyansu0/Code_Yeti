"""
CodeYeti File Loader Module

This module handles loading and reading files from the filesystem.
Supports Python (.py), Text (.txt), and Markdown (.md) files.
"""

import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from codeyeti.config.settings import settings
from codeyeti.utils.helpers import is_supported_file, get_file_extension


class FileLoader:
    """
    Handles loading files from disk for code ingestion.
    
    Supports individual files and recursive folder loading
    with filtering for supported file types.
    """
    
    def __init__(self):
        """Initialize the FileLoader with supported extensions."""
        self.supported_extensions = settings.supported_extensions
    
    def load_file(self, filepath: str) -> Optional[Dict[str, str]]:
        """
        Load a single file and return its contents with metadata.
        
        Args:
            filepath: Path to the file to load
            
        Returns:
            Dictionary with 'content', 'filename', 'filepath', 'extension'
            or None if file cannot be loaded
        """
        try:
            if not os.path.exists(filepath):
                return None
            
            if not is_supported_file(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                'content': content,
                'filename': os.path.basename(filepath),
                'filepath': os.path.abspath(filepath),
                'extension': get_file_extension(filepath)
            }
        except Exception as e:
            print(f"Error loading file {filepath}: {e}")
            return None
    
    def load_folder(self, folder_path: str, recursive: bool = True) -> List[Dict[str, str]]:
        """
        Load all supported files from a folder.
        
        Args:
            folder_path: Path to the folder to load
            recursive: Whether to recursively load subfolders
            
        Returns:
            List of dictionaries with file contents and metadata
        """
        loaded_files = []
        
        if not os.path.exists(folder_path):
            return loaded_files
        
        if not os.path.isdir(folder_path):
            result = self.load_file(folder_path)
            if result:
                loaded_files.append(result)
            return loaded_files
        
        path = Path(folder_path)
        pattern = '**/*' if recursive else '*'
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and is_supported_file(str(file_path)):
                result = self.load_file(str(file_path))
                if result:
                    loaded_files.append(result)
        
        return loaded_files
    
    def load_uploaded_files(self, uploaded_files: List) -> List[Dict[str, str]]:
        """
        Load files from Streamlit uploaded file objects.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            
        Returns:
            List of dictionaries with file contents and metadata
        """
        loaded_files = []
        
        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                filename = uploaded_file.name
                extension = get_file_extension(filename)
                
                if extension in self.supported_extensions:
                    loaded_files.append({
                        'content': content,
                        'filename': filename,
                        'filepath': filename,
                        'extension': extension
                    })
            except Exception as e:
                print(f"Error loading uploaded file {uploaded_file.name}: {e}")
        
        return loaded_files
    
    def get_file_stats(self, files: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Get statistics about loaded files.
        
        Args:
            files: List of loaded file dictionaries
            
        Returns:
            Dictionary with file statistics
        """
        stats = {
            'total_files': len(files),
            'total_lines': 0,
            'total_chars': 0,
            'by_extension': {}
        }
        
        for file_data in files:
            content = file_data['content']
            ext = file_data['extension']
            
            stats['total_lines'] += content.count('\n') + 1
            stats['total_chars'] += len(content)
            
            if ext not in stats['by_extension']:
                stats['by_extension'][ext] = 0
            stats['by_extension'][ext] += 1
        
        return stats
