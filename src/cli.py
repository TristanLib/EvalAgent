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
@click.option('--url', '-u', 
              default='http://localhost:11434',
              help='Ollama server URL')
def ollama_status(url: str):
    """Check Ollama server status and available models"""
    
    console.print("🦙 [bold blue]Ollama Server Status[/bold blue]")
    console.print("=" * 30)
    
    from .llm_clients.ollama_client import OllamaClient
    from .models import LLMConfig
    
    # Create a dummy config to check server status
    config = LLMConfig(
        name="ollama-check",
        api_key="not_required",
        base_url=url,
        model_id="dummy"
    )
    
    client = OllamaClient(config)
    status = client.check_server_status()
    
    if status['status'] == 'running':
        console.print(f"✅ [green]Server Status:[/green] {status['status'].title()}")
        console.print(f"🌐 [bold]URL:[/bold] {status['url']}")
        console.print(f"📊 [bold]Available Models:[/bold] {status['model_count']}")
        
        if status['available_models']:
            console.print("\n📋 [bold]Models:[/bold]")
            for model in status['available_models']:
                console.print(f"  • {model}")
        else:
            console.print("\n[yellow]No models found. Use 'ollama pull <model>' to download models.[/yellow]")
    
    elif status['status'] == 'offline':
        console.print(f"❌ [red]Server Status:[/red] Offline")
        console.print(f"🌐 [bold]URL:[/bold] {status['url']}")
        console.print(f"[yellow]Make sure Ollama is running: ollama serve[/yellow]")
    
    else:
        console.print(f"⚠️  [yellow]Server Status:[/yellow] {status['status'].title()}")
        console.print(f"🌐 [bold]URL:[/bold] {status['url']}")
        console.print(f"[red]Error:[/red] {status.get('error', 'Unknown error')}")


@cli.command()
@click.argument('model_name')
@click.option('--url', '-u', 
              default='http://localhost:11434',
              help='Ollama server URL')
def ollama_pull(model_name: str, url: str):
    """Pull a model to Ollama server"""
    
    console.print(f"🦙 [bold blue]Pulling Ollama Model: {model_name}[/bold blue]")
    console.print("=" * 50)
    
    from .llm_clients.ollama_client import OllamaClient
    from .models import LLMConfig
    
    config = LLMConfig(
        name="ollama-pull",
        api_key="not_required",
        base_url=url,
        model_id=model_name
    )
    
    client = OllamaClient(config)
    
    with console.status(f"[bold green]Pulling {model_name}..."):
        success = client.pull_model(model_name)
    
    if success:
        console.print(f"✅ [green]Successfully pulled model: {model_name}[/green]")
    else:
        console.print(f"❌ [red]Failed to pull model: {model_name}[/red]")


@cli.command()
@click.option('--dataset', '-d',
              help='Download specific dataset (humaneval, mbpp, humaneval_plus, mbpp_plus)')
@click.option('--all', 'download_all', is_flag=True,
              help='Download all available datasets')
@click.option('--force', is_flag=True,
              help='Force re-download even if dataset exists')
