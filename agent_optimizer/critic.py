"""
Output Evaluator/Critic Agent - Compares actual vs expected outputs and provides feedback.
"""

import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .types import EvaluationResult, AgentFeedback, OptimizationObjective, ScoringMetrics, InputOutputPair, AggregationStrategy
from .config_loader import get_optimizer_config

logger = logging.getLogger(__name__)


class OutputEvaluator:
    """Evaluates workflow outputs against expected results."""
    
    def __init__(self, model_name: str = "openai/gpt-4o"):
        self.model_name = model_name
        self.config = get_optimizer_config()
        self.evaluation_prompts = {
            OptimizationObjective.ACCURACY: self.config.get_critic_prompt('accuracy'),
            OptimizationObjective.FLUENCY: self.config.get_critic_prompt('fluency'),
            OptimizationObjective.FACTUALITY: self.config.get_critic_prompt('factuality'),
            OptimizationObjective.INSTRUCTION_FOLLOWING: self.config.get_critic_prompt('instruction_following')
        }
    
    async def evaluate_output(
        self,
        actual_output: str,
        expected_output: str,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        agent_traces: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate actual output against expected output.
        
        Args:
            actual_output: The actual output from the workflow
            expected_output: The expected/ground truth output
            objective: The optimization objective to focus on
            agent_traces: Optional traces from individual agents
            
        Returns:
            EvaluationResult with score and feedback
        """
        try:
            # Generate LLM-based evaluation (primary evaluation method)
            llm_evaluation = await self._llm_evaluate(
                actual_output, expected_output, objective, agent_traces
            )
            
            # Calculate backup metrics for reference
            metrics = self._calculate_metrics(actual_output, expected_output)

            # Use LLM score as primary, with fallback to combined score if LLM fails
            if llm_evaluation.get('score') is not None:
                final_score = llm_evaluation['score']
                logger.info(f"Using LLM evaluation score: {final_score:.4f}")
            else:
                final_score = self._combine_scores(metrics, 0.0)
                logger.warning("LLM evaluation failed, using backup metrics")
            
            # Extract agent-specific feedback
            agent_feedback = self._extract_agent_feedback(
                llm_evaluation.get('agent_feedback', []),
                agent_traces
            )
            
            return EvaluationResult(
                score=final_score,
                global_feedback=llm_evaluation.get('global_feedback', 'No feedback available'),
                agent_feedback=agent_feedback,
                metrics=asdict(metrics)
            )
            
        except Exception as e:
            logger.error(f"Error evaluating output: {str(e)}")
            return EvaluationResult(
                score=0.0,
                global_feedback=f"Evaluation failed: {str(e)}",
                agent_feedback=[],
                metrics=asdict(ScoringMetrics())
            )
    
    async def evaluate_multiple_outputs(
        self,
        actual_outputs: List[str],
        input_output_pairs: List[InputOutputPair],
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        aggregation_strategy: AggregationStrategy = AggregationStrategy.AVERAGE,
        agent_traces: Optional[List[Dict[str, Any]]] = None
    ) -> EvaluationResult:
        """
        Evaluate multiple actual outputs against their expected outputs.
        
        Args:
            actual_outputs: List of actual outputs from the workflow
            input_output_pairs: List of input-output pairs with expected outputs
            objective: The optimization objective to focus on
            aggregation_strategy: How to aggregate scores across pairs
            agent_traces: Optional traces from individual agents for each pair
            
        Returns:
            EvaluationResult with aggregated score and feedback
        """
        if len(actual_outputs) != len(input_output_pairs):
            raise ValueError(f"Mismatch: {len(actual_outputs)} outputs vs {len(input_output_pairs)} pairs")
        
        try:
            # Evaluate each pair individually
            individual_results = []
            for i, (actual_output, pair) in enumerate(zip(actual_outputs, input_output_pairs)):
                traces_for_pair = agent_traces[i] if agent_traces and i < len(agent_traces) else None
                
                result = await self.evaluate_output(
                    actual_output=actual_output,
                    expected_output=pair.expected_output,
                    objective=objective,
                    agent_traces=traces_for_pair
                )
                individual_results.append((result, pair.weight))
            
            # Aggregate scores based on strategy
            aggregated_score = self._aggregate_scores(
                [(result.score, weight) for result, weight in individual_results],
                aggregation_strategy
            )
            
            # Combine feedback
            all_agent_feedback = []
            global_feedback_parts = []
            
            for i, (result, weight) in enumerate(individual_results):
                global_feedback_parts.append(
                    f"Pair {i+1} (weight={weight}): Score={result.score:.3f} - {result.global_feedback}"
                )
                
                # Add pair index to agent feedback
                for feedback in result.agent_feedback:
                    feedback_copy = AgentFeedback(
                        agent_id=f"{feedback.agent_id}_pair{i+1}",
                        issue=feedback.issue,
                        evidence=feedback.evidence,
                        suggested_fix=feedback.suggested_fix
                    )
                    all_agent_feedback.append(feedback_copy)
            
            # Aggregate metrics
            aggregated_metrics = self._aggregate_metrics([result.metrics for result, _ in individual_results])
            
            combined_global_feedback = (
                f"Aggregated evaluation using {aggregation_strategy.value} strategy:\n" + 
                f"Final Score: {aggregated_score:.3f}\n\n" +
                "Individual Pair Results:\n" + "\n".join(global_feedback_parts)
            )
            
            return EvaluationResult(
                score=aggregated_score,
                global_feedback=combined_global_feedback,
                agent_feedback=all_agent_feedback,
                metrics=aggregated_metrics
            )
            
        except Exception as e:
            logger.error(f"Error evaluating multiple outputs: {str(e)}")
            return EvaluationResult(
                score=0.0,
                global_feedback=f"Multiple output evaluation failed: {str(e)}",
                agent_feedback=[],
                metrics=asdict(ScoringMetrics())
            )
    
    def _calculate_metrics(self, actual: str, expected: str) -> ScoringMetrics:
        """Calculate various scoring metrics."""
        metrics = ScoringMetrics()
        
        # Exact match
        metrics.exact_match = 1.0 if actual.strip() == expected.strip() else 0.0
        
        # Simple semantic similarity (word overlap)
        metrics.semantic_similarity = self._calculate_word_overlap(actual, expected)
        
        # BLEU-like score (simplified)
        metrics.bleu_score = self._calculate_bleu_like_score(actual, expected)
        
        # ROUGE-like score (simplified)
        metrics.rouge_score = self._calculate_rouge_like_score(actual, expected)
        
        return metrics
    
    def _calculate_word_overlap(self, actual: str, expected: str) -> float:
        """Calculate word overlap similarity."""
        actual_words = set(actual.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = actual_words.intersection(expected_words)
        return len(intersection) / len(expected_words)
    
    def _calculate_bleu_like_score(self, actual: str, expected: str) -> float:
        """Calculate a simplified BLEU-like score."""
        actual_tokens = actual.lower().split()
        expected_tokens = expected.lower().split()
        
        if not expected_tokens:
            return 0.0
        
        # Calculate 1-gram precision
        matches = 0
        for token in actual_tokens:
            if token in expected_tokens:
                matches += 1
        
        precision = matches / len(actual_tokens) if actual_tokens else 0.0
        
        # Apply brevity penalty
        bp = min(1.0, len(actual_tokens) / len(expected_tokens))
        
        return precision * bp
    
    def _calculate_rouge_like_score(self, actual: str, expected: str) -> float:
        """Calculate a simplified ROUGE-like score."""
        actual_tokens = set(actual.lower().split())
        expected_tokens = set(expected.lower().split())
        
        if not expected_tokens:
            return 0.0
        
        intersection = actual_tokens.intersection(expected_tokens)
        return len(intersection) / len(expected_tokens)
    
    def _combine_scores(self, metrics: ScoringMetrics, llm_score: float) -> float:
        """Combine different scoring metrics into a final score."""
        weights = {
            'semantic_similarity': 0.3,
            'bleu_score': 0.2,
            'rouge_score': 0.2,
            'llm_score': 0.3
        }
        
        combined_score = (
            metrics.semantic_similarity * weights['semantic_similarity'] +
            metrics.bleu_score * weights['bleu_score'] +
            metrics.rouge_score * weights['rouge_score'] +
            llm_score * weights['llm_score']
        )
        
        return min(1.0, max(0.0, combined_score))
    
    async def _llm_evaluate(
        self,
        actual: str,
        expected: str,
        objective: OptimizationObjective,
        agent_traces: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use Google ADK agent to evaluate output quality."""
        try:
            # Import the LLM utility functions
            from .llm_utils import call_evaluation_agent
            
            # Add agent traces if available
            traces_info = ""
            if agent_traces:
                traces_info = "\n\nAgent Execution Traces:\n"
                for agent_id, trace in agent_traces.items():
                    if hasattr(trace, 'output_data'):
                        traces_info += f"- {agent_id}: {trace.output_data[:200]}...\n"
                    elif isinstance(trace, dict):
                        traces_info += f"- {agent_id}: {trace.get('output_data', '')[:200]}...\n"
                    else:
                        traces_info += f"- {agent_id}: {str(trace)[:200]}...\n"
            
            # Create evaluation prompt from YAML configuration
            evaluation_template = self.config.get_critic_prompt('main_evaluation')

            evaluation_prompt = evaluation_template.format(
                expected=expected,
                actual=actual,
                traces_info=traces_info,
                objective=objective.value
            )
            
            logger.info(f"Calling evaluation agent with prompt length: {len(evaluation_prompt)}")
            
            # Use Google ADK agent instead of direct LiteLLM call
            system_message = self.config.get_critic_system_message('default')
            response_text = await call_evaluation_agent(
                evaluation_prompt=evaluation_prompt,
                system_instruction=system_message,
                model_name=self.model_name  # Now properly uses the model_name parameter!
            )
            
            logger.info(f"Evaluation agent response length: {len(response_text)}")
            logger.debug(f"Evaluation agent raw response: {response_text}")
            
            # Try to extract JSON from the response
            evaluation_result = self._parse_evaluation_response(response_text)
            
            if not evaluation_result:
                logger.error("Failed to parse evaluation agent response, falling back to mock")
                logger.error(f"Response that failed to parse: {repr(response_text)}")
                return self._mock_llm_evaluation(actual, expected, objective)
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Evaluation agent failed: {str(e)}")
            traceback.print_exc()
            return self._mock_llm_evaluation(actual, expected, objective)
    
    def _parse_evaluation_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM evaluation response and extract JSON."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                logger.debug(f"Extracted JSON string: {json_str}")
                evaluation = json.loads(json_str)
                logger.debug(f"Parsed JSON object: {evaluation}")
                
                # Validate the structure and normalize format
                if isinstance(evaluation, dict) and 'score' in evaluation:
                    
                    # Ensure score is valid
                    score = float(evaluation['score'])
                    if 0.0 <= score <= 1.0:
                        evaluation['score'] = score
                        
                        # Handle different response formats:
                        # Format 1: {"score": 0.8, "global_feedback": "...", "agent_feedback": [...]}
                        # Format 2: {"score": 0.8, "feedback": "..."}
                        
                        if 'global_feedback' in evaluation:
                            # Already in correct format
                            if 'agent_feedback' not in evaluation:
                                evaluation['agent_feedback'] = []
                        elif 'feedback' in evaluation:
                            # Convert from simple format to expected format
                            evaluation['global_feedback'] = evaluation.pop('feedback')
                            evaluation['agent_feedback'] = []
                            logger.info("Converted simple feedback format to expected format")
                        else:
                            # Missing feedback entirely - add default
                            evaluation['global_feedback'] = "No feedback provided"
                            evaluation['agent_feedback'] = []
                            logger.warning("No feedback field found, using default")
                        
                        logger.info(f"Successfully parsed LLM evaluation: score={score:.3f}")
                        return evaluation
                    else:
                        logger.warning(f"Invalid score range: {score} (must be 0.0-1.0)")
                else:
                    logger.warning(f"Missing required 'score' field in evaluation: {evaluation}")
            
            logger.warning("Could not find valid JSON structure in LLM evaluation response")
            return None
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing error in evaluation: {str(e)}")
            logger.error(f"Failed to parse JSON string: {json_str if 'json_str' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM evaluation response: {str(e)}")
            return None
    
    def _mock_llm_evaluation(self, actual: str, expected: str, objective: OptimizationObjective) -> Dict[str, Any]:
        """Mock LLM evaluation for testing purposes."""
        logger.warning("🚨 USING MOCK LLM EVALUATION - Google ADK agent integration failed!")
        # Simple similarity-based scoring
        similarity = self._calculate_word_overlap(actual, expected)
        
        global_feedback = f"Output similarity: {similarity:.2f}. "
        agent_feedback = []
        
        if similarity < 0.5:
            global_feedback += "Output differs significantly from expected result. "
            agent_feedback.append({
                'agent_id': 'unknown',
                'issue': 'Low similarity to expected output',
                'evidence': f'Word overlap: {similarity:.2f}'
            })
        
        if len(actual) < len(expected) * 0.5:
            global_feedback += "Output is too brief. "
            agent_feedback.append({
                'agent_id': 'unknown',
                'issue': 'Output too brief',
                'evidence': f'Actual length: {len(actual)}, Expected length: {len(expected)}'
            })
        
        return {
            'score': similarity,
            'global_feedback': global_feedback,
            'agent_feedback': agent_feedback
        }
    
    def _extract_agent_feedback(
        self,
        llm_feedback: List[Dict[str, Any]],
        agent_traces: Optional[Dict[str, Any]] = None
    ) -> List[AgentFeedback]:
        """Extract and structure agent-specific feedback."""
        feedback_list = []
        
        for feedback_item in llm_feedback:
            if isinstance(feedback_item, dict):
                feedback_list.append(AgentFeedback(
                    agent_id=feedback_item.get('agent_id', 'unknown'),
                    issue=feedback_item.get('issue', ''),
                    evidence=feedback_item.get('evidence', ''),
                    suggested_fix=feedback_item.get('suggested_fix')
                ))
        
        return feedback_list
    
    def _aggregate_scores(
        self, 
        score_weight_pairs: List[tuple[float, float]], 
        strategy: AggregationStrategy
    ) -> float:
        """Aggregate scores based on the given strategy."""
        if not score_weight_pairs:
            return 0.0
        
        scores = [score for score, weight in score_weight_pairs]
        weights = [weight for score, weight in score_weight_pairs]
        
        if strategy == AggregationStrategy.AVERAGE:
            return sum(scores) / len(scores)
        
        elif strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            total_weight = sum(weights)
            if total_weight == 0:
                return sum(scores) / len(scores)  # Fall back to simple average
            weighted_sum = sum(score * weight for score, weight in score_weight_pairs)
            return weighted_sum / total_weight
        
        elif strategy == AggregationStrategy.MIN:
            return min(scores)
        
        elif strategy == AggregationStrategy.MAX:
            return max(scores)
        
        elif strategy == AggregationStrategy.MEDIAN:
            sorted_scores = sorted(scores)
            n = len(sorted_scores)
            if n % 2 == 0:
                return (sorted_scores[n//2 - 1] + sorted_scores[n//2]) / 2
            else:
                return sorted_scores[n//2]
        
        else:
            logger.warning(f"Unknown aggregation strategy: {strategy}, using average")
            return sum(scores) / len(scores)
    
    def _aggregate_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate metrics across multiple evaluations."""
        if not metrics_list:
            return asdict(ScoringMetrics())
        
        # Calculate averages for each metric
        aggregated = {}
        
        # Get all metric keys from first non-empty result
        all_keys = set()
        for metrics in metrics_list:
            if metrics:
                all_keys.update(metrics.keys())
        
        for key in all_keys:
            values = [metrics.get(key, 0.0) for metrics in metrics_list if metrics]
            aggregated[key] = sum(values) / len(values) if values else 0.0
        
        return aggregated
    
