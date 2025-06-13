"""JSON report generation"""

import json
import os
from datetime import datetime
from typing import Dict, Any

from ..models import BenchmarkRun


class JSONReporter:
    """Generates JSON reports from benchmark results"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, benchmark_run: BenchmarkRun, summary: Dict[str, Any]) -> str:
        """Generate a comprehensive JSON report"""
        
        # Convert benchmark run to dictionary
        report_data = {
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "benchmark_id": benchmark_run.id,
                "benchmark_type": benchmark_run.benchmark_type.value,
                "status": benchmark_run.status.value,
                "duration_seconds": benchmark_run.end_time - benchmark_run.start_time if benchmark_run.end_time else 0,
                "models_evaluated": benchmark_run.models_evaluated,
                "problems_count": benchmark_run.problems_count,
                "total_evaluations": len(benchmark_run.results)
            },
            "summary": summary,
            "model_performances": [self._serialize_model_performance(perf) for perf in benchmark_run.model_performances],
            "detailed_results": [self._serialize_evaluation_result(result) for result in benchmark_run.results],
            "configuration": benchmark_run.configuration
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{benchmark_run.benchmark_type.value}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return filepath
    
    def _serialize_model_performance(self, performance) -> Dict[str, Any]:
        """Convert ModelPerformance to dictionary"""
        return {
            "model_name": performance.model_name,
            "total_problems": performance.total_problems,
            "problems_solved": performance.problems_solved,
            "success_rate": performance.problems_solved / performance.total_problems if performance.total_problems > 0 else 0,
            "pass_at_1": performance.pass_at_1,
            "pass_at_5": performance.pass_at_5,
            "pass_at_10": performance.pass_at_10,
            "average_execution_time": performance.average_execution_time,
            "average_quality_score": performance.average_quality_score,
            "category_performance": performance.category_performance,
            "difficulty_performance": performance.difficulty_performance
        }
    
    def _serialize_evaluation_result(self, result) -> Dict[str, Any]:
        """Convert EvaluationResult to dictionary"""
        return {
            "problem_id": result.problem_id,
            "model_name": result.model_name,
            "status": result.status.value,
            "evaluation_time": result.evaluation_time,
            "generated_code": {
                "code": result.generated_code.code,
                "generation_time": result.generated_code.generation_time,
                "tokens_used": result.generated_code.tokens_used,
                "temperature": result.generated_code.temperature,
                "attempt_number": result.generated_code.attempt_number
            },
            "execution_result": {
                "passed": result.execution_result.passed,
                "output": result.execution_result.output,
                "error_message": result.execution_result.error_message,
                "execution_time": result.execution_result.execution_time,
                "memory_usage": result.execution_result.memory_usage,
                "test_case_results": result.execution_result.test_case_results
            },
            "quality_metrics": {
                "cyclomatic_complexity": result.quality_metrics.cyclomatic_complexity,
                "lines_of_code": result.quality_metrics.lines_of_code,
                "maintainability_index": result.quality_metrics.maintainability_index,
                "style_score": result.quality_metrics.style_score,
                "security_issues": result.quality_metrics.security_issues,
                "performance_score": result.quality_metrics.performance_score
            },
            "pass_at_k_scores": result.pass_at_k_scores
        }
    
    def generate_summary_report(self, summary: Dict[str, Any]) -> str:
        """Generate a summary-only JSON report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_summary_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        summary_data = {
            "report_generated": datetime.now().isoformat(),
            "summary": summary
        }
        
        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        return filepath