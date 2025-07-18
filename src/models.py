"""Core data models for EvalAgent"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import time


class BenchmarkType(Enum):
    HUMANEVAL = "humaneval"
    MBPP = "mbpp"
    BIGCODEBENCH = "bigcodebench"
    CUSTOM = "custom"


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TestCase:
    """Represents a single test case for code evaluation"""
    input_data: Any
    expected_output: Any
    test_type: str = "unit"  # unit, integration, performance


@dataclass
class Problem:
    """Represents a coding problem to evaluate"""
    id: str
    title: str
    description: str
    function_signature: str
    docstring: str
    test_cases: List[TestCase]
    difficulty: str = "medium"  # easy, medium, hard
    category: str = "general"  # algorithms, data_structures, etc.
    time_limit: int = 10  # seconds
    memory_limit: int = 128  # MB


@dataclass
class GeneratedCode:
    """Represents code generated by an LLM"""
    code: str
    model_name: str
    problem_id: str
    generation_time: float
    tokens_used: int
    temperature: float
    attempt_number: int


@dataclass
class ExecutionResult:
    """Result of executing generated code"""
    passed: bool
    output: Any
    error_message: Optional[str]
    execution_time: float
    memory_usage: float
    test_case_results: List[bool]


@dataclass
class CodeQualityMetrics:
    """Code quality analysis results"""
    cyclomatic_complexity: int
    lines_of_code: int
    maintainability_index: float
    style_score: float
    security_issues: List[str]
    performance_score: float


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single problem-model pair"""
    problem_id: str
    model_name: str
    generated_code: GeneratedCode
    execution_result: ExecutionResult
    quality_metrics: CodeQualityMetrics
    status: EvaluationStatus
    evaluation_time: float
    pass_at_k_scores: Dict[int, float]


@dataclass
class ModelPerformance:
    """Aggregated performance metrics for a model"""
    model_name: str
    total_problems: int
    problems_solved: int
    pass_at_1: float
    pass_at_5: float
    pass_at_10: float
    average_execution_time: float
    average_quality_score: float
    category_performance: Dict[str, float]
    difficulty_performance: Dict[str, float]


@dataclass
class BenchmarkRun:
    """Represents a complete benchmark evaluation run"""
    id: str
    benchmark_type: BenchmarkType
    models_evaluated: List[str]
    problems_count: int
    start_time: float
    end_time: Optional[float]
    status: EvaluationStatus
    results: List[EvaluationResult]
    model_performances: List[ModelPerformance]
    configuration: Dict[str, Any]


@dataclass
class LLMConfig:
    """Configuration for an LLM"""
    name: str
    api_key: str
    base_url: str
    model_id: str
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30
    max_retries: int = 3