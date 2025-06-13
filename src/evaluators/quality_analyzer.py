"""Code quality analysis functionality"""

import ast
import re
from typing import List, Dict, Any
import subprocess
import tempfile
import os

from ..models import CodeQualityMetrics, GeneratedCode


class QualityAnalyzer:
    """Analyzes code quality metrics"""
    
    def __init__(self):
        self.complexity_threshold = 10
        self.max_line_length = 100
    
    def analyze_quality(self, generated_code: GeneratedCode) -> CodeQualityMetrics:
        """Perform comprehensive code quality analysis"""
        code = generated_code.code
        
        try:
            # Parse AST for analysis
            tree = ast.parse(code)
            
            # Calculate metrics
            complexity = self._calculate_cyclomatic_complexity(tree)
            loc = self._count_lines_of_code(code)
            maintainability = self._calculate_maintainability_index(code, complexity, loc)
            style_score = self._analyze_code_style(code)
            security_issues = self._check_security_issues(code)
            performance_score = self._analyze_performance(tree)
            
            return CodeQualityMetrics(
                cyclomatic_complexity=complexity,
                lines_of_code=loc,
                maintainability_index=maintainability,
                style_score=style_score,
                security_issues=security_issues,
                performance_score=performance_score
            )
            
        except SyntaxError:
            # Return default metrics for invalid code
            return CodeQualityMetrics(
                cyclomatic_complexity=0,
                lines_of_code=0,
                maintainability_index=0.0,
                style_score=0.0,
                security_issues=["Syntax error in code"],
                performance_score=0.0
            )
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points that increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                # List comprehensions add complexity
                for generator in node.generators:
                    complexity += len(generator.ifs) + 1
        
        return complexity
    
    def _count_lines_of_code(self, code: str) -> int:
        """Count non-empty, non-comment lines"""
        lines = code.split('\n')
        loc = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        
        return loc
    
    def _calculate_maintainability_index(self, code: str, complexity: int, loc: int) -> float:
        """Calculate maintainability index (simplified version)"""
        if loc == 0:
            return 0.0
        
        # Simplified MI calculation based on Halstead metrics and cyclomatic complexity
        # Real MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        
        # Simplified version focusing on complexity and length
        halstead_volume = loc * 2  # Simplified approximation
        
        if halstead_volume <= 0:
            return 0.0
        
        import math
        mi = max(0, 171 - 5.2 * math.log(halstead_volume) - 0.23 * complexity - 16.2 * math.log(max(1, loc)))
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))
    
    def _analyze_code_style(self, code: str) -> float:
        """Analyze code style and PEP 8 compliance"""
        style_score = 100.0
        deductions = 0
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self.max_line_length:
                deductions += 1
            
            # Check indentation (should be 4 spaces)
            if line.strip() and line.startswith(' '):
                leading_spaces = len(line) - len(line.lstrip(' '))
                if leading_spaces % 4 != 0:
                    deductions += 1
            
            # Check for trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                deductions += 1
        
        # Check naming conventions
        if not self._check_naming_conventions(code):
            deductions += 5
        
        # Check for proper spacing around operators
        if not self._check_operator_spacing(code):
            deductions += 2
        
        # Deduct points for style violations
        style_score = max(0, style_score - (deductions * 2))
        
        return style_score
    
    def _check_naming_conventions(self, code: str) -> bool:
        """Check Python naming conventions"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Function names should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                        return False
                
                elif isinstance(node, ast.ClassDef):
                    # Class names should be PascalCase
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        return False
                
                elif isinstance(node, ast.arg):
                    # Parameter names should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.arg):
                        return False
            
            return True
        except:
            return False
    
    def _check_operator_spacing(self, code: str) -> bool:
        """Check for proper spacing around operators"""
        # Simple regex check for common spacing issues
        patterns = [
            r'[a-zA-Z0-9]\+[a-zA-Z0-9]',  # No space around +
            r'[a-zA-Z0-9]\-[a-zA-Z0-9]',  # No space around -
            r'[a-zA-Z0-9]\*[a-zA-Z0-9]',  # No space around *
            r'[a-zA-Z0-9]/[a-zA-Z0-9]',   # No space around /
            r'[a-zA-Z0-9]=[a-zA-Z0-9]',   # No space around =
        ]
        
        for pattern in patterns:
            if re.search(pattern, code):
                return False
        
        return True
    
    def _check_security_issues(self, code: str) -> List[str]:
        """Check for common security issues"""
        issues = []
        
        # Check for dangerous imports/functions
        dangerous_patterns = [
            (r'import\s+os', 'Use of os module - potential security risk'),
            (r'import\s+subprocess', 'Use of subprocess module - potential security risk'),
            (r'eval\s*\(', 'Use of eval() function - major security risk'),
            (r'exec\s*\(', 'Use of exec() function - major security risk'),
            (r'__import__\s*\(', 'Use of __import__() function - potential security risk'),
            (r'open\s*\(', 'File operations detected - review for path traversal'),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(message)
        
        return issues
    
    def _analyze_performance(self, tree: ast.AST) -> float:
        """Analyze potential performance issues"""
        performance_score = 100.0
        deductions = 0
        
        for node in ast.walk(tree):
            # Nested loops (potential O(n²) or worse)
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)) and child != node:
                        nested_loops += 1
                
                if nested_loops > 0:
                    deductions += nested_loops * 10
            
            # String concatenation in loops (inefficient)
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        # Look for string concatenation
                        deductions += 5
        
        return max(0, performance_score - deductions)