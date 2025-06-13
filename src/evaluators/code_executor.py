"""Code execution and testing functionality"""

import ast
import sys
import time
import traceback
import subprocess
import tempfile
import os
from typing import List, Any, Dict, Optional
from contextlib import contextmanager
import psutil

from ..models import Problem, TestCase, ExecutionResult, GeneratedCode


class CodeExecutor:
    """Safely executes and tests generated code"""
    
    def __init__(self, timeout: int = 10, memory_limit: int = 128):
        self.timeout = timeout
        self.memory_limit = memory_limit  # MB
    
    def execute_code(self, generated_code: GeneratedCode, problem: Problem) -> ExecutionResult:
        """Execute generated code against test cases"""
        start_time = time.time()
        
        try:
            # Validate syntax first
            if not self._validate_syntax(generated_code.code):
                return ExecutionResult(
                    passed=False,
                    output=None,
                    error_message="Syntax error in generated code",
                    execution_time=time.time() - start_time,
                    memory_usage=0,
                    test_case_results=[]
                )
            
            # Run test cases
            test_results = []
            total_memory = 0
            
            for test_case in problem.test_cases:
                result = self._run_single_test(
                    generated_code.code,
                    problem.function_signature,
                    test_case
                )
                test_results.append(result['passed'])
                total_memory += result['memory_usage']
            
            execution_time = time.time() - start_time
            all_passed = all(test_results)
            
            return ExecutionResult(
                passed=all_passed,
                output=test_results,
                error_message=None,
                execution_time=execution_time,
                memory_usage=total_memory / len(problem.test_cases),
                test_case_results=test_results
            )
            
        except Exception as e:
            return ExecutionResult(
                passed=False,
                output=None,
                error_message=str(e),
                execution_time=time.time() - start_time,
                memory_usage=0,
                test_case_results=[]
            )
    
    def _validate_syntax(self, code: str) -> bool:
        """Check if code has valid Python syntax"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _run_single_test(self, code: str, function_signature: str, test_case: TestCase) -> Dict:
        """Run a single test case in isolated environment"""
        # Extract function name from signature
        func_name = function_signature.split('(')[0].split()[-1]
        
        # Create test script
        test_script = f"""
import sys
import time
import psutil
import os

# Generated code
{code}

# Test execution
try:
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    result = {func_name}({repr(test_case.input_data)})
    execution_time = time.time() - start_time
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = memory_after - memory_before
    
    expected = {repr(test_case.expected_output)}
    passed = result == expected
    
    print(f"RESULT:{{
        'passed': {passed},
        'output': {repr(result)},
        'expected': {repr(test_case.expected_output)},
        'execution_time': {execution_time},
        'memory_usage': {memory_used}
    }}")
    
except Exception as e:
    print(f"ERROR:{{
        'passed': False,
        'error': '{str(e)}',
        'execution_time': 0,
        'memory_usage': 0
    }}")
"""
        
        # Execute in temporary file with timeout
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Parse result
            output = result.stdout.strip()
            if output.startswith('RESULT:'):
                return eval(output[7:])  # Extract dict after 'RESULT:'
            elif output.startswith('ERROR:'):
                error_info = eval(output[6:])  # Extract dict after 'ERROR:'
                return {
                    'passed': False,
                    'memory_usage': 0,
                    'error': error_info.get('error', 'Unknown error')
                }
            else:
                return {
                    'passed': False,
                    'memory_usage': 0,
                    'error': 'Unexpected output format'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'memory_usage': 0,
                'error': f'Execution timeout ({self.timeout}s)'
            }
        except Exception as e:
            return {
                'passed': False,
                'memory_usage': 0,
                'error': str(e)
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    @contextmanager
    def _resource_limit(self):
        """Context manager for resource limiting"""
        # This is a simplified version - in production you'd use more robust isolation
        original_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(1000)  # Prevent infinite recursion
            yield
        finally:
            sys.setrecursionlimit(original_limit)