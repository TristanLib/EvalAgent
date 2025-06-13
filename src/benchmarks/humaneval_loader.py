"""HumanEval benchmark loader"""

import json
import os
from typing import List, Dict, Any
from ..models import Problem, TestCase


class HumanEvalLoader:
    """Loader for HumanEval benchmark dataset"""
    
    def __init__(self, data_path: str = "benchmarks/humaneval"):
        self.data_path = data_path
    
    def load_problems(self) -> List[Problem]:
        """Load HumanEval problems"""
        
        # First try to load from local file
        local_path = os.path.join(self.data_path, "humaneval.jsonl")
        if os.path.exists(local_path):
            return self._load_from_file(local_path)
        
        # If not found, create sample HumanEval-style problems
        return self._create_sample_problems()
    
    def _load_from_file(self, filepath: str) -> List[Problem]:
        """Load problems from JSONL file"""
        problems = []
        
        with open(filepath, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                problem = self._parse_humaneval_problem(data)
                problems.append(problem)
        
        return problems
    
    def _parse_humaneval_problem(self, data: Dict[str, Any]) -> Problem:
        """Parse a HumanEval problem from JSON data"""
        
        # Extract test cases from the test string
        test_cases = self._extract_test_cases(data.get('test', ''))
        
        return Problem(
            id=data['task_id'],
            title=f"HumanEval {data['task_id']}",
            description=data['prompt'],
            function_signature=self._extract_function_signature(data['prompt']),
            docstring=self._extract_docstring(data['prompt']),
            test_cases=test_cases,
            difficulty=self._infer_difficulty(data),
            category="humaneval"
        )
    
    def _extract_function_signature(self, prompt: str) -> str:
        """Extract function signature from prompt"""
        lines = prompt.split('\n')
        for line in lines:
            if line.strip().startswith('def '):
                return line.strip()
        return "def unknown():"
    
    def _extract_docstring(self, prompt: str) -> str:
        """Extract docstring from prompt"""
        lines = prompt.split('\n')
        in_docstring = False
        docstring_lines = []
        
        for line in lines:
            if '"""' in line and not in_docstring:
                in_docstring = True
                docstring_lines.append(line.strip('"""').strip())
            elif '"""' in line and in_docstring:
                docstring_lines.append(line.strip('"""').strip())
                break
            elif in_docstring:
                docstring_lines.append(line.strip())
        
        return '\n'.join(docstring_lines).strip()
    
    def _extract_test_cases(self, test_string: str) -> List[TestCase]:
        """Extract test cases from test string (simplified)"""
        # This is a simplified implementation
        # In practice, you'd need to parse and execute the test code
        test_cases = []
        
        # For now, create dummy test cases
        # In a real implementation, you'd parse the test code and extract assertions
        test_cases.append(TestCase(
            input_data=None,  # Would extract from test code
            expected_output=None,  # Would extract from test code
            test_type="assertion"
        ))
        
        return test_cases
    
    def _infer_difficulty(self, data: Dict[str, Any]) -> str:
        """Infer problem difficulty"""
        # Simple heuristic based on prompt length and complexity
        prompt = data.get('prompt', '')
        
        if len(prompt) > 500:
            return "hard"
        elif len(prompt) > 200:
            return "medium"
        else:
            return "easy"
    
    def _create_sample_problems(self) -> List[Problem]:
        """Create sample HumanEval-style problems"""
        
        problems = [
            Problem(
                id="HumanEval/0",
                title="Has Close Elements",
                description="Check if in given list of numbers, are any two numbers closer to each other than given threshold.",
                function_signature="def has_close_elements(numbers: List[float], threshold: float) -> bool:",
                docstring="""Check if in given list of numbers, are any two numbers closer to each other than given threshold.
                >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
                False
                >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
                True""",
                test_cases=[
                    TestCase(input_data=[[1.0, 2.0, 3.0], 0.5], expected_output=False),
                    TestCase(input_data=[[1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3], expected_output=True),
                    TestCase(input_data=[[1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3], expected_output=True),
                    TestCase(input_data=[[1.0, 2.0, 5.9, 4.0, 5.0], 0.95], expected_output=True),
                ],
                difficulty="medium",
                category="arrays"
            ),
            Problem(
                id="HumanEval/1",
                title="Separate Paren Groups",
                description="Input to this function is a string containing multiple groups of nested parentheses.",
                function_signature="def separate_paren_groups(paren_string: str) -> List[str]:",
                docstring="""Input to this function is a string containing multiple groups of nested parentheses. 
                Your goal is to separate those groups and return a list of those.
                Separate groups are balanced (each open brace is properly closed) and not nested within each other.
                Ignore any spaces in the input string.
                >>> separate_paren_groups('( ) (( )) (( )( ))')
                ['()', '(())', '(()())']""",
                test_cases=[
                    TestCase(input_data=["( ) (( )) (( )( ))"], expected_output=["()", "(())", "(()())"]),
                    TestCase(input_data=["()"], expected_output=["()"]),
                    TestCase(input_data=["((()))"], expected_output=["((()))"]),
                    TestCase(input_data=["() (())"], expected_output=["()", "(())"]),
                ],
                difficulty="medium",
                category="strings"
            ),
            Problem(
                id="HumanEval/2",
                title="Truncate Number",
                description="Given a positive floating point number, return the integer part of the number.",
                function_signature="def truncate_number(number: float) -> float:",
                docstring="""Given a positive floating point number, it can be decomposed into
                and integer part (largest integer smaller than given number) and decimals
                (leftover part always smaller than 1).
                Return the decimal part of the number.
                >>> truncate_number(3.5)
                0.5""",
                test_cases=[
                    TestCase(input_data=[3.5], expected_output=0.5),
                    TestCase(input_data=[1.25], expected_output=0.25),
                    TestCase(input_data=[123.0], expected_output=0.0),
                    TestCase(input_data=[1.33333], expected_output=0.33333),
                ],
                difficulty="easy",
                category="math"
            )
        ]
        
        return problems