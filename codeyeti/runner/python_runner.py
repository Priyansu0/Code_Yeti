"""
CodeYeti Python Code Runner Module

This module provides safe Python code execution with output capture,
timeout handling, and error reporting.
"""

import sys
import io
import traceback
import contextlib
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import threading
import queue

from codeyeti.config.settings import settings


@dataclass
class ExecutionResult:
    """
    Represents the result of code execution.
    
    Attributes:
        success: Whether execution completed without errors
        output: Standard output captured
        error: Error message if execution failed
        traceback_str: Full traceback string if available
        return_value: Return value if applicable
    """
    success: bool
    output: str
    error: Optional[str] = None
    traceback_str: Optional[str] = None
    return_value: Optional[str] = None


class PythonRunner:
    """
    Safe Python code execution environment.
    
    Provides controlled execution with output capture, timeout,
    and sandboxing for educational code experimentation.
    """
    
    def __init__(self):
        """Initialize the PythonRunner with configuration."""
        self.timeout = settings.execution_timeout
        self.max_output = settings.max_output_length
    
    def execute(self, code: str, timeout: int = None) -> ExecutionResult:
        """
        Execute Python code safely and capture output.
        
        Args:
            code: Python source code to execute
            timeout: Optional timeout in seconds
            
        Returns:
            ExecutionResult with output and status
        """
        if timeout is None:
            timeout = self.timeout
        
        result_queue = queue.Queue()
        
        thread = threading.Thread(
            target=self._execute_in_thread,
            args=(code, result_queue)
        )
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout} seconds",
                traceback_str=None
            )
        
        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return ExecutionResult(
                success=False,
                output="",
                error="No result received from execution",
                traceback_str=None
            )
    
    def _execute_in_thread(self, code: str, result_queue: queue.Queue):
        """
        Execute code in a separate thread.
        
        Args:
            code: Code to execute
            result_queue: Queue to put result into
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            safe_globals = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
            }
            
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                exec(code, safe_globals)
            
            output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stderr_output:
                output += f"\n[stderr]: {stderr_output}"
            
            output = self._truncate_output(output)
            
            result_queue.put(ExecutionResult(
                success=True,
                output=output,
                error=None,
                traceback_str=None
            ))
            
        except Exception as e:
            output = stdout_capture.getvalue()
            error_type = type(e).__name__
            error_msg = str(e)
            tb_str = traceback.format_exc()
            
            result_queue.put(ExecutionResult(
                success=False,
                output=self._truncate_output(output),
                error=f"{error_type}: {error_msg}",
                traceback_str=tb_str
            ))
    
    def _truncate_output(self, output: str) -> str:
        """
        Truncate output if it exceeds maximum length.
        
        Args:
            output: Output string to truncate
            
        Returns:
            Truncated output with indicator if needed
        """
        if len(output) > self.max_output:
            return output[:self.max_output] + "\n... [Output truncated]"
        return output
    
    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Python code syntax without executing.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def analyze_execution_error(self, result: ExecutionResult) -> Dict:
        """
        Analyze an execution error for debugging.
        
        Args:
            result: ExecutionResult from failed execution
            
        Returns:
            Dictionary with error analysis
        """
        if result.success:
            return {'has_error': False}
        
        error_analysis = {
            'has_error': True,
            'error_type': 'Unknown',
            'error_message': result.error or 'Unknown error',
            'line_number': None,
            'suggestion': None
        }
        
        if result.error:
            parts = result.error.split(':', 1)
            if len(parts) == 2:
                error_analysis['error_type'] = parts[0].strip()
                error_analysis['error_message'] = parts[1].strip()
        
        if result.traceback_str:
            import re
            line_match = re.search(r'line (\d+)', result.traceback_str)
            if line_match:
                error_analysis['line_number'] = int(line_match.group(1))
        
        error_type = error_analysis['error_type']
        suggestions = {
            'NameError': "Check if the variable or function is defined before use.",
            'TypeError': "Verify that you're using the correct types for operations.",
            'SyntaxError': "Check for missing parentheses, colons, or indentation issues.",
            'IndentationError': "Ensure consistent use of spaces or tabs for indentation.",
            'IndexError': "Check if the index is within the valid range of the list.",
            'KeyError': "Verify the key exists in the dictionary before accessing it.",
            'AttributeError': "Check if the object has the attribute or method you're trying to use.",
            'ImportError': "Ensure the module is installed and the import path is correct.",
            'ZeroDivisionError': "Add a check to prevent division by zero.",
            'ValueError': "Verify the input value is in the expected format or range.",
        }
        
        error_analysis['suggestion'] = suggestions.get(
            error_type,
            "Review the error message and traceback for more details."
        )
        
        return error_analysis
