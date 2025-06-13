"""HTML report generation"""

import os
from datetime import datetime
from typing import Dict, Any
from jinja2 import Template

from ..models import BenchmarkRun


class HTMLReporter:
    """Generates HTML reports from benchmark results"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, benchmark_run: BenchmarkRun, summary: Dict[str, Any]) -> str:
        """Generate an interactive HTML report"""
        
        template = self._get_html_template()
        
        # Prepare data for template
        template_data = {
            'benchmark_run': benchmark_run,
            'summary': summary,
            'generated_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'duration': benchmark_run.end_time - benchmark_run.start_time if benchmark_run.end_time else 0,
            'model_performances': benchmark_run.model_performances,
            'detailed_results': benchmark_run.results[:50],  # Limit for performance
            'chart_data': self._prepare_chart_data(benchmark_run, summary)
        }
        
        # Render template
        html_content = template.render(**template_data)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{benchmark_run.benchmark_type.value}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _prepare_chart_data(self, benchmark_run: BenchmarkRun, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for charts and visualizations"""
        
        chart_data = {}
        
        # Model performance comparison
        if benchmark_run.model_performances:
            chart_data['model_comparison'] = {
                'labels': [p.model_name for p in benchmark_run.model_performances],
                'pass_at_1': [p.pass_at_1 * 100 for p in benchmark_run.model_performances],
                'quality_scores': [p.average_quality_score for p in benchmark_run.model_performances],
                'execution_times': [p.average_execution_time for p in benchmark_run.model_performances]
            }
        
        # Success rate distribution
        if 'by_model' in summary.get('statistics', {}):
            model_stats = summary['statistics']['by_model']
            chart_data['success_distribution'] = {
                'labels': list(model_stats.keys()),
                'success_rates': [stats['success_rate'] * 100 for stats in model_stats.values()]
            }
        
        # Problem difficulty analysis (simplified)
        difficulty_stats = {}
        for result in benchmark_run.results:
            difficulty = self._infer_difficulty(result)
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'total': 0, 'passed': 0}
            difficulty_stats[difficulty]['total'] += 1
            if result.execution_result.passed:
                difficulty_stats[difficulty]['passed'] += 1
        
        chart_data['difficulty_analysis'] = {
            'labels': list(difficulty_stats.keys()),
            'success_rates': [
                stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
                for stats in difficulty_stats.values()
            ]
        }
        
        return chart_data
    
    def _infer_difficulty(self, result) -> str:
        """Infer problem difficulty (simplified heuristic)"""
        exec_time = result.execution_result.execution_time
        complexity = result.quality_metrics.cyclomatic_complexity
        
        if exec_time > 1.0 or complexity > 10:
            return 'Hard'
        elif exec_time > 0.1 or complexity > 5:
            return 'Medium'
        else:
            return 'Easy'
    
    def _get_html_template(self) -> Template:
        """Get the HTML template for the report"""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvalAgent Benchmark Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .header { text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid #eee; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; }
        .summary-card .value { font-size: 28px; font-weight: bold; color: #007bff; }
        .chart-container { margin: 40px 0; }
        .chart-wrapper { position: relative; height: 400px; margin: 20px 0; }
        .model-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .model-table th, .model-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .model-table th { background-color: #f8f9fa; font-weight: bold; }
        .model-table tr:hover { background-color: #f5f5f5; }
        .status-badge { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; text-transform: uppercase; }
        .status-completed { background-color: #28a745; }
        .status-failed { background-color: #dc3545; }
        .insights { background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .insights ul { margin: 0; padding-left: 20px; }
        .insights li { margin: 10px 0; }
        .top-performers { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .performer-card { background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 EvalAgent Benchmark Report</h1>
            <p><strong>Benchmark:</strong> {{ benchmark_run.benchmark_type.value.title() }} | 
               <strong>Generated:</strong> {{ generated_time }} | 
               <strong>Duration:</strong> {{ "%.2f"|format(duration) }}s</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Models Evaluated</h3>
                <div class="value">{{ benchmark_run.models_evaluated|length }}</div>
            </div>
            <div class="summary-card">
                <h3>Problems Tested</h3>
                <div class="value">{{ benchmark_run.problems_count }}</div>
            </div>
            <div class="summary-card">
                <h3>Total Evaluations</h3>
                <div class="value">{{ benchmark_run.results|length }}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value">{{ "%.1f"|format(summary.statistics.overall.overall_success_rate * 100) }}%</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>📊 Model Performance Comparison</h2>
            <div class="chart-wrapper">
                <canvas id="modelComparisonChart"></canvas>
            </div>
        </div>

        <div class="top-performers">
            <h2>🏆 Top Performers</h2>
            {% for category, model in summary.top_performers.items() %}
            <div class="performer-card">
                <h4>{{ category.replace('_', ' ').title() }}</h4>
                <p><strong>{{ model }}</strong></p>
            </div>
            {% endfor %}
        </div>

        <div class="insights">
            <h2>💡 Key Insights</h2>
            <ul>
                {% for insight in summary.insights %}
                <li>{{ insight }}</li>
                {% endfor %}
            </ul>
        </div>

        <h2>📈 Model Performance Details</h2>
        <table class="model-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Pass@1</th>
                    <th>Pass@5</th>
                    <th>Pass@10</th>
                    <th>Problems Solved</th>
                    <th>Quality Score</th>
                    <th>Avg Execution Time</th>
                </tr>
            </thead>
            <tbody>
                {% for ranking in summary.model_rankings %}
                <tr>
                    <td><strong>{{ ranking.rank }}</strong></td>
                    <td>{{ ranking.model }}</td>
                    <td>{{ "%.1f"|format(ranking.pass_at_1 * 100) }}%</td>
                    <td>{{ "%.1f"|format(ranking.pass_at_5 * 100) }}%</td>
                    <td>{{ "%.1f"|format(ranking.pass_at_10 * 100) }}%</td>
                    <td>{{ ranking.problems_solved }}/{{ ranking.total_problems }}</td>
                    <td>{{ "%.1f"|format(ranking.avg_quality_score) }}</td>
                    <td>{{ "%.3f"|format(model_performances[loop.index0].average_execution_time) }}s</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by <strong>EvalAgent</strong> - LLM Coding Evaluation Framework</p>
        </div>
    </div>

    <script>
        // Model Performance Comparison Chart
        const ctx = document.getElementById('modelComparisonChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{ chart_data.model_comparison.labels | tojson }},
                datasets: [{
                    label: 'Pass@1 (%)',
                    data: {{ chart_data.model_comparison.pass_at_1 | tojson }},
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }, {
                    label: 'Quality Score',
                    data: {{ chart_data.model_comparison.quality_scores | tojson }},
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Pass@1 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Quality Score'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Model Performance: Pass@1 Rate vs Code Quality'
                    },
                    legend: {
                        display: true
                    }
                }
            }
        });
    </script>
</body>
</html>
        """
        
        return Template(template_str)