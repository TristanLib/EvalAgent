# EvalAgent - LLM Coding Evaluation Framework

A comprehensive AI agent for evaluating the coding abilities of popular Large Language Models (LLMs).

## Features

- **Multi-Framework Support**: Implements HumanEval, MBPP, and custom evaluation benchmarks
- **Multiple LLM APIs**: Support for OpenAI, Anthropic, Google, and other popular LLM providers
- **Comprehensive Metrics**: Pass@k, functional correctness, code quality analysis
- **Real-world Testing**: Bug fixing, code completion, and refactoring tasks
- **Detailed Reporting**: JSON, CSV, and HTML report generation
- **Extensible Architecture**: Easy to add new benchmarks and evaluation criteria

## Architecture

```
EvalAgent/
├── src/
│   ├── agents/           # Evaluation agents
│   ├── benchmarks/       # Benchmark implementations
│   ├── evaluators/       # Code evaluation logic
│   ├── llm_clients/      # LLM API clients
│   ├── metrics/          # Evaluation metrics
│   └── reporters/        # Result reporting
├── tests/                # Test suites
├── benchmarks/           # Benchmark datasets
└── config/              # Configuration files
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your API keys

# Run evaluation
python -m evalagent --benchmark humaneval --models gpt-4,claude-3-sonnet --output results/
```

## Supported Benchmarks

- **HumanEval**: 164 Python programming problems
- **MBPP**: 974 basic programming problems  
- **BigCodeBench**: Complex real-world coding tasks
- **Custom**: Define your own evaluation criteria

## Supported LLMs

- OpenAI (GPT-3.5, GPT-4, GPT-4-turbo)
- Anthropic (Claude-3-haiku, Claude-3-sonnet, Claude-3-opus)
- Google (Gemini Pro, Gemini Ultra)
- Cohere (Command-R, Command-R+)
- Open source models via Hugging Face

## Evaluation Metrics

- **Pass@k**: Probability of k attempts passing tests
- **Functional Correctness**: Code execution success rate
- **Code Quality**: Style, complexity, and maintainability scores
- **Performance**: Execution time and memory usage
- **Security**: Static analysis for common vulnerabilities