def download_benchmarks(dataset: str, download_all: bool, force: bool):
    """Download official benchmark datasets"""
    
    from .benchmarks.dataset_downloader import BenchmarkDownloader
    
    console.print("📥 [bold blue]Benchmark Dataset Downloader[/bold blue]")
    console.print("=" * 40)
    
    downloader = BenchmarkDownloader()
    
    if download_all:
        console.print("Downloading all available datasets...")
        results = downloader.download_all(force=force)
        
        console.print("\n📊 [bold]Download Results:[/bold]")
        for name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            console.print(f"  • {name}: {status}")
    
    elif dataset:
        if dataset not in downloader.DATASETS:
            console.print(f"[red]Error: Unknown dataset '{dataset}'[/red]")
            console.print("Available datasets:")
            for name in downloader.DATASETS:
                console.print(f"  • {name}")
            return
        
        success = downloader.download_dataset(dataset, force=force)
        if success:
            console.print(f"✅ [green]Successfully downloaded {dataset}[/green]")
        else:
            console.print(f"❌ [red]Failed to download {dataset}[/red]")
    
    else:
        # Show available datasets
        console.print("📋 [bold]Available Benchmark Datasets[/bold]")
        
        datasets = downloader.list_available_datasets()
        for name, info in datasets.items():
            is_downloaded = downloader.is_downloaded(name)
            status = "✅ Downloaded" if is_downloaded else "⬜ Not downloaded"
            
            console.print(f"\n[bold]{name}[/bold] - {status}")
            console.print(f"  Description: {info['description']}")
            console.print(f"  Size: {info['size']}")
            console.print(f"  License: {info['license']}")
            
            if is_downloaded:
                try:
                    detailed_info = downloader.get_dataset_info(name)
                    if 'problem_count' in detailed_info:
                        console.print(f"  Problems: {detailed_info['problem_count']}")
                    if 'local_size' in detailed_info:
                        console.print(f"  Local size: {detailed_info['local_size']}")
                except:
                    pass
        
        console.print(f"\n💡 [yellow]Usage:[/yellow]")
        console.print("  Download specific: evalagent download-benchmarks --dataset humaneval")
        console.print("  Download all: evalagent download-benchmarks --all")


@cli.command()
@click.option('--benchmark', '-b',
              type=click.Choice(['humaneval', 'mbpp', 'custom']),
              default='humaneval',
              help='Benchmark to inspect')
@click.option('--problem-id', '-p',
              help='Show details for specific problem ID')
@click.option('--limit', '-l',
              type=int, default=5,
              help='Number of problems to show (default: 5)')
@click.option('--show-tests', is_flag=True,
              help='Show test cases for each problem')
def inspect_benchmarks(benchmark: str, problem_id: str, limit: int, show_tests: bool):
    """Inspect benchmark problems and test cases"""
    
    console.print(f"🔍 [bold blue]Inspecting {benchmark.title()} Benchmark[/bold blue]")
    console.print("=" * 50)
    
    from .benchmarks import BenchmarkLoader
    from .models import BenchmarkType
    
    try:
        loader = BenchmarkLoader()
        benchmark_type = BenchmarkType(benchmark)
        problems = loader.load_benchmark(benchmark_type)
        
        console.print(f"📊 [bold]Total problems:[/bold] {len(problems)}")
        
        if problem_id:
            # Show specific problem
            problem = next((p for p in problems if p.id == problem_id), None)
            if not problem:
                console.print(f"[red]Problem '{problem_id}' not found[/red]")
                console.print("Available problem IDs:")
                for p in problems[:10]:
                    console.print(f"  • {p.id}")
                return
            
            problems = [problem]
            limit = 1
        
        # Show problems
        for i, problem in enumerate(problems[:limit]):
            console.print(f"\n📋 [bold]Problem {i+1}: {problem.id}[/bold]")
            console.print(f"Title: {problem.title}")
            console.print(f"Difficulty: {problem.difficulty}")
            console.print(f"Category: {problem.category}")
            
            console.print(f"\n[bold]Description:[/bold]")
            console.print(problem.description[:200] + "..." if len(problem.description) > 200 else problem.description)
            
            console.print(f"\n[bold]Function signature:[/bold]")
            console.print(problem.function_signature)
            
            if problem.docstring:
                console.print(f"\n[bold]Docstring:[/bold]")
                console.print(problem.docstring)
            
            if show_tests:
                console.print(f"\n[bold]Test cases ({len(problem.test_cases)}):[/bold]")
                for j, test_case in enumerate(problem.test_cases):
                    console.print(f"  Test {j+1}:")
                    console.print(f"    Type: {test_case.test_type}")
                    if test_case.input_data:
                        console.print(f"    Input: {test_case.input_data}")
                    if test_case.expected_output:
                        console.print(f"    Expected: {test_case.expected_output}")
            else:
                console.print(f"\n[bold]Test cases:[/bold] {len(problem.test_cases)} (use --show-tests to view)")
            
            if i < len(problems[:limit]) - 1:
                console.print("-" * 50)
        
        if len(problems) > limit and not problem_id:
            console.print(f"\n... and {len(problems) - limit} more problems")
            console.print(f"Use --limit {len(problems)} to see all")
    
    except Exception as e:
        console.print(f"[red]Error loading benchmark: {e}[/red]")


