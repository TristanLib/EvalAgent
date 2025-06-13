# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EvalAgent is a comprehensive AI agent for evaluating the coding abilities of popular Large Language Models (LLMs). It supports multiple evaluation frameworks, LLM APIs, and generates detailed reports with visualizations.

## Build and Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m src.cli init
```

### Configuration
```bash
# Copy and edit configuration file
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys
```

### Running Evaluations
```bash
# List available models
python -m src.cli list-models

# Run evaluation with specific models
python -m src.cli run --models gpt-4,claude-3-sonnet --benchmark humaneval

# Run with local Ollama models
python -m src.cli run --models llama3:8b,codellama:7b --benchmark humaneval

# Run with custom options
python -m src.cli run --models gpt-3.5-turbo --benchmark humaneval --problems-limit 5 --max-workers 2 --formats json,html
```

### Development
```bash
# Run example
python example.py

# Install in development mode
pip install -e .

# Run CLI directly after installation
evalagent run --models gpt-4 --benchmark humaneval

# Ollama management commands
python -m src.cli ollama-status
python -m src.cli ollama-pull llama3:8b

# Benchmark management commands
python -m src.cli download-benchmarks --all
python -m src.cli inspect-benchmarks --benchmark humaneval --show-tests
python -m src.cli show-test-results results/benchmark_report_*.json
```

## Architecture Overview

- **src/agents/**: Core evaluation orchestration
- **src/benchmarks/**: Benchmark implementations (HumanEval, MBPP, etc.)
- **src/evaluators/**: Code execution, quality analysis, metrics calculation
- **src/llm_clients/**: LLM API clients (OpenAI, Anthropic, etc.)
- **src/reporters/**: Report generation (JSON, CSV, HTML)
- **src/models.py**: Core data models and types
- **src/cli.py**: Command-line interface

## Key Features

- Multi-framework support (HumanEval, MBPP, custom benchmarks)
- Multiple LLM APIs (OpenAI, Anthropic, Google, Cohere)
- Comprehensive metrics (Pass@k, code quality, performance)
- Rich reporting with visualizations
- Parallel execution for performance
- Extensible architecture