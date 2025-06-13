# EvalAgent Benchmarks Guide

This document explains EvalAgent's benchmark system, including official third-party datasets and how to inspect the tests being used.

## Overview

EvalAgent uses **official, well-established benchmarks** from the research community to ensure fair and standardized evaluation of LLM coding abilities. You can also inspect exactly which tests are being used for complete transparency.

## Supported Benchmarks

### 1. HumanEval (OpenAI)
- **Source**: [OpenAI Human-Eval](https://github.com/openai/human-eval)
- **Problems**: 164 Python programming tasks
- **License**: MIT
- **Description**: Hand-written programming problems with function signatures, docstrings, and test cases
- **Focus**: Algorithm implementation, data structures, string manipulation

### 2. MBPP (Google Research)
- **Source**: [Google Research MBPP](https://github.com/google-research/google-research/tree/master/mbpp)
- **Problems**: 974 Python programming tasks
- **License**: Apache 2.0
- **Description**: Mostly Basic Programming Problems covering fundamental programming concepts
- **Focus**: Basic programming skills, logic, simple algorithms

### 3. Enhanced Versions (EvalPlus)
- **HumanEval+**: Extended version with more comprehensive test cases
- **MBPP+**: Extended version with more comprehensive test cases
- **Source**: [EvalPlus Project](https://github.com/evalplus/evalplus)

## Using Official Benchmarks

### Download Datasets
```bash
# List available datasets
python -m src.cli download-benchmarks

# Download all official datasets
python -m src.cli download-benchmarks --all

# Download specific dataset
python -m src.cli download-benchmarks --dataset humaneval
python -m src.cli download-benchmarks --dataset mbpp
```

### Run Evaluation with Official Data
```bash
# Use official HumanEval dataset
python -m src.cli run --models gpt-4,llama3:8b --benchmark humaneval

# Use official MBPP dataset  
python -m src.cli run --models gpt-4,llama3:8b --benchmark mbpp
```

## Inspecting Tests and Problems

### View Benchmark Problems
```bash
# Inspect HumanEval problems
python -m src.cli inspect-benchmarks --benchmark humaneval --limit 3

# Show specific problem with test cases
python -m src.cli inspect-benchmarks --benchmark humaneval --problem-id "HumanEval/0" --show-tests

# View all test cases for first 2 problems
python -m src.cli inspect-benchmarks --benchmark humaneval --limit 2 --show-tests
```

**Example Output:**
```
🔍 Inspecting HumanEval Benchmark
📊 Total problems: 164

📋 Problem 1: HumanEval/0
Title: HumanEval HumanEval/0
Difficulty: medium
Category: arrays

Description:
Check if in given list of numbers, are any two numbers closer to each other than given threshold.

Function signature:
def has_close_elements(numbers: List[float], threshold: float) -> bool:

Test cases (4):
  Test 1:
    Type: assertion
    Input: has_close_elements([1.0, 2.0, 3.0], 0.5)
    Expected: False
  Test 2:
    Type: assertion
    Input: has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    Expected: True
```

### Analyze Test Results
```bash
# Show summary of completed evaluation
python -m src.cli show-test-results results/benchmark_report_humaneval_20241213_143022.json

# Show detailed results by model
python -m src.cli show-test-results results/benchmark_report_humaneval_20241213_143022.json --format detailed

# Show results by problem
python -m src.cli show-test-results results/benchmark_report_humaneval_20241213_143022.json --format problems
```

**Example Output:**
```
📊 Benchmark Test Results Analysis
📋 Benchmark: humaneval
🤖 Models: gpt-4, llama3:8b
📊 Total Problems: 164
🧪 Total Evaluations: 328

🤖 gpt-4
  Results: 142/164 passed (86.6%)
  Failed problems: HumanEval/12, HumanEval/45, HumanEval/78

🤖 llama3:8b  
  Results: 98/164 passed (59.8%)
  Failed problems: HumanEval/5, HumanEval/12, HumanEval/23, HumanEval/34, HumanEval/45
```

## Test Transparency

### What Tests Are Used?
EvalAgent provides complete transparency about which tests are being used:

1. **Official Test Cases**: Downloaded directly from official repositories
2. **Parsed Assertions**: Test cases are extracted from benchmark assertion statements
3. **Execution Environment**: Safe, isolated code execution with timeouts
4. **Pass/Fail Criteria**: Based on exact output matching and successful execution

### Test Case Format
Each problem includes:
- **Function Signature**: Exact function interface to implement
- **Description**: Natural language problem description
- **Test Cases**: Input/output pairs or assertion statements
- **Expected Behavior**: Clear success criteria

### Example Test Case Structure
```python
Problem: HumanEval/0
Function: def has_close_elements(numbers: List[float], threshold: float) -> bool

Test Cases:
1. assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False
2. assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True
3. assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
4. assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True
```

## Data Sources and Attribution

### HumanEval
- **Citation**: Chen et al. "Evaluating Large Language Models Trained on Code" (2021)
- **Repository**: https://github.com/openai/human-eval
- **License**: MIT License
- **Data Format**: JSONL with task_id, prompt, canonical_solution, test, entry_point

### MBPP  
- **Citation**: Austin et al. "Program Synthesis with Large Language Models" (2021)
- **Repository**: https://github.com/google-research/google-research/tree/master/mbpp
- **License**: Apache 2.0 License
- **Data Format**: JSONL with task_id, text, code, test_list

### Enhanced Datasets (EvalPlus)
- **Citation**: Liu et al. "Is Your Code Generated by ChatGPT Really Correct?" (2023)
- **Repository**: https://github.com/evalplus/evalplus
- **Enhancement**: Additional test cases to reduce false positives

## Creating Custom Benchmarks

You can also create custom benchmark problems:

```python
from src.models import Problem, TestCase

custom_problem = Problem(
    id="custom_001",
    title="Custom Problem",
    description="Your problem description",
    function_signature="def your_function(param):",
    docstring="Function documentation",
    test_cases=[
        TestCase(
            input_data="your_function(test_input)",
            expected_output="expected_result",
            test_type="assertion"
        )
    ],
    difficulty="medium",
    category="custom"
)
```

## Quality Assurance

EvalAgent ensures test quality through:

1. **Official Sources**: All benchmarks from peer-reviewed research
2. **Version Control**: Specific dataset versions and checksums
3. **Parsing Validation**: Robust test case extraction with error handling
4. **Execution Safety**: Sandboxed code execution with resource limits
5. **Result Verification**: Multiple validation layers for test results

## Best Practices

1. **Download Official Data**: Always use `download-benchmarks` for official datasets
2. **Inspect Before Running**: Use `inspect-benchmarks` to understand test cases
3. **Analyze Results**: Use `show-test-results` to understand model performance
4. **Document Sources**: Report which datasets and versions you used
5. **Compare Fairly**: Use same datasets across different model evaluations

This comprehensive benchmark system ensures that EvalAgent provides reliable, reproducible, and transparent LLM coding evaluations based on established research standards.