"""
CodeYeti Code Summarizer Module

This module provides file and project summarization capabilities,
extracting purpose, main logic, and key components.
"""

from typing import Dict, List, Optional
import ollama

from codeyeti.config.settings import settings
from codeyeti.rag.loader import FileLoader
from codeyeti.rag.chunker import CodeChunker


class CodeSummarizer:
    """
    Summarizes code files and entire projects.
    
    Provides concise overviews focusing on purpose,
    main logic, and key components.
    """
    
    def __init__(self):
        """Initialize the CodeSummarizer."""
        self.llm_model = settings.llm_model
        self.loader = FileLoader()
        self.chunker = CodeChunker()
    
    def summarize_code(self, code: str, filename: str = "code") -> Dict:
        """
        Summarize a single piece of code.
        
        Args:
            code: Source code to summarize
            filename: Name of the file (optional)
            
        Returns:
            Dictionary with summary information
        """
        prompt = f"""You are CodeYeti. Provide a concise summary of this code:

FILE: {filename}
```python
{code}
```

Provide:
1. **Purpose**: What this code does (1-2 sentences)
2. **Main Logic**: How it works (2-3 sentences)
3. **Key Components**: List of important functions/classes with brief descriptions
4. **Dependencies**: External modules or libraries used

Keep it concise and informative."""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 800
                }
            )
            
            return {
                'filename': filename,
                'summary': response['response'].strip(),
                'line_count': len(code.split('\n')),
                'char_count': len(code)
            }
        except Exception as e:
            return {
                'filename': filename,
                'summary': f"Could not generate summary: {str(e)}",
                'line_count': len(code.split('\n')),
                'char_count': len(code)
            }
    
    def summarize_file(self, file_data: Dict) -> Dict:
        """
        Summarize a loaded file.
        
        Args:
            file_data: Dictionary with file content and metadata
            
        Returns:
            Dictionary with file summary
        """
        return self.summarize_code(
            file_data.get('content', ''),
            file_data.get('filename', 'unknown')
        )
    
    def summarize_files(self, files: List[Dict]) -> Dict:
        """
        Summarize multiple files as a project.
        
        Args:
            files: List of file data dictionaries
            
        Returns:
            Dictionary with project summary
        """
        if not files:
            return {
                'project_summary': "No files to summarize.",
                'file_summaries': [],
                'stats': {'total_files': 0}
            }
        
        file_overviews = []
        total_lines = 0
        
        for file_data in files:
            filename = file_data.get('filename', 'unknown')
            content = file_data.get('content', '')
            lines = len(content.split('\n'))
            total_lines += lines
            
            chunks = self.chunker.chunk_file(file_data)
            components = []
            for chunk in chunks:
                if chunk['chunk_type'] in ['function', 'class']:
                    components.append(f"{chunk['chunk_type']}: {chunk['name']}")
            
            file_overviews.append({
                'filename': filename,
                'lines': lines,
                'components': components[:10]
            })
        
        project_summary = self._generate_project_summary(file_overviews)
        
        return {
            'project_summary': project_summary,
            'file_summaries': file_overviews,
            'stats': {
                'total_files': len(files),
                'total_lines': total_lines
            }
        }
    
    def _generate_project_summary(self, file_overviews: List[Dict]) -> str:
        """
        Generate an overall project summary.
        
        Args:
            file_overviews: List of file overview dictionaries
            
        Returns:
            Project summary string
        """
        files_info = []
        for fo in file_overviews[:10]:
            components = ', '.join(fo['components'][:5]) if fo['components'] else 'N/A'
            files_info.append(f"- {fo['filename']} ({fo['lines']} lines): {components}")
        
        files_str = '\n'.join(files_info)
        
        prompt = f"""You are CodeYeti. Provide a project summary based on these files:

FILES:
{files_str}

Provide:
1. **Project Purpose**: What this project appears to do (1-2 sentences)
2. **Architecture**: How the code is organized (2-3 sentences)
3. **Main Components**: Key files/modules and their roles
4. **Notable Patterns**: Any design patterns or notable approaches used

Keep it concise and high-level."""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 600
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Could not generate project summary: {str(e)}"
    
    def get_quick_summary(self, code: str) -> str:
        """
        Get a quick one-line summary of code.
        
        Args:
            code: Source code
            
        Returns:
            One-line summary string
        """
        prompt = f"""Summarize this code in ONE sentence (max 20 words):

```python
{code[:2000]}
```

SUMMARY:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.1,
                    'num_predict': 50
                }
            )
            return response['response'].strip()
        except Exception as e:
            return "Unable to generate summary."
    
    def extract_components(self, code: str) -> Dict:
        """
        Extract and list all components from code.
        
        Args:
            code: Python source code
            
        Returns:
            Dictionary with extracted components
        """
        file_data = {'content': code, 'filename': 'temp.py', 'extension': '.py'}
        chunks = self.chunker.chunk_file(file_data)
        
        components = {
            'functions': [],
            'classes': [],
            'imports': [],
            'blocks': []
        }
        
        import re
        import_pattern = re.compile(r'^(?:from\s+\S+\s+)?import\s+\S+', re.MULTILINE)
        imports = import_pattern.findall(code)
        components['imports'] = [imp.strip() for imp in imports]
        
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', '')
            name = chunk.get('name', '')
            docstring = chunk.get('docstring', '')
            
            item = {
                'name': name,
                'start_line': chunk.get('start_line', 0),
                'end_line': chunk.get('end_line', 0),
                'docstring': docstring[:200] if docstring else None
            }
            
            if chunk_type == 'function':
                components['functions'].append(item)
            elif chunk_type == 'class':
                components['classes'].append(item)
            elif chunk_type == 'block':
                components['blocks'].append(item)
        
        return components
