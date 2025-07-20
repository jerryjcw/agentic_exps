"""
Example usage of the Agent Optimizer system.

This example demonstrates how to use the agent optimizer to improve
a simple code analysis workflow.
"""

import asyncio
import json
import logging
from pathlib import Path
import yaml

from agent_optimizer import (
    AgentOptimizer,
    OptimizationInput,
    OptimizationConfig,
    OptimizationObjective,
    InputOutputPair,
    AggregationStrategy
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    
    # Load configuration from JSON payload file
    payload_path = Path(__file__).parent.parent / "api" / "examples" / "nano_code_improvement_payload.json"
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    # Extract configurations from payload
    agent_config = payload['agent_config']
    job_config = payload['job_config']
    template_config = payload['template_config']
    
    from agent_optimizer.input_data import expected_input, expected_output

    # Define input data and expected output
    input_data = expected_input
    
    expected_output_text = expected_output
    
    # Create multiple input-output pairs for comprehensive testing
    # In this example, we'll use the same input-output pair multiple times with different weights
    # In practice, you would have different inputs for different test cases
    input_output_pairs = [
        InputOutputPair(
            input_data=input_data,
            expected_output=expected_output_text,
            weight=1.0
        ),
        # You can add more pairs here for different test cases
        # InputOutputPair(
        #     input_data=different_input_data,
        #     expected_output=different_expected_output,
        #     weight=1.5  # Higher weight for more important cases
        # ),
    ]
    
    # Create optimization configuration
    optimization_config = OptimizationConfig(
        max_iterations=3,
        convergence_threshold=0.91,
        optimization_objective=OptimizationObjective.ACCURACY,
        enable_tracing=True,
        aggregation_strategy=AggregationStrategy.AVERAGE  # Use average aggregation
    )
    
    # Create optimization input using new format
    optimization_input = OptimizationInput(
        agent_config=agent_config,
        input_output_pairs=input_output_pairs,
        config=optimization_config,
        job_config=job_config,
        template_config=template_config
    )
    
    # Run optimization
    logger.info("Starting agent optimization example")
    
    optimizer = AgentOptimizer()
    
    try:
        # Run optimization
        result = await optimizer.optimize_workflow(optimization_input)
        
        # Print results
        print("\n" + "="*60)
        print("OPTIMIZATION RESULTS")
        print("="*60)
        
        print(f"Final Score: {result.final_score:.3f}")
        print(f"Iterations Run: {result.iterations_run}")
        print(f"Convergence Achieved: {result.convergence_achieved}")
        print(f"Termination Reason: {result.termination_reason}")
        
        print("\n" + "-"*40)
        print("ITERATION HISTORY")
        print("-"*40)
        
        for iteration in result.history:
            print(f"Iteration {iteration.iteration}: Score {iteration.score:.3f}")
            if iteration.changed_prompts:
                print(f"  Applied {len(iteration.changed_prompts)} suggestions:")
                for suggestion in iteration.changed_prompts:
                    print(f"    - {suggestion.agent_id}: {suggestion.reason}, {suggestion.new_prompt}")
        
        # Generate comprehensive report
        report = optimizer.generate_optimization_report(result, agent_config)
        
        print(f"report = {report}")

        print("\n" + "-"*40)
        print("OPTIMIZATION REPORT")
        print("-"*40)
        
        print(f"Average Score: {report['performance_metrics']['average_score']:.3f}")
        print(f"Score Variance: {report['performance_metrics']['score_variance']:.3f}")
        print(f"Total Changes: {report['configuration_changes']['total_changes']}")
        print(f"Agents Modified: {', '.join(report['configuration_changes']['agents_modified'])}")
        
        # Save results
        results_dir = Path(__file__).parent.parent / "output"
        results_dir.mkdir(exist_ok=True)
        
        # Save final configuration
        final_config_path = results_dir / "optimized_agent_config.yaml"
        with open(final_config_path, 'w') as f:
            yaml.dump(result.final_agent_config, f, default_flow_style=False)
        
        # Save optimization report
        report_path = results_dir / "optimization_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nResults saved to:")
        print(f"  Configuration: {final_config_path}")
        print(f"  Report: {report_path}")
        
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise


async def run_comparison_example():
    """Example of comparing two configurations."""
    
    logger.info("Running configuration comparison example")
    
    # Load two different configurations
    config_path_1 = Path(__file__).parent.parent / "config" / "agent" / "yaml_examples" / "simple_code_improvement.yaml"
    config_path_2 = Path(__file__).parent.parent / "config" / "agent" / "yaml_examples" / "sequential_agent_config.yaml"
    
    with open(config_path_1, 'r') as f:
        config_a = yaml.safe_load(f)
    
    with open(config_path_2, 'r') as f:
        config_b = yaml.safe_load(f)
    
    input_data = "def hello(): print('Hello, World!')"
    expected_output = "Simple function that prints greeting message."
    
    optimizer = AgentOptimizer()
    
    try:
        comparison = await optimizer.compare_configurations(
            config_a=config_a,
            config_b=config_b,
            input_data=input_data,
            expected_output=expected_output
        )
        
        print("\n" + "="*60)
        print("CONFIGURATION COMPARISON")
        print("="*60)
        
        print(f"Configuration A Score: {comparison['config_a']['score']:.3f}")
        print(f"Configuration B Score: {comparison['config_b']['score']:.3f}")
        print(f"Winner: {comparison['winner']}")
        print(f"Score Difference: {comparison['score_difference']:.3f}")
        
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Uncomment to run comparison example
    # asyncio.run(run_comparison_example())