"""
Optimization Loop Controller - Orchestrates the agent workflow optimization process.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from copy import deepcopy

from .types import (
    OptimizationInput, OptimizationResult, 
    OptimizationIteration, OptimizationObjective,
    LLMServiceError
)
from .runner import WorkflowRunner
from .critic import OutputEvaluator
from .trace import TraceExtractor
from .suggester import SuggestionGenerator
from .updater import PromptUpdater

logger = logging.getLogger(__name__)


class AgentOptimizer:
    """Main orchestrator for agent workflow optimization."""
    
    def __init__(self):
        self.runner = WorkflowRunner(enable_tracing=True)
        self.evaluator = OutputEvaluator()
        self.trace_extractor = TraceExtractor()
        self.suggestion_generator = SuggestionGenerator()
        self.prompt_updater = PromptUpdater()
    
    async def optimize_workflow(
        self,
        optimization_input: OptimizationInput
    ) -> OptimizationResult:
        """
        Main optimization loop that iteratively improves agent prompts.
        
        Args:
            optimization_input: Input configuration for optimization
            
        Returns:
            OptimizationResult with final configuration and metrics
        """
        logger.info("Starting agent workflow optimization")
        
        # Initialize result
        result = OptimizationResult(
            final_score=0.0,
            iterations_run=0,
            final_agent_config=deepcopy(optimization_input.agent_config),
            history=[]
        )
        
        # Keep track of best configuration
        best_config = deepcopy(optimization_input.agent_config)
        best_score = 0.0
        plateau_counter = 0
        
        try:
            for iteration in range(optimization_input.config.max_iterations):
                logger.info(f"Starting optimization iteration {iteration + 1}/{optimization_input.config.max_iterations}")
                
                # Run workflow for each input-output pair (no LLM dependency)
                outputs = []
                traces = []
                
                for i, pair in enumerate(optimization_input.input_output_pairs):
                    logger.info(f"Running workflow for input-output pair {i + 1}/{len(optimization_input.input_output_pairs)}")
                    
                    output, trace = await self.runner.run_workflow(
                        agent_config=result.final_agent_config,
                        input_data=pair.input_data,
                        job_config=optimization_input.job_config,
                        template_config=optimization_input.template_config
                    )
                    
                    outputs.append(output)
                    traces.append(trace)
                
                # Extract detailed traces if enabled
                processed_traces = []
                if optimization_input.config.enable_tracing:
                    for i, (output, trace) in enumerate(zip(outputs, traces)):
                        if trace:
                            processed_trace = self.trace_extractor.extract_trace_from_results(
                                {'execution_results': {}, 'final_output': output},
                                result.final_agent_config
                            )
                            processed_traces.append(processed_trace.agent_traces if processed_trace else None)
                        else:
                            processed_traces.append(None)
                
                # LLM-dependent operations with retry logic
                current_iteration_retries = 0
                evaluation_result = None
                individual_evaluations = []
                suggestions = []
                
                while current_iteration_retries < optimization_input.config.max_llm_retries_per_iteration:
                    try:
                        # Evaluate each pair individually for detailed feedback (LLM dependent)
                        individual_evaluations = []
                        for i, pair in enumerate(optimization_input.input_output_pairs):
                            individual_eval = await self.evaluator.evaluate_output(
                                actual_output=outputs[i],
                                expected_output=pair.expected_output,
                                objective=optimization_input.config.optimization_objective,
                                agent_traces=processed_traces[i] if processed_traces and i < len(processed_traces) else None
                            )
                            individual_evaluations.append(individual_eval)
                        
                        # Evaluate outputs using multiple pairs for aggregated score (LLM dependent)
                        evaluation_result = await self.evaluator.evaluate_multiple_outputs(
                            actual_outputs=outputs,
                            input_output_pairs=optimization_input.input_output_pairs,
                            objective=optimization_input.config.optimization_objective,
                            aggregation_strategy=optimization_input.config.aggregation_strategy,
                            agent_traces=processed_traces if processed_traces else None
                        )
                        
                        # If we need suggestions, generate them (LLM dependent) 
                        if iteration < optimization_input.config.max_iterations - 1:
                            current_prompts = self.runner.get_agent_prompts(result.final_agent_config)
                            
                            # Use new multiple pairs method for suggestion generation
                            suggestions = await self.suggestion_generator.generate_suggestions_for_multiple_pairs(
                                current_prompts=current_prompts,
                                individual_evaluations=individual_evaluations,
                                input_output_pairs=optimization_input.input_output_pairs,
                                aggregated_evaluation=evaluation_result,
                                traces=traces,
                                objective=optimization_input.config.optimization_objective
                            )
                        
                        # If we get here, all LLM operations succeeded
                        break
                        
                    except LLMServiceError as llm_error:
                        current_iteration_retries += 1
                        result.llm_failure_count += 1
                        
                        if llm_error.error_type == "service_error":
                            result.llm_service_errors += 1
                        elif llm_error.error_type in ["format_error", "parsing_error"]:
                            result.llm_format_errors += 1
                        
                        logger.warning(
                            f"LLM {llm_error.error_type} on iteration {iteration+1}, "
                            f"retry {current_iteration_retries}/{optimization_input.config.max_llm_retries_per_iteration}: {llm_error.message}"
                        )
                        
                        if llm_error.original_response:
                            logger.debug(f"Original LLM response: {llm_error.original_response[:500]}...")
                        
                        if current_iteration_retries >= optimization_input.config.max_llm_retries_per_iteration:
                            result.termination_reason = f"LLM failures exceeded max retries ({llm_error.error_type})"
                            logger.error(f"Terminating optimization: {result.termination_reason}")
                            break
                        
                        # Brief delay before retry
                        await asyncio.sleep(1)
                        continue
                
                # Check if we should terminate due to LLM failures
                if current_iteration_retries >= optimization_input.config.max_llm_retries_per_iteration:
                    break
                
                # Continue with normal optimization flow if LLM operations succeeded
                if not evaluation_result:
                    logger.error("Evaluation result is None after retry loop - this should not happen")
                    result.termination_reason = "Internal error: missing evaluation result"
                    break
                
                # Log critic's evaluation output
                logger.info(f"=== CRITIC EVALUATION (Iteration {iteration + 1}) ===")
                logger.info(f"Score: {evaluation_result.score:.4f}")
                logger.info(f"Global Feedback: {evaluation_result.global_feedback}")
                if evaluation_result.agent_feedback:
                    logger.info(f"Agent-Specific Feedback ({len(evaluation_result.agent_feedback)} items):")
                    for feedback in evaluation_result.agent_feedback:
                        logger.info(f"  - {feedback.agent_id}: {feedback.issue}")
                        logger.info(f"    Evidence: {feedback.evidence}")
                else:
                    logger.info("No agent-specific feedback provided")
                logger.info(f"Metrics: {evaluation_result.metrics}")
                logger.info("=" * 50)
                
                # Set baseline score from first iteration
                if iteration == 0:
                    result.baseline_score = evaluation_result.score
                    result.baseline_evaluation = evaluation_result
                
                # Create iteration record (use first trace for backward compatibility)
                first_trace = traces[0] if traces else None
                current_prompts = self.runner.get_agent_prompts(result.final_agent_config)
                iteration_record = OptimizationIteration(
                    iteration=iteration + 1,
                    score=evaluation_result.score,
                    evaluation_result=evaluation_result,
                    trace=first_trace,
                    current_prompts=current_prompts
                )
                
                # Store critic response
                critic_response = f"Score: {evaluation_result.score:.4f}\n"
                critic_response += f"Global Feedback: {evaluation_result.global_feedback}\n"
                if evaluation_result.agent_feedback:
                    critic_response += f"\nAgent-Specific Feedback:\n"
                    for feedback in evaluation_result.agent_feedback:
                        critic_response += f"- {feedback.agent_id}: {feedback.issue}\n"
                        critic_response += f"  Evidence: {feedback.evidence}\n"
                critic_response += f"\nMetrics: {evaluation_result.metrics}"
                iteration_record.critic_response = critic_response
                
                logger.info(f"Iteration {iteration + 1} score: {evaluation_result.score:.3f}")
                
                # Check for improvement
                if evaluation_result.score > best_score:
                    best_score = evaluation_result.score
                    best_config = deepcopy(result.final_agent_config)
                    plateau_counter = 0
                    logger.info(f"New best score: {best_score:.3f}")
                else:
                    plateau_counter += 1
                    logger.info(f"No improvement (plateau counter: {plateau_counter})")
                
                # Check termination conditions
                if evaluation_result.score >= optimization_input.config.convergence_threshold:
                    result.convergence_achieved = True
                    result.termination_reason = "Convergence threshold reached"
                    logger.info(f"Converged! Score: {evaluation_result.score:.3f}")
                    break
                
                # Check for plateau
                if plateau_counter >= optimization_input.config.plateau_patience:
                    result.termination_reason = "Plateau detected - no improvement"
                    logger.info("Optimization stopped due to plateau")
                    break
                
                # Log suggester's output (suggestions already generated in retry loop above)
                if iteration < optimization_input.config.max_iterations - 1:
                    logger.info(f"=== SUGGESTER OUTPUT (Iteration {iteration + 1}) ===")
                    if suggestions:
                        logger.info(f"Generated {len(suggestions)} suggestions:")
                        for i, suggestion in enumerate(suggestions, 1):
                            logger.info(f"  {i}. Agent: {suggestion.agent_id}")
                            logger.info(f"     Reason: {suggestion.reason}")
                            logger.info(f"     Confidence: {suggestion.confidence}")
                            logger.info(f"     New Prompt: {suggestion.new_prompt[:100]}{'...' if len(suggestion.new_prompt) > 100 else ''}")
                            logger.info(f"     Full New Prompt Length: {len(suggestion.new_prompt)} chars")
                    else:
                        logger.info("No suggestions generated")
                    logger.info("=" * 50)
                    
                    # Store suggester response
                    suggester_response = f"Generated {len(suggestions)} suggestions:\n"
                    if suggestions:
                        for i, suggestion in enumerate(suggestions, 1):
                            suggester_response += f"\n{i}. Agent: {suggestion.agent_id}\n"
                            suggester_response += f"   Reason: {suggestion.reason}\n"
                            suggester_response += f"   Confidence: {suggestion.confidence}\n"
                            suggester_response += f"   New Prompt: {suggestion.new_prompt}\n"
                    else:
                        suggester_response = "No suggestions generated"
                    iteration_record.suggester_response = suggester_response
                    iteration_record.generated_suggestions = suggestions
                    
                    if suggestions:
                        # Apply suggestions
                        updated_config, applied_suggestions = self.prompt_updater.apply_suggestions(
                            agent_config=result.final_agent_config,
                            suggestions=suggestions,
                            max_suggestions=3  # Limit to prevent too many changes at once
                        )
                        
                        # Validate updated configuration
                        is_valid, errors = self.prompt_updater.validate_configuration(updated_config)
                        
                        if is_valid:
                            result.final_agent_config = updated_config
                            iteration_record.changed_prompts = applied_suggestions
                            logger.info(f"Applied {len(applied_suggestions)} suggestions")
                        else:
                            logger.warning(f"Invalid configuration after updates: {errors}")
                            # Keep current configuration
                    else:
                        logger.info("No suggestions generated")
                
                # Add iteration to history
                result.history.append(iteration_record)
                result.iterations_run += 1
            
            # Set final results
            result.final_score = best_score
            result.final_agent_config = best_config
            
            if result.termination_reason == "":
                result.termination_reason = "Maximum iterations reached"
            
            logger.info(f"Optimization completed. Final score: {result.final_score:.3f}")
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            result.termination_reason = f"Error: {str(e)}"
        
        return result
    
    async def run_single_evaluation(
        self,
        agent_config: Dict[str, Any],
        input_data: Any,
        expected_output: str,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        job_config: Optional[Dict[str, Any]] = None,
        template_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a single evaluation without optimization.
        
        Args:
            agent_config: Agent configuration
            input_data: Input data
            expected_output: Expected output
            objective: Optimization objective
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Run workflow
            output, trace = await self.runner.run_workflow(
                agent_config=agent_config,
                input_data=input_data,
                job_config=job_config,
                template_config=template_config
            )
            
            # Evaluate output
            evaluation_result = await self.evaluator.evaluate_output(
                actual_output=output,
                expected_output=expected_output,
                objective=objective,
                agent_traces=trace.agent_traces if trace else None
            )
            
            return {
                'score': evaluation_result.score,
                'output': output,
                'evaluation': evaluation_result,
                'trace': trace
            }
            
        except Exception as e:
            logger.error(f"Single evaluation failed: {str(e)}")
            return {
                'score': 0.0,
                'output': f"Error: {str(e)}",
                'evaluation': None,
                'trace': None
            }
    
    async def compare_configurations(
        self,
        config_a: Dict[str, Any],
        config_b: Dict[str, Any],
        input_data: Any,
        expected_output: str,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY
    ) -> Dict[str, Any]:
        """
        Compare two agent configurations.
        
        Args:
            config_a: First configuration
            config_b: Second configuration
            input_data: Input data
            expected_output: Expected output
            objective: Optimization objective
            
        Returns:
            Comparison results
        """
        logger.info("Comparing two configurations")
        
        # Run evaluations in parallel
        results_a, results_b = await asyncio.gather(
            self.run_single_evaluation(config_a, input_data, expected_output, objective),
            self.run_single_evaluation(config_b, input_data, expected_output, objective)
        )
        
        # Compare results
        comparison = {
            'config_a': {
                'score': results_a['score'],
                'output_length': len(results_a['output']),
                'evaluation': results_a['evaluation']
            },
            'config_b': {
                'score': results_b['score'],
                'output_length': len(results_b['output']),
                'evaluation': results_b['evaluation']
            },
            'winner': 'config_a' if results_a['score'] > results_b['score'] else 'config_b',
            'score_difference': abs(results_a['score'] - results_b['score'])
        }
        
        logger.info(f"Comparison complete. Winner: {comparison['winner']} "
                   f"(scores: A={results_a['score']:.3f}, B={results_b['score']:.3f})")
        
        return comparison
    
    def generate_optimization_report(
        self,
        result: OptimizationResult,
        original_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive optimization report.
        
        Args:
            result: Optimization result
            original_config: Original configuration before optimization
            
        Returns:
            Comprehensive report dictionary
        """
        report = {
            'summary': {
                'convergence_achieved': result.convergence_achieved,
                'final_score': result.final_score,
                'baseline_score': result.baseline_score,
                'score_improvement': result.final_score - (result.baseline_score or 0.0),
                'iterations_run': result.iterations_run,
                'termination_reason': result.termination_reason
            },
            'baseline_evaluation': {
                'score': result.baseline_score,
                'global_feedback': result.baseline_evaluation.global_feedback if result.baseline_evaluation else None,
                'agent_feedback_count': len(result.baseline_evaluation.agent_feedback) if result.baseline_evaluation else 0,
                'metrics': result.baseline_evaluation.metrics if result.baseline_evaluation else {}
            },
            'progress': {
                'scores': [iteration.score for iteration in result.history],
                'improvements': self._calculate_improvements(result.history),
                'best_iteration': self._find_best_iteration(result.history)
            },
            'configuration_changes': {
                'total_changes': sum(len(iter.changed_prompts) for iter in result.history),
                'agents_modified': self._get_modified_agents(result.history),
                'prompt_diff': self.prompt_updater.get_prompt_diff(original_config, result.final_agent_config)
            },
            'performance_metrics': {
                'average_score': self._calculate_average_score(result.history, result.final_score),
                'score_variance': self._calculate_score_variance(result.history, result.final_score),
                'convergence_rate': self._calculate_convergence_rate(result.history)
            },
            'llm_reliability_metrics': {
                'total_llm_failures': result.llm_failure_count,
                'service_errors': result.llm_service_errors,
                'format_errors': result.llm_format_errors,
                'llm_success_rate': self._calculate_llm_success_rate(result),
                'max_retries_per_iteration': original_config.get('max_llm_retries_per_iteration', 3)
            },
            'detailed_iterations': []
        }
        
        # Add detailed iteration information including critic and suggester responses
        for iteration in result.history:
            iteration_detail = {
                'iteration': iteration.iteration,
                'score': iteration.score,
                'critic_response': iteration.critic_response,
                'suggester_response': iteration.suggester_response,
                'generated_suggestions_count': len(iteration.generated_suggestions),
                'applied_suggestions_count': len(iteration.changed_prompts),
                'current_prompts': iteration.current_prompts,
                'applied_suggestions': [
                    {
                        'agent_id': suggestion.agent_id,
                        'reason': suggestion.reason,
                        'confidence': suggestion.confidence,
                        'new_prompt': suggestion.new_prompt
                    }
                    for suggestion in iteration.changed_prompts
                ]
            }
            report['detailed_iterations'].append(iteration_detail)
        
        return report
    
    def _calculate_improvements(self, history: List[OptimizationIteration]) -> List[float]:
        """Calculate score improvements between iterations."""
        if len(history) < 2:
            return []
        
        improvements = []
        for i in range(1, len(history)):
            improvement = history[i].score - history[i-1].score
            improvements.append(improvement)
        
        return improvements
    
    def _find_best_iteration(self, history: List[OptimizationIteration]) -> Optional[int]:
        """Find the iteration with the best score."""
        if not history:
            return None
        
        best_score = max(iter.score for iter in history)
        for i, iteration in enumerate(history):
            if iteration.score == best_score:
                return i + 1
        
        return None
    
    def _get_modified_agents(self, history: List[OptimizationIteration]) -> List[str]:
        """Get list of agents that were modified during optimization."""
        modified_agents = set()
        
        for iteration in history:
            for suggestion in iteration.changed_prompts:
                modified_agents.add(suggestion.agent_id)
        
        return list(modified_agents)
    
    def _calculate_average_score(self, history: List[OptimizationIteration], final_score: float) -> float:
        """Calculate average score including all iterations and final score."""
        if not history:
            return final_score
        
        scores = [iter.score for iter in history] + [final_score]
        return sum(scores) / len(scores)

    def _calculate_score_variance(self, history: List[OptimizationIteration], final_score: float = None) -> float:
        """Calculate variance in scores across iterations."""
        if not history:
            return 0.0
        
        scores = [iter.score for iter in history]
        if final_score is not None:
            scores.append(final_score)
        
        if len(scores) < 2:
            return 0.0
            
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        return variance
    
    def _calculate_convergence_rate(self, history: List[OptimizationIteration]) -> float:
        """Calculate rate of convergence."""
        if len(history) < 2:
            return 0.0
        
        # Simple convergence rate: (final_score - initial_score) / iterations
        initial_score = history[0].score
        final_score = history[-1].score
        iterations = len(history)
        
        return (final_score - initial_score) / iterations
    
    def _calculate_llm_success_rate(self, result: OptimizationResult) -> float:
        """Calculate LLM success rate during optimization."""
        # Estimate total LLM calls: 2 per successful iteration (critic + suggester) + failures
        total_attempts = (result.iterations_run * 2) + result.llm_failure_count
        if total_attempts == 0:
            return 1.0
        
        successful_calls = result.iterations_run * 2
        return successful_calls / total_attempts
    
