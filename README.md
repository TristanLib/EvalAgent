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
python -m evalagent --benchmark humaneval --models gpt-4,claude-3-sonnet,llama3:8b --output results/
```

## Supported Benchmarks

EvalAgent supports both **official third-party benchmarks** and **custom evaluation criteria**:

### Official Benchmarks
- **HumanEval**: 164 Python programming problems from OpenAI
- **MBPP**: 974 basic programming problems from Google Research  
- **HumanEval+**: Enhanced version with more comprehensive test cases
- **MBPP+**: Enhanced version with more comprehensive test cases
- **Custom**: Define your own evaluation criteria

### Benchmark Management
```bash
# Download official benchmark datasets
python -m src.cli download-benchmarks --all

# Download specific benchmark
python -m src.cli download-benchmarks --dataset humaneval

# Inspect benchmark problems and tests
python -m src.cli inspect-benchmarks --benchmark humaneval --show-tests

# View test results from completed evaluation
python -m src.cli show-test-results results/benchmark_report_*.json --format detailed
```

## Supported LLMs

- **OpenAI** (GPT-3.5, GPT-4, GPT-4-turbo)
- **Anthropic** (Claude-3-haiku, Claude-3-sonnet, Claude-3-opus)
- **Ollama** (Local models: Llama3, CodeLlama, Mistral, Mixtral, Vicuna, etc.)
- **Google** (Gemini Pro, Gemini Ultra)
- **Cohere** (Command-R, Command-R+)
- **Open source models** via Hugging Face

## Evaluation Metrics

- **Pass@k**: Probability of k attempts passing tests
- **Functional Correctness**: Code execution success rate
- **Code Quality**: Style, complexity, and maintainability scores
- **Performance**: Execution time and memory usage
- **Security**: Static analysis for common vulnerabilities

## Using Ollama (Local Models)

EvalAgent supports local model evaluation via [Ollama](https://ollama.ai/), allowing you to test open-source models without API costs.

### Setup Ollama

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/download
   ```

2. **Start Ollama server**:
   ```bash
   ollama serve
   ```

3. **Pull models for evaluation**:
   ```bash
   # Pull specific models
   ollama pull llama3:8b
   ollama pull codellama:7b
   ollama pull mistral:7b
   
   # Or use EvalAgent to pull models
   python -m src.cli ollama-pull llama3:8b
   python -m src.cli ollama-pull codellama:13b
   ```

4. **Check server status**:
   ```bash
   python -m src.cli ollama-status
   ```

5. **Run evaluation with local models**:
   ```bash
   python -m src.cli run --models llama3:8b,codellama:7b,mistral:7b --benchmark humaneval
   ```

### Popular Coding Models for Ollama

- **CodeLlama**: `codellama:7b`, `codellama:13b`, `codellama:34b`
- **Llama3**: `llama3:8b`, `llama3:70b`
- **Mistral**: `mistral:7b`, `mixtral:8x7b`
- **Specialized**: `wizard-vicuna-uncensored:7b`, `orca-mini:3b`