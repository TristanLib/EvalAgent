"""MBPP benchmark loader"""

import json
from typing import List, Dict, Any
from ..models import Problem, TestCase
from .dataset_downloader import BenchmarkDownloader


class MBPPLoader:
    """Loader for MBPP (Mostly Basic Programming Problems) benchmark dataset"""
    
    def __init__(self, data_path: str = "benchmarks"):
        self.data_path = data_path
        self.downloader = BenchmarkDownloader(data_path)
    
    def load_problems(self, use_official: bool = True) -> List[Problem]:
        """Load MBPP problems"""
        
        if use_official:
            # Try to load official MBPP dataset
            if self.downloader.is_downloaded('mbpp'):
                dataset_path = self.downloader.get_dataset_path('mbpp')
                return self._load_from_file(str(dataset_path))
            else:
                print("Official MBPP dataset not found. Use 'download-benchmarks' command to download it.")
                print("Using sample problems instead...")
        
        # Fallback to sample problems
        return self._create_sample_problems()
    
    def _load_from_file(self, filepath: str) -> List[Problem]:
        """Load problems from JSONL file"""
        problems = []
        
        with open(filepath, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                problem = self._parse_mbpp_problem(data)
                if problem:  # Skip if parsing failed
                    problems.append(problem)
        
        return problems
    
    def _parse_mbpp_problem(self, data: Dict[str, Any]) -> Problem:
        """Parse an MBPP problem from JSON data"""
        
        try:
            # MBPP format:
            # {
            #   "task_id": 1,
            #   "text": "Write a function to find the minimum cost path...",
            #   "code": "def min_cost(cost, m, n): ...",
            #   "test_list": ["assert min_cost(...) == ...", ...]
            # }
            
            task_id = str(data.get('task_id', 'unknown'))
            text = data.get('text', '')
            code = data.get('code', '')
            test_list = data.get('test_list', [])
            
            # Extract function signature from the code
            function_signature = self._extract_function_signature(code)
            
            # Create test cases from test_list
            test_cases = self._create_test_cases(test_list)
            
            # Determine difficulty based on problem characteristics
            difficulty = self._infer_difficulty(text, code, test_list)
            
            return Problem(
                id=f"MBPP/{task_id}",
                title=f"MBPP Problem {task_id}",
                description=text,
                function_signature=function_signature,
                docstring=text,  # Use description as docstring
                test_cases=test_cases,
                difficulty=difficulty,
                category="mbpp"
            )
            
        except Exception as e:
            print(f"Warning: Failed to parse MBPP problem {data.get('task_id', 'unknown')}: {e}")
            return None
    
    def _extract_function_signature(self, code: str) -> str:
        """Extract function signature from code"""
        lines = code.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                return stripped
        return "def unknown():"
    
    def _create_test_cases(self, test_list: List[str]) -> List[TestCase]:
        """Create test cases from MBPP test list"""
        test_cases = []
        
        for test_str in test_list:
            if not test_str.strip():
                continue
            
            try:
                # MBPP tests are typically assert statements
                if test_str.strip().startswith('assert '):
                    # Parse the assertion
                    assertion = test_str.strip()[7:]  # Remove 'assert '
                    
                    if '==' in assertion:
                        call_part, expected_part = assertion.split('==', 1)
                        call_part = call_part.strip()
                        expected_part = expected_part.strip()
                        
                        test_cases.append(TestCase(
                            input_data=call_part,
                            expected_output=expected_part,
                            test_type="assertion"
                        ))
                    else:
                        # Boolean assertion
                        test_cases.append(TestCase(
                            input_data=assertion,
                            expected_output="True",
                            test_type="boolean"
                        ))
                else:
                    # Other test format
                    test_cases.append(TestCase(
                        input_data=test_str,
                        expected_output=None,
                        test_type="general"
                    ))
                    
            except Exception:
                # If parsing fails, create a basic test case
                test_cases.append(TestCase(
                    input_data=test_str,
                    expected_output=None,
                    test_type="raw"
                ))
        
        # Ensure at least one test case
        if not test_cases:
            test_cases.append(TestCase(
                input_data="No test cases",
                expected_output=None,
                test_type="basic"
            ))
        
        return test_cases
    
    def _infer_difficulty(self, text: str, code: str, test_list: List[str]) -> str:
        """Infer problem difficulty based on various factors"""
        
        # Simple heuristics based on problem characteristics
        difficulty_score = 0
        
        # Text length and complexity
        if len(text) > 200:
            difficulty_score += 1
        if len(text) > 400:
            difficulty_score += 1
        
        # Code complexity
        if len(code) > 300:
            difficulty_score += 1
        if len(code) > 600:
            difficulty_score += 1
        
        # Number of test cases
        if len(test_list) > 5:
            difficulty_score += 1
        
        # Keywords that suggest complexity
        complex_keywords = ['algorithm', 'dynamic', 'recursive', 'optimization', 'graph', 'tree', 'matrix']
        if any(keyword in text.lower() for keyword in complex_keywords):
            difficulty_score += 2
        
        # Nested structures in code
        if 'for' in code and 'for' in code[code.find('for')+3:]:  # Nested loops
            difficulty_score += 1
        
        if difficulty_score >= 4:
            return "hard"
        elif difficulty_score >= 2:
            return "medium"
        else:
            return "easy"
    
    def _create_sample_problems(self) -> List[Problem]:
        """Create sample MBPP-style problems"""
        
        problems = [
            Problem(
                id="MBPP/001",
                title="Find Minimum in List",
                description="Write a function that takes a list of numbers and returns the minimum value.",
                function_signature="def find_min(numbers):",
                docstring="Return the minimum number in the list.",
                test_cases=[
                    TestCase(input_data="find_min([1, 2, 3])", expected_output="1", test_type="assertion"),
                    TestCase(input_data="find_min([5, 1, 9, 2])", expected_output="1", test_type="assertion"),
                    TestCase(input_data="find_min([-1, -5, -2])", expected_output="-5", test_type="assertion"),
                ],
                difficulty="easy",
                category="arrays"
            ),
            Problem(
                id="MBPP/002",
                title="Check Even Number",
                description="Write a function that checks if a number is even.",
                function_signature="def is_even(n):",
                docstring="Return True if the number is even, False otherwise.",
                test_cases=[
                    TestCase(input_data="is_even(4)", expected_output="True", test_type="assertion"),
                    TestCase(input_data="is_even(7)", expected_output="False", test_type="assertion"),
                    TestCase(input_data="is_even(0)", expected_output="True", test_type="assertion"),
                ],
                difficulty="easy",
                category="math"
            ),
            Problem(
                id="MBPP/003",
                title="Count Vowels",
                description="Write a function that counts the number of vowels in a string.",
                function_signature="def count_vowels(text):",
                docstring="Return the count of vowels (a, e, i, o, u) in the given text.",
                test_cases=[
                    TestCase(input_data="count_vowels('hello')", expected_output="2", test_type="assertion"),
                    TestCase(input_data="count_vowels('python')", expected_output="1", test_type="assertion"),
                    TestCase(input_data="count_vowels('aeiou')", expected_output="5", test_type="assertion"),
                ],
                difficulty="medium",
                category="strings"
            )
        ]
        
        return problems