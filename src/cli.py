"""Command line interface for EvalAgent"""

import asyncio
import os
import yaml
from typing import List, Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .agents import EvaluationAgent
from .models import BenchmarkType, LLMConfig, Problem, TestCase
from .benchmarks import BenchmarkLoader
from .reporters import JSONReporter, CSVReporter, HTMLReporter


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """EvalAgent - LLM Coding Evaluation Framework"""
    pass


@cli.command()
@click.option('--benchmark', '-b', 
              type=click.Choice(['humaneval', 'mbpp', 'custom']), 
              default='humaneval',
              help='Benchmark to run')
@click.option('--models', '-m', 
              help='Comma-separated list of model names to evaluate')
@click.option('--config', '-c', 
              default='config/config.yaml',
              help='Path to configuration file')
@click.option('--output', '-o', 
              default='results/',
              help='Output directory for results')
@click.option('--formats', '-f',
              default='json,csv,html',
              help='Output formats (comma-separated)')
@click.option('--max-workers', '-w',
              default=4,
              help='Maximum number of parallel workers')
@click.option('--problems-limit', '-p',
              type=int,
              help='Limit number of problems (for testing)')
def run(benchmark: str, models: str, config: str, output: str, formats: str, max_workers: int, problems_limit: int):
    """Run LLM evaluation benchmark"""
    
    console.print("🤖 [bold blue]EvalAgent - LLM Coding Evaluation[/bold blue]")
    console.print("=" * 50)
    
    # Load configuration
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: Configuration file not found: {config}[/red]")
        console.print(f"[yellow]Please copy {config}.example to {config} and configure your API keys[/yellow]")
        return
    
    # Parse models
    if not models:
        console.print("[red]Error: No models specified. Use --models option[/red]")
        return
    
    model_names = [m.strip() for m in models.split(',')]
    console.print(f"📋 Models to evaluate: {', '.join(model_names)}")
    
    # Create LLM configurations
    llm_configs = []
    for model_name in model_names:
        llm_config = _create_llm_config(model_name, config_data)
        if llm_config:
            llm_configs.append(llm_config)
        else:
            console.print(f"[yellow]Warning: Could not create config for model {model_name}[/yellow]")
    
    if not llm_configs:
        console.print("[red]Error: No valid model configurations found[/red]")
        return
    
    # Load benchmark
    console.print(f"📚 Loading {benchmark} benchmark...")
    benchmark_type = BenchmarkType(benchmark)
    
    try:
        loader = BenchmarkLoader()
        problems = loader.load_benchmark(benchmark_type)
        
        if problems_limit:
            problems = problems[:problems_limit]
            console.print(f"[yellow]Limited to {len(problems)} problems for testing[/yellow]")
        
        console.print(f"✅ Loaded {len(problems)} problems")
        
    except Exception as e:
        console.print(f"[red]Error loading benchmark: {str(e)}[/red]")
        return
    
    # Run evaluation
    console.print(f"🚀 Starting evaluation with {max_workers} workers...")
    
    agent = EvaluationAgent(config_data.get('evaluation', {}))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running evaluation...", total=None)
            
            # Run the benchmark
            benchmark_run = asyncio.run(
                agent.run_benchmark(benchmark_type, problems, llm_configs, max_workers)
            )
            
            progress.update(task, description="Generating reports...")
            
            # Generate summary
            summary = agent.generate_summary_report(benchmark_run)
            
            # Generate reports
            output_formats = [f.strip() for f in formats.split(',')]
            report_files = _generate_reports(benchmark_run, summary, output, output_formats)
            
            progress.remove_task(task)
        
        # Display results
        _display_results(summary)
        
        console.print(f"\n📁 [green]Reports generated:[/green]")
        for file in report_files:
            console.print(f"  • {file}")
            
    except Exception as e:
        console.print(f"[red]Error during evaluation: {str(e)}[/red]")
        raise


@cli.command()
@click.option('--config', '-c', 
              default='config/config.yaml',
              help='Path to configuration file')
def list_models(config: str):
    """List available models from configuration"""
    
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: Configuration file not found: {config}[/red]")
        return
    
    console.print("🤖 [bold blue]Available Models[/bold blue]")
    console.print("=" * 30)
    
    for provider, provider_config in config_data.get('llm_apis', {}).items():
        if 'models' in provider_config:
            console.print(f"\n[bold]{provider.title()}:[/bold]")
            for model in provider_config['models']:
                console.print(f"  • {model}")


