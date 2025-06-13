"""Base LLM client interface"""

from abc import ABC, abstractmethod
from typing import Optional
import time

from ..models import Problem, GeneratedCode, LLMConfig


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate_code(self, problem: Problem, attempt_number: int = 1) -> GeneratedCode:
        """Generate code for a given problem"""
        pass
    
    def _create_prompt(self, problem: Problem) -> str:
        """Create a prompt for code generation"""
        prompt = f"""You are an expert Python programmer. Your task is to implement a function that solves the given problem.

Problem: {problem.title}

Description:
{problem.description}

Function signature:
{problem.function_signature}

Requirements:
{problem.docstring}

Please provide only the function implementation in Python. Do not include any test cases, examples, or explanations.
Make sure your code is efficient, readable, and handles edge cases appropriately.

Your response should contain only the Python function implementation."""
        
        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from LLM response"""
        # Remove markdown code blocks if present
        lines = response.strip().split('\n')
        
        # Find code block boundaries
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```python') or line.strip().startswith('```'):
                start_idx = i + 1
                break
        
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '```':
                end_idx = i
                break
        
        # Extract code lines
        code_lines = lines[start_idx:end_idx]
        
        # Remove leading/trailing empty lines
        while code_lines and not code_lines[0].strip():
            code_lines.pop(0)
        while code_lines and not code_lines[-1].strip():
            code_lines.pop()
        
        return '\n'.join(code_lines)
    
    def _count_tokens(self, text: str) -> int:
        """Rough token count estimation"""
        # Simple approximation: ~4 characters per token
        return len(text) // 4