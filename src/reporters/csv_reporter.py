"""CSV report generation"""

import csv
import os
from datetime import datetime
from typing import Dict, Any, List

from ..models import BenchmarkRun


class CSVReporter:
    """Generates CSV reports from benchmark results"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, benchmark_run: BenchmarkRun, summary: Dict[str, Any]) -> List[str]:
        """Generate CSV reports (multiple files for different views)"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_created = []
        
        # 1. Model performance summary
        model_perf_file = self._generate_model_performance_csv(benchmark_run, timestamp)
        files_created.append(model_perf_file)
        
        # 2. Detailed results
        detailed_file = self._generate_detailed_results_csv(benchmark_run, timestamp)
        files_created.append(detailed_file)
        
        # 3. Problem-wise analysis
        problem_file = self._generate_problem_analysis_csv(benchmark_run, timestamp)
        files_created.append(problem_file)
        
        return files_created
    
    def _generate_model_performance_csv(self, benchmark_run: BenchmarkRun, timestamp: str) -> str:
        """Generate model performance summary CSV"""
        
        filename = f"model_performance_{benchmark_run.benchmark_type.value}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'model_name', 'total_problems', 'problems_solved', 'success_rate',
                'pass_at_1', 'pass_at_5', 'pass_at_10', 'avg_execution_time',
                'avg_quality_score', 'avg_cyclomatic_complexity', 'avg_lines_of_code'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for perf in benchmark_run.model_performances:
                # Calculate additional metrics from detailed results
                model_results = [r for r in benchmark_run.results if r.model_name == perf.model_name]
                avg_complexity = sum(r.quality_metrics.cyclomatic_complexity for r in model_results) / len(model_results) if model_results else 0
                avg_loc = sum(r.quality_metrics.lines_of_code for r in model_results) / len(model_results) if model_results else 0
                
                writer.writerow({
                    'model_name': perf.model_name,
                    'total_problems': perf.total_problems,
                    'problems_solved': perf.problems_solved,
                    'success_rate': perf.problems_solved / perf.total_problems if perf.total_problems > 0 else 0,
                    'pass_at_1': perf.pass_at_1,
                    'pass_at_5': perf.pass_at_5,
                    'pass_at_10': perf.pass_at_10,
                    'avg_execution_time': perf.average_execution_time,
                    'avg_quality_score': perf.average_quality_score,
                    'avg_cyclomatic_complexity': avg_complexity,
                    'avg_lines_of_code': avg_loc
                })
        
        return filepath
    
    def _generate_detailed_results_csv(self, benchmark_run: BenchmarkRun, timestamp: str) -> str:
        """Generate detailed results CSV"""
        
        filename = f"detailed_results_{benchmark_run.benchmark_type.value}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'problem_id', 'model_name', 'status', 'passed', 'evaluation_time',
                'generation_time', 'tokens_used', 'execution_time', 'memory_usage',
                'cyclomatic_complexity', 'lines_of_code', 'maintainability_index',
                'style_score', 'performance_score', 'security_issues_count',
                'error_message'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in benchmark_run.results:
                writer.writerow({
                    'problem_id': result.problem_id,
                    'model_name': result.model_name,
                    'status': result.status.value,
                    'passed': result.execution_result.passed,
                    'evaluation_time': result.evaluation_time,
                    'generation_time': result.generated_code.generation_time,
                    'tokens_used': result.generated_code.tokens_used,
                    'execution_time': result.execution_result.execution_time,
                    'memory_usage': result.execution_result.memory_usage,
                    'cyclomatic_complexity': result.quality_metrics.cyclomatic_complexity,
                    'lines_of_code': result.quality_metrics.lines_of_code,
                    'maintainability_index': result.quality_metrics.maintainability_index,
                    'style_score': result.quality_metrics.style_score,
                    'performance_score': result.quality_metrics.performance_score,
                    'security_issues_count': len(result.quality_metrics.security_issues),
                    'error_message': result.execution_result.error_message or ''
                })
        
        return filepath
    
    def _generate_problem_analysis_csv(self, benchmark_run: BenchmarkRun, timestamp: str) -> str:
        """Generate problem-wise analysis CSV"""
        
        filename = f"problem_analysis_{benchmark_run.benchmark_type.value}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Group results by problem
        problem_stats = {}
        for result in benchmark_run.results:
            if result.problem_id not in problem_stats:
                problem_stats[result.problem_id] = {
                    'total_attempts': 0,
                    'successful_attempts': 0,
                    'models_tested': set(),
                    'avg_execution_time': 0,
                    'avg_quality_score': 0,
                    'execution_times': [],
                    'quality_scores': []
                }
            
            stats = problem_stats[result.problem_id]
            stats['total_attempts'] += 1
            stats['models_tested'].add(result.model_name)
            stats['execution_times'].append(result.execution_result.execution_time)
            stats['quality_scores'].append(result.quality_metrics.maintainability_index)
            
            if result.execution_result.passed:
                stats['successful_attempts'] += 1
        
        # Calculate averages
        for problem_id, stats in problem_stats.items():
            stats['avg_execution_time'] = sum(stats['execution_times']) / len(stats['execution_times'])
            stats['avg_quality_score'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
            stats['success_rate'] = stats['successful_attempts'] / stats['total_attempts']
            stats['models_count'] = len(stats['models_tested'])
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'problem_id', 'total_attempts', 'successful_attempts', 'success_rate',
                'models_tested', 'avg_execution_time', 'avg_quality_score'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for problem_id, stats in problem_stats.items():
                writer.writerow({
                    'problem_id': problem_id,
                    'total_attempts': stats['total_attempts'],
                    'successful_attempts': stats['successful_attempts'],
                    'success_rate': stats['success_rate'],
                    'models_tested': stats['models_count'],
                    'avg_execution_time': stats['avg_execution_time'],
                    'avg_quality_score': stats['avg_quality_score']
                })
        
        return filepath