@cli.command()
def init():
    """Initialize EvalAgent with example configuration"""
    
    config_dir = "config"
    results_dir = "results"
    logs_dir = "logs"
    
    # Create directories
    for directory in [config_dir, results_dir, logs_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Copy example config if it doesn't exist
    config_file = os.path.join(config_dir, "config.yaml")
    example_config = os.path.join(config_dir, "config.example.yaml")
    
    if not os.path.exists(config_file) and os.path.exists(example_config):
        import shutil
        shutil.copy(example_config, config_file)
        console.print(f"✅ Created configuration file: {config_file}")
        console.print(f"[yellow]Please edit {config_file} and add your API keys[/yellow]")
    else:
        console.print(f"ℹ️  Configuration file already exists: {config_file}")
    
    console.print("\n🎉 [green]EvalAgent initialized successfully![/green]")
    console.print("\nNext steps:")
    console.print("1. Edit config/config.yaml with your API keys")
    console.print("2. Run: evalagent run --models gpt-4,claude-3-sonnet")


def _create_llm_config(model_name: str, config_data: Dict[str, Any]) -> LLMConfig:
    """Create LLM configuration from model name and config data"""
    
    # Find the model in configuration
    for provider, provider_config in config_data.get('llm_apis', {}).items():
        if model_name in provider_config.get('models', []):
            return LLMConfig(
                name=model_name,
                api_key=provider_config.get('api_key', ''),
                base_url=provider_config.get('base_url', ''),
                model_id=model_name,
                temperature=config_data.get('evaluation', {}).get('temperature', 0.1),
                max_tokens=config_data.get('evaluation', {}).get('max_tokens', 2048),
                timeout=config_data.get('evaluation', {}).get('timeout', 30),
                max_retries=config_data.get('evaluation', {}).get('max_retries', 3)
            )
    
    return None


def _generate_reports(benchmark_run, summary: Dict[str, Any], output_dir: str, formats: List[str]) -> List[str]:
    """Generate reports in specified formats"""
    
    os.makedirs(output_dir, exist_ok=True)
    report_files = []
    
    if 'json' in formats:
        json_reporter = JSONReporter(output_dir)
        json_file = json_reporter.generate_report(benchmark_run, summary)
        report_files.append(json_file)
    
    if 'csv' in formats:
        csv_reporter = CSVReporter(output_dir)
        csv_files = csv_reporter.generate_report(benchmark_run, summary)
        report_files.extend(csv_files)
    
    if 'html' in formats:
        html_reporter = HTMLReporter(output_dir)
        html_file = html_reporter.generate_report(benchmark_run, summary)
        report_files.append(html_file)
    
    return report_files


def _display_results(summary: Dict[str, Any]):
    """Display evaluation results in the console"""
    
    console.print("\n🏆 [bold green]Evaluation Results[/bold green]")
    console.print("=" * 50)
    
    # Overall statistics
    overall = summary.get('statistics', {}).get('overall', {})
    console.print(f"📊 [bold]Overall Success Rate:[/bold] {overall.get('overall_success_rate', 0) * 100:.1f}%")
    console.print(f"⏱️  [bold]Average Execution Time:[/bold] {overall.get('average_execution_time', 0):.3f}s")
    console.print(f"📈 [bold]Average Quality Score:[/bold] {overall.get('average_quality_score', 0):.1f}")
    
    # Model rankings table
    rankings = summary.get('model_rankings', [])
    if rankings:
        console.print("\n📋 [bold]Model Rankings[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Model", style="bold")
        table.add_column("Pass@1", justify="right")
        table.add_column("Pass@5", justify="right")
        table.add_column("Solved", justify="right")
        table.add_column("Quality", justify="right")
        
        for ranking in rankings[:10]:  # Show top 10
            table.add_row(
                str(ranking['rank']),
                ranking['model'],
                f"{ranking['pass_at_1'] * 100:.1f}%",
                f"{ranking['pass_at_5'] * 100:.1f}%",
                f"{ranking['problems_solved']}/{ranking['total_problems']}",
                f"{ranking['avg_quality_score']:.1f}"
            )
        
        console.print(table)
    
    # Top performers
    top_performers = summary.get('top_performers', {})
    if top_performers:
        console.print("\n🥇 [bold]Top Performers[/bold]")
        for category, model in top_performers.items():
            category_display = category.replace('_', ' ').title()
            console.print(f"  • [bold]{category_display}:[/bold] {model}")
    
    # Key insights
    insights = summary.get('insights', [])
    if insights:
        console.print("\n💡 [bold]Key Insights[/bold]")
        for insight in insights:
            console.print(f"  • {insight}")


if __name__ == '__main__':
    cli()