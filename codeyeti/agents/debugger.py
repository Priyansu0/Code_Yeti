"""
CodeYeti Debug Agent Module

This module provides intelligent debugging assistance,
analyzing errors and generating fix suggestions.
"""

from typing import Dict, Optional
import ollama

from codeyeti.config.settings import settings
from codeyeti.runner.python_runner import ExecutionResult


class DebugAgent:
    """
    Intelligent debugging assistant for code errors.
    
    Analyzes execution errors, traces root causes,
    and provides step-by-step fix suggestions.
    """
    
    def __init__(self):
        """Initialize the DebugAgent with LLM settings."""
        self.llm_model = settings.llm_model
    
    def analyze_error(
        self,
        code: str,
        result: ExecutionResult
    ) -> Dict:
        """
        Analyze an execution error and provide debugging help.
        
        Args:
            code: The original code that was executed
            result: ExecutionResult from the failed execution
            
        Returns:
            Dictionary with error analysis and fix suggestions
        """
        if result.success:
            return {
                'has_error': False,
                'message': "Code executed successfully. No errors to debug."
            }
        
        analysis = self._get_llm_analysis(code, result)
        
        return {
            'has_error': True,
            'error_type': self._extract_error_type(result.error),
            'error_message': result.error,
            'traceback': result.traceback_str,
            'analysis': analysis.get('cause', ''),
            'location': analysis.get('location', ''),
            'fix_explanation': analysis.get('fix_explanation', ''),
            'suggested_fix': analysis.get('suggested_code', ''),
            'original_code': code
        }
    
    def _get_llm_analysis(self, code: str, result: ExecutionResult) -> Dict:
        """
        Get LLM-powered error analysis.
        
        Args:
            code: Original code
            result: Execution result with error
            
        Returns:
            Dictionary with analysis components
        """
        prompt = f"""You are CodeYeti, an expert debugging assistant. Analyze this Python code error.

ORIGINAL CODE:
```python
{code}
```

ERROR MESSAGE:
{result.error}

TRACEBACK:
{result.traceback_str if result.traceback_str else 'Not available'}

Provide a structured analysis with these exact sections:

**CAUSE:**
Explain what caused this error in simple terms (1-2 sentences).

**LOCATION:**
Identify the exact line or area where the error occurs.

**FIX EXPLANATION:**
Step-by-step explanation of how to fix this error.

**SUGGESTED FIX:**
```python
[Provide the corrected code here]
```

Keep explanations clear and beginner-friendly."""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 1500
                }
            )
            
            return self._parse_analysis_response(response['response'])
        except Exception as e:
            return {
                'cause': f"Could not get LLM analysis: {str(e)}",
                'location': 'Unknown',
                'fix_explanation': 'Please ensure Ollama is running.',
                'suggested_code': code
            }
    
    def _parse_analysis_response(self, response: str) -> Dict:
        """
        Parse the structured LLM response.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Dictionary with parsed sections
        """
        result = {
            'cause': '',
            'location': '',
            'fix_explanation': '',
            'suggested_code': ''
        }
        
        import re
        
        cause_match = re.search(
            r'\*\*CAUSE:\*\*\s*(.*?)(?=\*\*LOCATION:|$)',
            response, re.DOTALL | re.IGNORECASE
        )
        if cause_match:
            result['cause'] = cause_match.group(1).strip()
        
        location_match = re.search(
            r'\*\*LOCATION:\*\*\s*(.*?)(?=\*\*FIX|$)',
            response, re.DOTALL | re.IGNORECASE
        )
        if location_match:
            result['location'] = location_match.group(1).strip()
        
        fix_match = re.search(
            r'\*\*FIX EXPLANATION:\*\*\s*(.*?)(?=\*\*SUGGESTED|```|$)',
            response, re.DOTALL | re.IGNORECASE
        )
        if fix_match:
            result['fix_explanation'] = fix_match.group(1).strip()
        
        code_match = re.search(
            r'```python\s*(.*?)```',
            response, re.DOTALL
        )
        if code_match:
            result['suggested_code'] = code_match.group(1).strip()
        
        return result
    
    def _extract_error_type(self, error_message: Optional[str]) -> str:
        """
        Extract the error type from an error message.
        
        Args:
            error_message: Full error message
            
        Returns:
            Error type name
        """
        if not error_message:
            return "Unknown"
        
        parts = error_message.split(':', 1)
        return parts[0].strip() if parts else "Unknown"
    
    def suggest_quick_fixes(self, code: str, error_type: str) -> list:
        """
        Suggest quick fixes based on common error patterns.
        
        Args:
            code: The code with error
            error_type: Type of error
            
        Returns:
            List of quick fix suggestions
        """
        quick_fixes = {
            'NameError': [
                "Check variable spelling",
                "Ensure variable is defined before use",
                "Check if you need to import a module"
            ],
            'TypeError': [
                "Check argument types match function expectations",
                "Verify you're not mixing incompatible types",
                "Check if you're calling the function correctly"
            ],
            'SyntaxError': [
                "Check for missing colons after if/for/def/class",
                "Verify matching parentheses/brackets/quotes",
                "Check indentation is consistent"
            ],
            'IndentationError': [
                "Use consistent spaces (4 spaces recommended)",
                "Don't mix tabs and spaces",
                "Check nested blocks have proper indentation"
            ],
            'IndexError': [
                "Check list/array length before accessing",
                "Remember indices start at 0",
                "Use len() to verify bounds"
            ],
            'KeyError': [
                "Use .get() method with default value",
                "Check if key exists with 'in' operator",
                "Verify dictionary keys match exactly"
            ],
            'AttributeError': [
                "Check object type with type()",
                "Verify method/attribute name spelling",
                "Ensure object is initialized properly"
            ],
            'ImportError': [
                "Verify module is installed (pip install)",
                "Check import path is correct",
                "Verify module name spelling"
            ],
            'ZeroDivisionError': [
                "Add check: if divisor != 0",
                "Handle edge case with try/except",
                "Validate input before division"
            ],
            'ValueError': [
                "Validate input format before processing",
                "Use try/except for type conversions",
                "Check input range/constraints"
            ]
        }
        
        return quick_fixes.get(error_type, [
            "Review the error message carefully",
            "Check the line number in traceback",
            "Add print statements to debug"
        ])
    
    def format_debug_report(self, analysis: Dict) -> str:
        """
        Format the debug analysis as a readable report.
        
        Args:
            analysis: Analysis dictionary from analyze_error
            
        Returns:
            Formatted report string
        """
        if not analysis.get('has_error'):
            return "No errors to report. Code executed successfully!"
        
        report = []
        report.append("## Debug Report")
        report.append("")
        report.append(f"**Error Type:** {analysis.get('error_type', 'Unknown')}")
        report.append(f"**Error Message:** {analysis.get('error_message', 'No message')}")
        report.append("")
        
        if analysis.get('location'):
            report.append(f"**Location:** {analysis['location']}")
            report.append("")
        
        if analysis.get('analysis'):
            report.append("### Cause")
            report.append(analysis['analysis'])
            report.append("")
        
        if analysis.get('fix_explanation'):
            report.append("### How to Fix")
            report.append(analysis['fix_explanation'])
            report.append("")
        
        if analysis.get('suggested_fix'):
            report.append("### Suggested Fix")
            report.append("```python")
            report.append(analysis['suggested_fix'])
            report.append("```")
        
        return '\n'.join(report)