@cli.command()
@click.argument('benchmark_report_path')
@click.option('--format', 'output_format',
              type=click.Choice(['summary', 'detailed', 'problems']),
              default='summary',
              help='Report detail level')
def show_test_results(benchmark_report_path: str, output_format: str):
    """Show which tests were used and their results from a completed benchmark"""
    
    console.print("📊 [bold blue]Benchmark Test Results Analysis[/bold blue]")
    console.print("=" * 50)
    
    try:
        import json
        
        with open(benchmark_report_path, 'r') as f:
            report_data = json.load(f)
        
        metadata = report_data.get('metadata', {})
        console.print(f"📋 [bold]Benchmark:[/bold] {metadata.get('benchmark_type', 'Unknown')}")
        console.print(f"🕐 [bold]Date:[/bold] {metadata.get('report_generated', 'Unknown')}")
        console.print(f"🤖 [bold]Models:[/bold] {', '.join(metadata.get('models_evaluated', []))}")
        console.print(f"📊 [bold]Total Problems:[/bold] {metadata.get('problems_count', 0)}")
        console.print(f"🧪 [bold]Total Evaluations:[/bold] {metadata.get('total_evaluations', 0)}")
        
        if output_format == 'summary':
            # Show summary statistics
            summary = report_data.get('summary', {})
            if 'statistics' in summary:
                overall = summary['statistics'].get('overall', {})
                console.print(f"\n📈 [bold]Overall Results:[/bold]")
                console.print(f"  Success Rate: {overall.get('overall_success_rate', 0) * 100:.1f}%")
                console.print(f"  Avg Execution Time: {overall.get('average_execution_time', 0):.3f}s")
                console.print(f"  Avg Quality Score: {overall.get('average_quality_score', 0):.1f}")
        
        elif output_format == 'detailed':
            # Show detailed results for each model
            detailed_results = report_data.get('detailed_results', [])
            
            # Group by model
            by_model = {}
            for result in detailed_results:
                model = result['model_name']
                if model not in by_model:
                    by_model[model] = []
                by_model[model].append(result)
            
            for model, results in by_model.items():
                console.print(f"\n🤖 [bold]{model}[/bold]")
                passed = sum(1 for r in results if r['execution_result']['passed'])
                console.print(f"  Results: {passed}/{len(results)} passed ({passed/len(results)*100:.1f}%)")
                
                failed_problems = [r['problem_id'] for r in results if not r['execution_result']['passed']]
                if failed_problems:
                    console.print(f"  Failed problems: {', '.join(failed_problems[:5])}")
                    if len(failed_problems) > 5:
                        console.print(f"    ... and {len(failed_problems) - 5} more")
        
        elif output_format == 'problems':
            # Show results per problem
            detailed_results = report_data.get('detailed_results', [])
            
            # Group by problem
            by_problem = {}
            for result in detailed_results:
                problem = result['problem_id']
                if problem not in by_problem:
                    by_problem[problem] = []
                by_problem[problem].append(result)
            
            console.print(f"\n📋 [bold]Problem-wise Results:[/bold]")
            for problem_id, results in sorted(by_problem.items()):
                passed = sum(1 for r in results if r['execution_result']['passed'])
                console.print(f"\n  {problem_id}: {passed}/{len(results)} models passed")
                
                for result in results:
                    status = "✅" if result['execution_result']['passed'] else "❌"
                    model = result['model_name']
                    console.print(f"    {status} {model}")
                    
                    if not result['execution_result']['passed'] and result['execution_result']['error_message']:
                        error = result['execution_result']['error_message'][:100]
                        console.print(f"      Error: {error}...")
    
    except FileNotFoundError:
        console.print(f"[red]Report file not found: {benchmark_report_path}[/red]")
    except json.JSONDecodeError:
        console.print(f"[red]Invalid JSON format in report file[/red]")
    except Exception as e:
        console.print(f"[red]Error reading report: {e}[/red]")


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