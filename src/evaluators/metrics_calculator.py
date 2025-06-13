"""Metrics calculation functionality"""

import math
from typing import List, Dict, Any
from collections import defaultdict

from ..models import EvaluationResult, ModelPerformance, BenchmarkRun


class MetricsCalculator:
    """Calculates evaluation metrics and statistics"""
    
    def calculate_pass_at_k(self, results: List[bool], k: int) -> float:
        """Calculate pass@k metric"""
        if not results or k <= 0:
            return 0.0
        
        n = len(results)
        if k > n:
            k = n
        
        # Pass@k = 1 - (C(n-c, k) / C(n, k))
        # where c is the number of correct solutions
        c = sum(results)
        
        if c == 0:
            return 0.0
        if c >= k:
            return 1.0
        
        # Calculate combination C(n, k)
        def combination(n: int, r: int) -> int:
            if r > n or r < 0:
                return 0
            if r == 0 or r == n:
                return 1
            
            r = min(r, n - r)  # Take advantage of symmetry
            result = 1
            for i in range(r):
                result = result * (n - i) // (i + 1)
            return result
        
        c_n_k = combination(n, k)
        c_n_minus_c_k = combination(n - c, k)
        
        if c_n_k == 0:
            return 0.0
        
        return 1.0 - (c_n_minus_c_k / c_n_k)
    
    def calculate_model_performance(self, model_name: str, results: List[EvaluationResult]) -> ModelPerformance:
        """Calculate aggregated performance metrics for a model"""
        model_results = [r for r in results if r.model_name == model_name]
        
        if not model_results:
            return ModelPerformance(
                model_name=model_name,
                total_problems=0,
                problems_solved=0,
                pass_at_1=0.0,
                pass_at_5=0.0,
                pass_at_10=0.0,
                average_execution_time=0.0,
                average_quality_score=0.0,
                category_performance={},
                difficulty_performance={}
            )
        
        # Basic statistics
        total_problems = len(model_results)
        problems_solved = sum(1 for r in model_results if r.execution_result.passed)
        
        # Collect all execution results for pass@k calculation
        all_passes = [r.execution_result.passed for r in model_results]
        
        # Calculate pass@k scores
        pass_at_1 = self.calculate_pass_at_k(all_passes, 1)
        pass_at_5 = self.calculate_pass_at_k(all_passes, 5) if len(all_passes) >= 5 else pass_at_1
        pass_at_10 = self.calculate_pass_at_k(all_passes, 10) if len(all_passes) >= 10 else pass_at_5
        
        # Average metrics
        avg_execution_time = sum(r.execution_result.execution_time for r in model_results) / total_problems
        avg_quality_score = sum(r.quality_metrics.maintainability_index for r in model_results) / total_problems
        
        # Category and difficulty performance (simplified - would need problem metadata)
        category_performance = self._calculate_category_performance(model_results)
        difficulty_performance = self._calculate_difficulty_performance(model_results)
        
        return ModelPerformance(
            model_name=model_name,
            total_problems=total_problems,
            problems_solved=problems_solved,
            pass_at_1=pass_at_1,
            pass_at_5=pass_at_5,
            pass_at_10=pass_at_10,
            average_execution_time=avg_execution_time,
            average_quality_score=avg_quality_score,
            category_performance=category_performance,
            difficulty_performance=difficulty_performance
        )
    
    def _calculate_category_performance(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """Calculate performance by problem category"""
        category_stats = defaultdict(list)
        
        for result in results:
            # In a real implementation, this would use problem metadata
            # For now, we'll use a simple heuristic based on problem_id
            category = self._infer_category(result.problem_id)
            category_stats[category].append(result.execution_result.passed)
        
        category_performance = {}
        for category, passes in category_stats.items():
            if passes:
                category_performance[category] = sum(passes) / len(passes)
        
        return category_performance
    
    def _calculate_difficulty_performance(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """Calculate performance by problem difficulty"""
        difficulty_stats = defaultdict(list)
        
        for result in results:
            # In a real implementation, this would use problem metadata
            # For now, we'll use a simple heuristic
            difficulty = self._infer_difficulty(result)
            difficulty_stats[difficulty].append(result.execution_result.passed)
        
        difficulty_performance = {}
        for difficulty, passes in difficulty_stats.items():
            if passes:
                difficulty_performance[difficulty] = sum(passes) / len(passes)
        
        return difficulty_performance
    
    def _infer_category(self, problem_id: str) -> str:
        """Infer problem category from ID (placeholder implementation)"""
        # This is a simplified heuristic - in practice, you'd have problem metadata
        if 'sort' in problem_id.lower() or 'array' in problem_id.lower():
            return 'algorithms'
        elif 'list' in problem_id.lower() or 'tree' in problem_id.lower():
            return 'data_structures'
        elif 'string' in problem_id.lower() or 'text' in problem_id.lower():
            return 'string_processing'
        else:
            return 'general'
    
    def _infer_difficulty(self, result: EvaluationResult) -> str:
        """Infer problem difficulty from execution metrics"""
        # Simple heuristic based on execution time and complexity
        exec_time = result.execution_result.execution_time
        complexity = result.quality_metrics.cyclomatic_complexity
        
        if exec_time > 1.0 or complexity > 10:
            return 'hard'
        elif exec_time > 0.1 or complexity > 5:
            return 'medium'
        else:
            return 'easy'
    
    def calculate_benchmark_statistics(self, benchmark_run: BenchmarkRun) -> Dict[str, Any]:
        """Calculate comprehensive benchmark statistics"""
        if not benchmark_run.results:
            return {}
        
        total_evaluations = len(benchmark_run.results)
        successful_evaluations = sum(1 for r in benchmark_run.results if r.execution_result.passed)
        
        # Model comparison
        model_stats = {}
        for model_name in benchmark_run.models_evaluated:
            model_results = [r for r in benchmark_run.results if r.model_name == model_name]
            if model_results:
                model_stats[model_name] = {
                    'total': len(model_results),
                    'passed': sum(1 for r in model_results if r.execution_result.passed),
                    'success_rate': sum(1 for r in model_results if r.execution_result.passed) / len(model_results),
                    'avg_execution_time': sum(r.execution_result.execution_time for r in model_results) / len(model_results),
                    'avg_quality_score': sum(r.quality_metrics.maintainability_index for r in model_results) / len(model_results)
                }
        
        # Overall statistics
        overall_stats = {
            'total_evaluations': total_evaluations,
            'successful_evaluations': successful_evaluations,
            'overall_success_rate': successful_evaluations / total_evaluations if total_evaluations > 0 else 0,
            'average_execution_time': sum(r.execution_result.execution_time for r in benchmark_run.results) / total_evaluations,
            'average_quality_score': sum(r.quality_metrics.maintainability_index for r in benchmark_run.results) / total_evaluations,
            'models_evaluated': len(benchmark_run.models_evaluated),
            'problems_evaluated': benchmark_run.problems_count,
            'duration': benchmark_run.end_time - benchmark_run.start_time if benchmark_run.end_time else 0
        }
        
        return {
            'overall': overall_stats,
            'by_model': model_stats,
            'benchmark_info': {
                'type': benchmark_run.benchmark_type.value,
                'start_time': benchmark_run.start_time,
                'end_time': benchmark_run.end_time,
                'status': benchmark_run.status.value
            }
        }