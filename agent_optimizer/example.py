"""
Example usage of the Agent Optimizer system with file-based input/target configuration.

This example demonstrates how to use the agent optimizer to improve
a simple code analysis workflow using the new file-based approach where:
- Input configurations are loaded from files (following flexible_agents format)
- Target outputs are read from target files using DocumentReader
- Multiple input/target pairs can be processed with individual weights
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
    AggregationStrategy,
    TargetConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main example function using file-based input/target configuration."""
    
    # Load configuration from the new optimizer payload file
    payload_path = Path(__file__).parent.parent / "examples" / "optimizer_payload_test.json"
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    # Extract configurations from payload
    agent_config = payload['agent_config']
    job_config = payload['job_config']
    template_config = payload['template_config']
    
    # Extract the new input_configs and target_configs
    input_configs = payload['input_configs']
    target_configs_data = payload['target_configs']
    
    # Convert target_configs to TargetConfig objects
    target_configs = [
        TargetConfig(
            target_path=config['target_path'],
            weight=config.get('weight', 1.0)
        ) for config in target_configs_data
    ]
    
    # Create optimization configuration
    optimization_config = OptimizationConfig(
        max_iterations=3,
        convergence_threshold=0.85,
        optimization_objective=OptimizationObjective.ACCURACY,
        enable_tracing=True,
        aggregation_strategy=AggregationStrategy.AVERAGE,
        max_llm_retries_per_iteration=2
    )
    
    # Create optimization input using new file-based format
    optimization_input = OptimizationInput(
        agent_config=agent_config,
        input_output_pairs=[],  # Will be populated from input_configs/target_configs
        config=optimization_config,
        job_config=job_config,
        template_config=template_config,
        input_configs=input_configs,
        target_configs=target_configs
    )
    
    # Log configuration details
    logger.info("Starting agent optimization example with file-based configuration")
    logger.info(f"Input configs: {len(input_configs)} configuration(s)")
    logger.info(f"Target configs: {len(target_configs)} target(s)")
    
    for i, (input_config, target_config) in enumerate(zip(input_configs, target_configs)):
        logger.info(f"Pair {i+1}: Input path '{input_config.get('input_folders', [{}])[0].get('input_path', 'N/A')}' -> Target '{target_config.target_path}' (weight: {target_config.weight})")
    
    # Run optimization
    
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


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    