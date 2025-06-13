"""Example usage of EvalAgent with Ollama local models"""

import asyncio
from src.agents import EvaluationAgent
from src.models import BenchmarkType, LLMConfig
from src.benchmarks import BenchmarkLoader
from src.reporters import JSONReporter, HTMLReporter
from src.llm_clients import OllamaClient


async def main():
    """Example of running EvalAgent with Ollama models"""
    
    print("🦙 EvalAgent + Ollama Example")
    print("=" * 35)
    
    # Check Ollama server status first
    print("🔍 Checking Ollama server status...")
    
    ollama_config = LLMConfig(
        name="ollama-check",
        api_key="not_required",
        base_url="http://localhost:11434",
        model_id="dummy"
    )
    
    client = OllamaClient(ollama_config)
    status = client.check_server_status()
    
    if status['status'] != 'running':
        print(f"❌ Ollama server is not running: {status.get('error', 'Unknown error')}")
        print("💡 Make sure to start Ollama server: ollama serve")
        return
    
    print(f"✅ Ollama server is running with {status['model_count']} models")
    
    if not status['available_models']:
        print("⚠️  No models found on Ollama server")
        print("💡 Pull some models first:")
        print("   ollama pull llama3:8b")
        print("   ollama pull codellama:7b")
        return
    
    # Configure Ollama models (use first available model)
    available_model = status['available_models'][0]
    print(f"🤖 Using model: {available_model}")
    
    llm_configs = [
        LLMConfig(
            name=f"ollama-{available_model}",
            api_key="not_required",  # Ollama doesn't need API keys
            base_url="http://localhost:11434",
            model_id=available_model,
            temperature=0.1,
            max_tokens=2048,
            timeout=60  # Longer timeout for local models
        )
    ]
    
    # Load benchmark (use fewer problems for demo)
    loader = BenchmarkLoader()
    problems = loader.load_benchmark(BenchmarkType.HUMANEVAL)
    problems = problems[:2]  # Use only 2 problems for quick demo
    
    print(f"📚 Loaded {len(problems)} problems")
    print(f"🤖 Testing {len(llm_configs)} models")
    
    # Create evaluation agent
    config = {
        'timeout': 60,  # Longer timeout for local models
        'temperature': 0.1,
        'max_tokens': 2048
    }
    
    agent = EvaluationAgent(config)
    
    # Run evaluation
    print("🚀 Starting evaluation...")
    
    benchmark_run = await agent.run_benchmark(
        BenchmarkType.HUMANEVAL,
        problems,
        llm_configs,
        max_workers=1  # Use 1 worker for local models to avoid overload
    )
    
    # Generate summary
    summary = agent.generate_summary_report(benchmark_run)
    
    # Display results
    print("\n📊 Results:")
    for ranking in summary['model_rankings']:
        print(f"  {ranking['rank']}. {ranking['model']}: {ranking['pass_at_1']*100:.1f}% pass rate")
        print(f"     Quality Score: {ranking['avg_quality_score']:.1f}")
        print(f"     Problems Solved: {ranking['problems_solved']}/{ranking['total_problems']}")
    
    # Show insights
    if summary.get('insights'):
        print("\n💡 Insights:")
        for insight in summary['insights']:
            print(f"  • {insight}")
    
    # Generate reports
    json_reporter = JSONReporter("results")
    html_reporter = HTMLReporter("results")
    
    json_file = json_reporter.generate_report(benchmark_run, summary)
    html_file = html_reporter.generate_report(benchmark_run, summary)
    
    print(f"\n📁 Reports generated:")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")
    
    # Show example of generated code
    if benchmark_run.results:
        result = benchmark_run.results[0]
        print(f"\n🔍 Example generated code for problem '{result.problem_id}':")
        print("-" * 50)
        print(result.generated_code.code)
        print("-" * 50)
        print(f"Status: {'✅ Passed' if result.execution_result.passed else '❌ Failed'}")
        if result.execution_result.error_message:
            print(f"Error: {result.execution_result.error_message}")


if __name__ == "__main__":
    print("🦙 EvalAgent Ollama Example")
    print("=" * 30)
    print("Prerequisites:")
    print("1. Install Ollama: https://ollama.ai/")
    print("2. Start server: ollama serve")
    print("3. Pull models: ollama pull llama3:8b")
    print("=" * 30)
    
    # Run the example
    asyncio.run(main())