"""Main benchmark loader that coordinates different benchmark implementations"""

from typing import List
from ..models import Problem, BenchmarkType
from .humaneval_loader import HumanEvalLoader
from .mbpp_loader import MBPPLoader


class BenchmarkLoader:
    """Main class for loading different types of benchmarks"""
    
    def __init__(self):
        self.loaders = {
            BenchmarkType.HUMANEVAL: HumanEvalLoader(),
            BenchmarkType.MBPP: MBPPLoader(),
            BenchmarkType.CUSTOM: self._create_custom_loader()
        }
    
    def load_benchmark(self, benchmark_type: BenchmarkType) -> List[Problem]:
        """Load problems for the specified benchmark type"""
        
        if benchmark_type not in self.loaders:
            raise ValueError(f"Unsupported benchmark type: {benchmark_type}")
        
        loader = self.loaders[benchmark_type]
        return loader.load_problems()
    
    
    def _create_custom_loader(self):
        """Create custom benchmark loader (placeholder)"""
        # This would be implemented to load custom benchmarks
        return SampleLoader("Custom")


class SampleLoader:
    """Sample loader that creates example problems for testing"""
    
    def __init__(self, name: str):
        self.name = name
    
    def load_problems(self) -> List[Problem]:
        """Load sample problems"""
        from ..models import TestCase
        
        problems = [
            Problem(
                id=f"{self.name.lower()}_001",
                title="Sum Two Numbers",
                description="Write a function that returns the sum of two numbers.",
                function_signature="def add_numbers(a: int, b: int) -> int:",
                docstring="Return the sum of two integers a and b.",
                test_cases=[
                    TestCase(input_data=[2, 3], expected_output=5),
                    TestCase(input_data=[0, 0], expected_output=0),
                    TestCase(input_data=[-1, 1], expected_output=0),
                    TestCase(input_data=[100, 200], expected_output=300),
                ],
                difficulty="easy",
                category="arithmetic"
            ),
            Problem(
                id=f"{self.name.lower()}_002",
                title="Find Maximum",
                description="Write a function that finds the maximum element in a list.",
                function_signature="def find_max(numbers: List[int]) -> int:",
                docstring="Return the maximum number in the list. Assume the list is not empty.",
                test_cases=[
                    TestCase(input_data=[[1, 2, 3]], expected_output=3),
                    TestCase(input_data=[[5, 1, 9, 2]], expected_output=9),
                    TestCase(input_data=[[-1, -5, -2]], expected_output=-1),
                    TestCase(input_data=[[42]], expected_output=42),
                ],
                difficulty="easy",
                category="arrays"
            ),
            Problem(
                id=f"{self.name.lower()}_003",
                title="Reverse String",
                description="Write a function that reverses a string.",
                function_signature="def reverse_string(s: str) -> str:",
                docstring="Return the reverse of the input string.",
                test_cases=[
                    TestCase(input_data=["hello"], expected_output="olleh"),
                    TestCase(input_data=[""], expected_output=""),
                    TestCase(input_data=["a"], expected_output="a"),
                    TestCase(input_data=["Python"], expected_output="nohtyP"),
                ],
                difficulty="easy",
                category="strings"
            )
        ]
        
        return problems