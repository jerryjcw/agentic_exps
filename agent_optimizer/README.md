# Agent Optimizer

A system that accepts an agent workflow configuration (JSON/YAML), input data, and expected output, then iteratively modifies sub-agent prompts to make the overall workflow output converge toward the expected result.

## Features

- **Iterative Optimization**: Automatically improves agent prompts through multiple iterations
- **Multiple Objectives**: Supports accuracy, fluency, factuality, and instruction-following optimization
- **Comprehensive Evaluation**: Uses both semantic similarity and LLM-based evaluation
- **Detailed Tracing**: Tracks agent execution and provides detailed feedback
- **Configuration Management**: Safely updates agent configurations while preserving structure
- **Batch Processing**: Supports optimizing multiple configurations concurrently

## System Architecture

### Core Components

1. **Agent Workflow Runner** (`runner.py`)
   - Executes ADK-style agent workflows
   - Supports tracing and debugging
   - Compatible with existing agent configurations

2. **Output Evaluator/Critic Agent** (`critic.py`)
   - Compares actual vs expected outputs
   - Provides semantic similarity and LLM-based scoring
   - Generates agent-specific feedback

3. **Trace Extractor** (`trace.py`)
   - Extracts sub-agent execution traces
   - Provides detailed performance metrics
   - Supports trace export/import

4. **Suggestion Generator Agent** (`suggester.py`)
   - Generates prompt modification suggestions
   - Tailored to optimization objectives
   - Considers agent-specific feedback

5. **Prompt Updater** (`updater.py`)
   - Safely applies prompt changes
   - Validates configuration integrity
   - Supports rollback and history tracking

6. **Optimization Loop Controller** (`optimizer.py`)
   - Orchestrates the optimization process
   - Handles convergence and termination
   - Provides comprehensive reporting

## Usage

### Basic Usage

```python
import asyncio
from agent_optimizer import (
    AgentOptimizer,
    OptimizationInput,
    OptimizationConfig,
    OptimizationObjective
)

async def optimize_agent():
    # Load your agent configuration
    agent_config = {
        "name": "MyAgent",
        "class": "SequentialAgent",
        "module": "google.adk.agents",
        "sub_agents": [
            {
                "name": "AnalysisAgent",
                "class": "Agent",
                "module": "google.adk.agents",
                "model": "openai/gpt-4o",
                "instruction": "Analyze the provided input..."
            }
        ]
    }
    
    # Define input and expected output
    input_data = "Your input data here"
    expected_output = "Expected output format and content"
    
    # Configure optimization
    config = OptimizationConfig(
        max_iterations=5,
        convergence_threshold=0.9,
        optimization_objective=OptimizationObjective.ACCURACY
    )
    
    # Create optimization input
    optimization_input = OptimizationInput(
        agent_config=agent_config,
        input_data=input_data,
        expected_output=expected_output,
        config=config
    )
    
    # Run optimization
    optimizer = AgentOptimizer()
    result = await optimizer.optimize_workflow(optimization_input)
    
    print(f"Final Score: {result.final_score}")
    print(f"Iterations: {result.iterations_run}")
    print(f"Converged: {result.convergence_achieved}")
    
    return result.final_agent_config

# Run the optimization
asyncio.run(optimize_agent())
```

### Configuration Options

```python
from agent_optimizer import OptimizationConfig, OptimizationObjective

config = OptimizationConfig(
    max_iterations=10,              # Maximum optimization cycles
    convergence_threshold=0.9,      # Acceptable similarity threshold (0-1)
    optimization_objective=OptimizationObjective.ACCURACY,  # Focus area
    enable_tracing=True,            # Enable detailed tracing
    plateau_threshold=0.01,         # Minimum improvement threshold
    plateau_patience=3              # Iterations without improvement before stopping
)
```

### Optimization Objectives

- **ACCURACY**: Focus on factual correctness and precision
- **FLUENCY**: Optimize for natural language flow and readability
- **FACTUALITY**: Emphasize verifiable facts and source citation
- **INSTRUCTION_FOLLOWING**: Improve adherence to specific instructions

## System Inputs

- **agent_config**: JSON/YAML definition of multi-agent workflow (ADK-style)
- **input_data**: Input for the root agent
- **expected_output**: Ground-truth or desired output data
- **max_iterations**: Maximum optimization cycles (default = 5)
- **convergence_threshold**: Scoring threshold (0–1) for acceptable similarity
- **optimization_objective**: Focus area for optimization

## Termination Criteria

The system stops when:
- `final_score ≥ convergence_threshold`, OR
- `iterations ≥ max_iterations`, OR
- Plateau detected (no improvement for N iterations)

## Output Format

```python
{
    "final_score": 0.91,
    "iterations_run": 4,
    "convergence_achieved": True,
    "termination_reason": "Convergence threshold reached",
    "final_agent_config": {...},
    "history": [
        {
            "iteration": 1,
            "score": 0.61,
            "changed_prompts": [...],
            "evaluation_result": {...}
        },
        ...
    ]
}
```

## Examples

See `example.py` for a complete working example that demonstrates:
- Basic optimization workflow
- Configuration comparison
- Report generation
- Results export

## Installation

The system is designed to work with the existing agent framework. Make sure you have:
- Python 3.8+
- Required dependencies from the main project
- Access to the Google ADK agents module

## File Structure

```
agent_optimizer/
├── __init__.py          # Main module exports
├── types.py             # Data structures and schemas
├── runner.py            # Agent workflow execution
├── critic.py            # Output evaluation and scoring
├── trace.py             # Execution trace extraction
├── suggester.py         # Prompt improvement suggestions
├── updater.py           # Configuration updates
├── optimizer.py         # Main optimization controller
├── example.py           # Usage examples
└── README.md           # This file
```

## Advanced Features

### Batch Optimization

```python
# Optimize multiple configurations concurrently
results = await optimizer.batch_optimize(
    optimization_inputs=[input1, input2, input3],
    max_concurrent=3
)
```

### Configuration Comparison

```python
# Compare two configurations
comparison = await optimizer.compare_configurations(
    config_a=config1,
    config_b=config2,
    input_data=input_data,
    expected_output=expected_output
)
```

### Comprehensive Reporting

```python
# Generate detailed optimization report
report = optimizer.generate_optimization_report(result, original_config)
```

## Notes

- The system preserves the original agent configuration structure
- All prompt updates are validated before application
- Rollback functionality is available for failed optimizations
- Detailed tracing helps identify specific improvement areas
- The system is compatible with existing ADK agent configurations