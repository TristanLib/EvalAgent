"""Main evaluation agent that orchestrates the evaluation process"""

import time
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import (
    Problem, BenchmarkRun, EvaluationResult, ModelPerformance,
    BenchmarkType, EvaluationStatus, GeneratedCode, LLMConfig
)
from ..evaluators import CodeExecutor, QualityAnalyzer, MetricsCalculator
from ..llm_clients import LLMClientFactory


class EvaluationAgent:
    """Main agent that coordinates LLM evaluation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.code_executor = CodeExecutor(
            timeout=config.get('timeout', 10),
            memory_limit=config.get('memory_limit', 128)
        )
        self.quality_analyzer = QualityAnalyzer()
        self.metrics_calculator = MetricsCalculator()
        self.llm_client_factory = LLMClientFactory()
        
    async def run_benchmark(
        self,
        benchmark_type: BenchmarkType,
        problems: List[Problem],
        llm_configs: List[LLMConfig],
        max_workers: int = 4
    ) -> BenchmarkRun:
        """Run a complete benchmark evaluation"""
        
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        benchmark_run = BenchmarkRun(
            id=run_id,
            benchmark_type=benchmark_type,
            models_evaluated=[config.name for config in llm_configs],
            problems_count=len(problems),
            start_time=start_time,
            end_time=None,
            status=EvaluationStatus.RUNNING,
            results=[],
            model_performances=[],
            configuration=self.config
        )
        
        try:
            print(f"Starting benchmark: {benchmark_type.value}")
            print(f"Problems: {len(problems)}, Models: {len(llm_configs)}")
            
            # Run evaluations in parallel
            all_results = await self._run_evaluations_parallel(
                problems, llm_configs, max_workers
            )
            
            benchmark_run.results = all_results
            benchmark_run.end_time = time.time()
            benchmark_run.status = EvaluationStatus.COMPLETED
            
            # Calculate model performances
            model_performances = []
            for llm_config in llm_configs:
                performance = self.metrics_calculator.calculate_model_performance(
                    llm_config.name, all_results
                )
                model_performances.append(performance)
            
            benchmark_run.model_performances = model_performances
            
            print(f"Benchmark completed in {benchmark_run.end_time - benchmark_run.start_time:.2f}s")
            
            return benchmark_run
            
        except Exception as e:
            benchmark_run.end_time = time.time()
            benchmark_run.status = EvaluationStatus.FAILED
            print(f"Benchmark failed: {str(e)}")
            raise
    
    async def _run_evaluations_parallel(
        self,
        problems: List[Problem],
        llm_configs: List[LLMConfig],
        max_workers: int
    ) -> List[EvaluationResult]:
        """Run evaluations in parallel using thread pool"""
        
        all_results = []
        
        # Create evaluation tasks
        tasks = []
        for problem in problems:
            for llm_config in llm_configs:
                tasks.append((problem, llm_config))
        
        print(f"Running {len(tasks)} evaluation tasks with {max_workers} workers")
        
        # Execute tasks in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._evaluate_single, problem, llm_config): (problem, llm_config)
                for problem, llm_config in tasks
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    all_results.append(result)
                    completed += 1
                    
                    if completed % 10 == 0:
                        print(f"Completed {completed}/{len(tasks)} evaluations")
                        
                except Exception as e:
                    problem, llm_config = future_to_task[future]
                    print(f"Evaluation failed for {llm_config.name} on {problem.id}: {str(e)}")
        
        print(f"All {len(all_results)} evaluations completed")
        return all_results
    
    def _evaluate_single(self, problem: Problem, llm_config: LLMConfig) -> EvaluationResult:
        """Evaluate a single problem with a single LLM"""
        start_time = time.time()
        
        try:
            # Generate code using LLM
            llm_client = self.llm_client_factory.create_client(llm_config)
            generated_code = llm_client.generate_code(problem)
            
            # Execute and test the code
            execution_result = self.code_executor.execute_code(generated_code, problem)
            
            # Analyze code quality
            quality_metrics = self.quality_analyzer.analyze_quality(generated_code)
            
            # Calculate pass@k scores (simplified - would need multiple attempts for real pass@k)
            pass_at_k_scores = {
                1: 1.0 if execution_result.passed else 0.0,
                5: 1.0 if execution_result.passed else 0.0,
                10: 1.0 if execution_result.passed else 0.0
            }
            
            evaluation_time = time.time() - start_time
            
            return EvaluationResult(
                problem_id=problem.id,
                model_name=llm_config.name,
                generated_code=generated_code,
                execution_result=execution_result,
                quality_metrics=quality_metrics,
                status=EvaluationStatus.COMPLETED,
                evaluation_time=evaluation_time,
                pass_at_k_scores=pass_at_k_scores
            )
            
        except Exception as e:
            # Create failed result
            evaluation_time = time.time() - start_time
            
            # Create dummy objects for failed evaluation
            from ..models import ExecutionResult, CodeQualityMetrics
            
            failed_code = GeneratedCode(
                code="",
                model_name=llm_config.name,
                problem_id=problem.id,
                generation_time=0.0,
                tokens_used=0,
                temperature=llm_config.temperature,
                attempt_number=1
            )
            
            failed_execution = ExecutionResult(
                passed=False,
                output=None,
                error_message=str(e),
                execution_time=0.0,
                memory_usage=0.0,
                test_case_results=[]
            )
            
            failed_quality = CodeQualityMetrics(
                cyclomatic_complexity=0,
                lines_of_code=0,
                maintainability_index=0.0,
                style_score=0.0,
                security_issues=[str(e)],
                performance_score=0.0
            )
            
            return EvaluationResult(
                problem_id=problem.id,
                model_name=llm_config.name,
                generated_code=failed_code,
                execution_result=failed_execution,
                quality_metrics=failed_quality,
                status=EvaluationStatus.FAILED,
                evaluation_time=evaluation_time,
                pass_at_k_scores={1: 0.0, 5: 0.0, 10: 0.0}
            )
    
    def generate_summary_report(self, benchmark_run: BenchmarkRun) -> Dict[str, Any]:
        """Generate a summary report of the benchmark run"""
        
        statistics = self.metrics_calculator.calculate_benchmark_statistics(benchmark_run)
        
        # Create summary
        summary = {
            'benchmark_id': benchmark_run.id,
            'benchmark_type': benchmark_run.benchmark_type.value,
            'duration': benchmark_run.end_time - benchmark_run.start_time if benchmark_run.end_time else 0,
            'status': benchmark_run.status.value,
            'statistics': statistics,
            'model_rankings': self._create_model_rankings(benchmark_run.model_performances),
            'top_performers': self._identify_top_performers(benchmark_run.model_performances),
            'insights': self._generate_insights(benchmark_run)
        }
        
        return summary
    
    def _create_model_rankings(self, performances: List[ModelPerformance]) -> List[Dict[str, Any]]:
        """Create model rankings based on performance"""
        
        # Sort by pass@1 score (primary metric)
        sorted_models = sorted(performances, key=lambda x: x.pass_at_1, reverse=True)
        
        rankings = []
        for i, perf in enumerate(sorted_models, 1):
            rankings.append({
                'rank': i,
                'model': perf.model_name,
                'pass_at_1': perf.pass_at_1,
                'pass_at_5': perf.pass_at_5,
                'pass_at_10': perf.pass_at_10,
                'problems_solved': perf.problems_solved,
                'total_problems': perf.total_problems,
                'success_rate': perf.problems_solved / perf.total_problems if perf.total_problems > 0 else 0,
                'avg_quality_score': perf.average_quality_score
            })
        
        return rankings
    
    def _identify_top_performers(self, performances: List[ModelPerformance]) -> Dict[str, str]:
        """Identify top performing models in different categories"""
        
        if not performances:
            return {}
        
        top_performers = {}
        
        # Best overall (pass@1)
        best_overall = max(performances, key=lambda x: x.pass_at_1)
        top_performers['best_overall'] = best_overall.model_name
        
        # Best code quality
        best_quality = max(performances, key=lambda x: x.average_quality_score)
        top_performers['best_code_quality'] = best_quality.model_name
        
        # Fastest execution
        fastest = min(performances, key=lambda x: x.average_execution_time)
        top_performers['fastest_execution'] = fastest.model_name
        
        # Most consistent (highest pass@10 relative to pass@1)
        most_consistent = max(performances, key=lambda x: x.pass_at_10 - x.pass_at_1 if x.pass_at_1 > 0 else 0)
        top_performers['most_consistent'] = most_consistent.model_name
        
        return top_performers
    
    def _generate_insights(self, benchmark_run: BenchmarkRun) -> List[str]:
        """Generate insights from the benchmark results"""
        
        insights = []
        
        if not benchmark_run.model_performances:
            return ["No model performance data available for analysis."]
        
        # Performance spread analysis
        pass_at_1_scores = [p.pass_at_1 for p in benchmark_run.model_performances]
        min_score, max_score = min(pass_at_1_scores), max(pass_at_1_scores)
        
        if max_score - min_score > 0.3:
            insights.append(f"Large performance gap observed: {max_score:.1%} - {min_score:.1%} spread in pass@1 scores.")
        else:
            insights.append("Models showed relatively similar performance levels.")
        
        # Quality vs Performance analysis
        avg_quality = sum(p.average_quality_score for p in benchmark_run.model_performances) / len(benchmark_run.model_performances)
        avg_pass_rate = sum(p.pass_at_1 for p in benchmark_run.model_performances) / len(benchmark_run.model_performances)
        
        if avg_quality > 70 and avg_pass_rate > 0.7:
            insights.append("Models generally produced both correct and high-quality code.")
        elif avg_quality > 70:
            insights.append("Models focused on code quality but struggled with correctness.")
        elif avg_pass_rate > 0.7:
            insights.append("Models achieved good correctness but with lower code quality.")
        
        # Execution time analysis
        avg_exec_time = sum(p.average_execution_time for p in benchmark_run.model_performances) / len(benchmark_run.model_performances)
        if avg_exec_time > 1.0:
            insights.append("Generated solutions had relatively slow execution times, suggesting algorithmic inefficiencies.")
        
        return insights