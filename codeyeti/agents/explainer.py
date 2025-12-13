"""
CodeYeti Code Explainer Module

This module provides learning-focused code explanations using
local LLM, with adaptive detail based on code length.
"""

from typing import Dict, Optional
import ollama

from codeyeti.config.settings import settings
from codeyeti.utils.helpers import count_lines, is_short_code


class CodeExplainer:
    """
    Generates beginner-friendly code explanations.
    
    Adapts explanation style based on code length:
    - Short code (<=30 lines): Full code + line-by-line explanation
    - Long code (>30 lines): High-level overview + key components
    """
    
    def __init__(self):
        """Initialize the CodeExplainer with LLM settings."""
        self.llm_model = settings.llm_model
        self.threshold = settings.short_code_threshold
    
    def explain(self, code: str, language: str = "python") -> Dict:
        """
        Generate an explanation for code.
        
        Args:
            code: Source code to explain
            language: Programming language (default: python)
            
        Returns:
            Dictionary with explanation and metadata
        """
        line_count = count_lines(code)
        is_short = is_short_code(code)
        
        if is_short:
            explanation = self._explain_short_code(code, language)
            explanation_type = "detailed"
        else:
            explanation = self._explain_long_code(code, language)
            explanation_type = "overview"
        
        return {
            'explanation': explanation,
            'explanation_type': explanation_type,
            'line_count': line_count,
            'is_short_code': is_short,
            'code': code
        }
    
    def _explain_short_code(self, code: str, language: str) -> str:
        """
        Generate detailed line-by-line explanation for short code.
        
        Args:
            code: Source code (<=30 lines)
            language: Programming language
            
        Returns:
            Detailed explanation string
        """
        prompt = f"""You are CodeYeti, a friendly coding teacher. Explain this {language} code in a way that helps a beginner understand it completely.

CODE:
```{language}
{code}
```

Provide:
1. A simple, beginner-friendly overview of what this code does (2-3 sentences)
2. A line-by-line explanation where each important line is explained simply
3. Key concepts used in this code

Use simple language. Avoid jargon. Be encouraging and educational.

EXPLANATION:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 1500
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Could not generate explanation: {str(e)}. Please ensure Ollama is running."
    
    def _explain_long_code(self, code: str, language: str) -> str:
        """
        Generate high-level overview for long code.
        
        Args:
            code: Source code (>30 lines)
            language: Programming language
            
        Returns:
            High-level explanation string
        """
        prompt = f"""You are CodeYeti, a friendly coding teacher. This code is longer than 30 lines, so provide a high-level overview to avoid cognitive overload.

CODE:
```{language}
{code}
```

Provide:
1. Purpose: What does this code accomplish? (2-3 sentences)
2. Main Components: List the key functions/classes and what each does (brief bullet points)
3. Flow: How does the code work at a high level? (3-4 sentences)
4. Key Concepts: What programming concepts are used? (brief list)

Keep it concise and beginner-friendly. Don't explain every line - focus on the big picture.

OVERVIEW:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 1000
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Could not generate explanation: {str(e)}. Please ensure Ollama is running."
    
    def explain_concept(self, concept: str) -> str:
        """
        Explain a programming concept.
        
        Args:
            concept: Programming concept to explain
            
        Returns:
            Explanation of the concept
        """
        prompt = f"""You are CodeYeti, a friendly coding teacher. Explain this programming concept in simple terms:

CONCEPT: {concept}

Provide:
1. Simple definition (1-2 sentences)
2. Why it's useful (1-2 sentences)
3. Simple code example in Python
4. Common use cases (brief list)

Keep it beginner-friendly and practical.

EXPLANATION:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 800
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Could not generate explanation: {str(e)}. Please ensure Ollama is running."
    
    def get_line_explanation(self, code: str, line_number: int) -> str:
        """
        Explain a specific line of code.
        
        Args:
            code: Full source code
            line_number: Line number to explain (1-indexed)
            
        Returns:
            Explanation of the specific line
        """
        lines = code.split('\n')
        if line_number < 1 or line_number > len(lines):
            return f"Invalid line number. Code has {len(lines)} lines."
        
        target_line = lines[line_number - 1]
        context_start = max(0, line_number - 3)
        context_end = min(len(lines), line_number + 2)
        context = '\n'.join(lines[context_start:context_end])
        
        prompt = f"""Explain line {line_number} of this code in simple terms:

CONTEXT:
```python
{context}
```

TARGET LINE (line {line_number}):
{target_line}

Provide a clear, beginner-friendly explanation of what this line does and why.

EXPLANATION:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 300
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"
