"""Example usage of EvalAgent"""

import asyncio
from src.agents import EvaluationAgent
from src.models import BenchmarkType, LLMConfig
from src.benchmarks import BenchmarkLoader
from src.reporters import JSONReporter, HTMLReporter


async def main():
    """Example of running EvalAgent programmatically"""
    
    print("🤖 EvalAgent Example")
    print("=" * 30)
    
    # Configure LLMs (you need to add your API keys)
    llm_configs = [
        LLMConfig(
            name="gpt-3.5-turbo",
            api_key="your_openai_api_key_here",
            base_url="https://api.openai.com/v1",
            model_id="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=2048
        ),
        # Add more models as needed
    ]
    
    # Load benchmark
    loader = BenchmarkLoader()
    problems = loader.load_benchmark(BenchmarkType.HUMANEVAL)
    
    # Limit problems for this example
    problems = problems[:3]
    
    print(f"📚 Loaded {len(problems)} problems")
    print(f"🤖 Testing {len(llm_configs)} models")
    
    # Create evaluation agent
    config = {
        'timeout': 10,
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
        max_workers=2
    )
    
    # Generate summary
    summary = agent.generate_summary_report(benchmark_run)
    
    # Display results
    print("\n📊 Results:")
    for ranking in summary['model_rankings']:
        print(f"  {ranking['rank']}. {ranking['model']}: {ranking['pass_at_1']*100:.1f}% pass rate")
    
    # Generate reports
    json_reporter = JSONReporter("results")
    html_reporter = HTMLReporter("results")
    
    json_file = json_reporter.generate_report(benchmark_run, summary)
    html_file = html_reporter.generate_report(benchmark_run, summary)
    
    print(f"\n📁 Reports generated:")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")


if __name__ == "__main__":
    # Note: You need to add your API keys to make this work
    print("⚠️  Remember to add your API keys in the LLMConfig objects above!")
    print("💡 For a complete example with configuration file, use the CLI:")
    print("   python -m src.cli run --models gpt-3.5-turbo")
    
    # Uncomment to run the example:
    # asyncio.run(main())