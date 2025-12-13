"""
CodeYeti Python Code Runner Module

This module provides safe Python code execution with output capture,
timeout handling, security validation, and error reporting.
"""

import sys
import io
import traceback
import contextlib
import re
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import threading
import queue

from codeyeti.config.settings import settings


SAFE_BUILTINS = {
    'abs': abs,
    'all': all,
    'any': any,
    'ascii': ascii,
    'bin': bin,
    'bool': bool,
    'bytearray': bytearray,
    'bytes': bytes,
    'callable': callable,
    'chr': chr,
    'complex': complex,
    'dict': dict,
    'divmod': divmod,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'format': format,
    'frozenset': frozenset,
    'getattr': getattr,
    'hasattr': hasattr,
    'hash': hash,
    'hex': hex,
    'id': id,
    'int': int,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'iter': iter,
    'len': len,
    'list': list,
    'map': map,
    'max': max,
    'min': min,
    'next': next,
    'object': object,
    'oct': oct,
    'ord': ord,
    'pow': pow,
    'print': print,
    'range': range,
    'repr': repr,
    'reversed': reversed,
    'round': round,
    'set': set,
    'slice': slice,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'type': type,
    'zip': zip,
    'True': True,
    'False': False,
    'None': None,
    'Exception': Exception,
    'ValueError': ValueError,
    'TypeError': TypeError,
    'KeyError': KeyError,
    'IndexError': IndexError,
    'AttributeError': AttributeError,
    'RuntimeError': RuntimeError,
    'StopIteration': StopIteration,
    'ZeroDivisionError': ZeroDivisionError,
}

DANGEROUS_PATTERNS = [
    (r'\bimport\s+os\b', "Direct 'os' module import is blocked"),
    (r'\bimport\s+sys\b', "Direct 'sys' module import is blocked"),
    (r'\bimport\s+subprocess\b', "'subprocess' module is blocked"),
    (r'\bimport\s+shutil\b', "'shutil' module is blocked"),
    (r'\bfrom\s+os\s+import\b', "Importing from 'os' is blocked"),
    (r'\bfrom\s+sys\s+import\b', "Importing from 'sys' is blocked"),
    (r'\b__import__\s*\(', "'__import__' is blocked"),
    (r'\bexec\s*\(', "'exec' is blocked in user code"),
    (r'\beval\s*\(', "'eval' is blocked"),
    (r'\bcompile\s*\(', "'compile' is blocked"),
    (r'\bopen\s*\([^)]*["\'][wa]', "Writing to files is blocked"),
    (r'\bos\.system\b', "'os.system' is blocked"),
    (r'\bos\.popen\b', "'os.popen' is blocked"),
    (r'\bos\.remove\b', "'os.remove' is blocked"),
    (r'\bos\.unlink\b', "'os.unlink' is blocked"),
    (r'\bos\.rmdir\b', "'os.rmdir' is blocked"),
    (r'\bshutil\.rmtree\b', "'shutil.rmtree' is blocked"),
    (r'\bsubprocess\.\w+\b', "'subprocess' operations are blocked"),
    (r'\b__builtins__\b', "Accessing '__builtins__' is blocked"),
    (r'\b__class__\b', "Accessing '__class__' is blocked"),
    (r'\b__bases__\b', "Accessing '__bases__' is blocked"),
    (r'\b__subclasses__\b', "Accessing '__subclasses__' is blocked"),
    (r'\b__globals__\b', "Accessing '__globals__' is blocked"),
    (r'\b__code__\b', "Accessing '__code__' is blocked"),
    (r'\bgetattr\s*\([^)]*["\']__', "Accessing dunder attributes via getattr is blocked"),
]


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
        warnings: List of security warnings if any
    """
    success: bool
    output: str
    error: Optional[str] = None
    traceback_str: Optional[str] = None
    return_value: Optional[str] = None
    warnings: Optional[List[str]] = None


class PythonRunner:
    """
    Safe Python code execution environment.
    
    Provides controlled execution with:
    - Restricted builtins (no file/system access)
    - Pre-execution security validation
    - Output capture and timeout protection
    - Educational code experimentation focus
    """
    
    def __init__(self):
        """Initialize the PythonRunner with configuration."""
        self.timeout = settings.execution_timeout
        self.max_output = settings.max_output_length
    
    def security_check(self, code: str) -> Tuple[bool, List[str]]:
        """
        Check code for dangerous patterns before execution.
        
        Args:
            code: Python source code to check
            
        Returns:
            Tuple of (is_safe, list of violations)
        """
        violations = []
        
        for pattern, message in DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(message)
        
        return len(violations) == 0, violations
    
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
        
        is_safe, violations = self.security_check(code)
        if not is_safe:
            return ExecutionResult(
                success=False,
                output="",
                error="Security validation failed: " + "; ".join(violations),
                traceback_str=None,
                warnings=violations
            )
        
        is_valid, syntax_error = self.validate_code(code)
        if not is_valid:
            return ExecutionResult(
                success=False,
                output="",
                error=syntax_error,
                traceback_str=None
            )
        
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
        Execute code in a separate thread with restricted environment.
        
        Args:
            code: Code to execute
            result_queue: Queue to put result into
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            safe_globals = {
                '__builtins__': SAFE_BUILTINS,
                '__name__': '__main__',
            }
            
            allowed_modules = {
                'math': __import__('math'),
                'random': __import__('random'),
                'datetime': __import__('datetime'),
                'json': __import__('json'),
                'collections': __import__('collections'),
                'itertools': __import__('itertools'),
                'functools': __import__('functools'),
                're': __import__('re'),
                'string': __import__('string'),
                'statistics': __import__('statistics'),
            }
            safe_globals.update(allowed_modules)
            
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
