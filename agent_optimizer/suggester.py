"""
Suggestion Generator Agent - Generates prompt modification suggestions based on feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from .types import (
    EvaluationResult, PromptSuggestion, OptimizationObjective, 
    WorkflowTrace, InputOutputPair, LLMServiceError, AgentFeedback
)
from .config_loader import get_optimizer_config

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """Generates prompt modification suggestions to improve workflow output."""
    
    def __init__(self, model_name: str = "openai/gpt-4o"):
        self.model_name = model_name
        self.config = get_optimizer_config()
        self.suggestion_prompts = {
            OptimizationObjective.ACCURACY: self.config.get_suggester_prompt('accuracy'),
            OptimizationObjective.FLUENCY: self.config.get_suggester_prompt('fluency'),
            OptimizationObjective.FACTUALITY: self.config.get_suggester_prompt('factuality'),
            OptimizationObjective.INSTRUCTION_FOLLOWING: self.config.get_suggester_prompt('instruction_following')
        }
    
    async def generate_suggestions(
        self,
        current_prompts: Dict[str, str],
        evaluation_result: EvaluationResult,
        trace: Optional[WorkflowTrace] = None,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        expected_output: Optional[str] = None
    ) -> List[PromptSuggestion]:
        """
        Generate suggestions for improving agent prompts using LLM-based analysis only.
        
        Args:
            current_prompts: Current prompts for each agent
            evaluation_result: Result from output evaluation
            trace: Optional workflow trace (not used in LLM-only approach)
            objective: Optimization objective
            expected_output: Expected output for context
            
        Returns:
            List of PromptSuggestion objects
        """
        try:
            # Generate suggestions using LLM-based global analysis only
            suggestions = await self._generate_global_suggestions(
                current_prompts, evaluation_result, objective, expected_output
            )
            
            # Remove duplicates and rank suggestions
            suggestions = self._deduplicate_and_rank_suggestions(suggestions)
            
            logger.info(f"Generated {len(suggestions)} LLM-based suggestions")

            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return []
    
    async def generate_suggestions_for_multiple_pairs(
        self,
        current_prompts: Dict[str, str],
        individual_evaluations: List[EvaluationResult],
        input_output_pairs: List[InputOutputPair],
        aggregated_evaluation: EvaluationResult,
        traces: Optional[List[WorkflowTrace]] = None,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY
    ) -> List[PromptSuggestion]:
        """
        Generate suggestions based on multiple input-output pairs.
        
        Args:
            current_prompts: Current prompts for each agent
            individual_evaluations: Evaluation results for each pair
            input_output_pairs: The input-output pairs used
            aggregated_evaluation: Overall aggregated evaluation result
            traces: Optional workflow traces for each pair
            objective: Optimization objective
            
        Returns:
            List of PromptSuggestion objects
        """
        try:
            # When we have multiple pairs, we need to aggregate feedback across all pairs
            if len(individual_evaluations) == 1:
                # Single pair - use existing method
                trace = traces[0] if traces else None
                return await self.generate_suggestions(
                    current_prompts=current_prompts,
                    evaluation_result=individual_evaluations[0],
                    trace=trace,
                    objective=objective,
                    expected_output=input_output_pairs[0].expected_output
                )
            
            # Multiple pairs - use aggregation approach
            logger.info(f"Generating suggestions for {len(individual_evaluations)} input-output pairs")
            
            # Step 1: Aggregate feedback across all pairs using LLM
            aggregated_feedback = await self._aggregate_feedback_across_pairs(
                individual_evaluations,
                input_output_pairs,
                current_prompts,
                objective
            )
            
            # Step 2: Generate suggestions based on aggregated feedback using LLM-only approach
            suggestions = await self._generate_global_suggestions(
                current_prompts=current_prompts,
                evaluation_result=aggregated_feedback,
                objective=objective,
                expected_output="Multiple input-output pairs analyzed"
            )
            
            # Deduplicate and rank suggestions
            final_suggestions = self._deduplicate_and_rank_suggestions(suggestions)
            
            logger.info(f"Generated {len(final_suggestions)} suggestions from {len(individual_evaluations)} pairs")
            return final_suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions for multiple pairs: {str(e)}")
            return []
    
    async def _aggregate_feedback_across_pairs(
        self,
        individual_evaluations: List[EvaluationResult],
        input_output_pairs: List[InputOutputPair],
        current_prompts: Dict[str, str],
        objective: OptimizationObjective
    ) -> EvaluationResult:
        """
        Aggregate feedback from multiple pairs using an LLM to synthesize insights.
        """
        try:
            # Import LLM utility functions
            from .llm_utils import call_evaluation_agent
            
            # Prepare context for aggregation
            pair_summaries = []
            all_agent_feedback = []
            
            for i, (eval_result, pair) in enumerate(zip(individual_evaluations, input_output_pairs)):
                pair_summary = f"Pair {i+1}:\n"
                pair_summary += f"  Score: {eval_result.score:.3f}\n"
                pair_summary += f"  Global Feedback: {eval_result.global_feedback}\n"
                
                if eval_result.agent_feedback:
                    pair_summary += f"  Agent Feedback:\n"
                    for feedback in eval_result.agent_feedback:
                        pair_summary += f"    - {feedback.agent_id}: {feedback.issue}\n"
                        pair_summary += f"      Evidence: {feedback.evidence}\n"
                        
                        # Collect for overall aggregation
                        all_agent_feedback.append(feedback)
                
                pair_summaries.append(pair_summary)
            
            # Create aggregation prompt
            aggregation_prompt = self.config.get_suggester_prompt('feedback_aggregation').format(
                num_pairs=len(individual_evaluations),
                pair_summaries="\n\n".join(pair_summaries),
                current_prompts="\n".join([
                    f"Agent '{agent_id}': {prompt[:200]}..."
                    for agent_id, prompt in current_prompts.items()
                ]),
                objective=objective.value
            )
            
            # Use LLM to aggregate feedback
            system_message = self.config.get_suggester_system_message('aggregation')
            aggregated_response = await call_evaluation_agent(
                evaluation_prompt=aggregation_prompt,
                system_instruction=system_message,
                model_name=self.model_name
            )
            
            # Parse the aggregated response
            aggregated_feedback = self._parse_aggregated_feedback(aggregated_response)
            
            # Calculate average score
            avg_score = sum(eval_result.score for eval_result in individual_evaluations) / len(individual_evaluations)
            
            return EvaluationResult(
                score=avg_score,
                global_feedback=aggregated_feedback.get('global_feedback', 'Aggregated feedback from multiple pairs'),
                agent_feedback=aggregated_feedback.get('agent_feedback', []),
                metrics={}
            )
            
        except Exception as e:
            logger.error(f"Error aggregating feedback: {str(e)}")
            # Fallback: simple concatenation
            combined_feedback = f"Combined feedback from {len(individual_evaluations)} pairs:\n"
            combined_agent_feedback = []
            
            for i, eval_result in enumerate(individual_evaluations):
                combined_feedback += f"\nPair {i+1}: {eval_result.global_feedback}\n"
                combined_agent_feedback.extend(eval_result.agent_feedback)
            
            avg_score = sum(eval_result.score for eval_result in individual_evaluations) / len(individual_evaluations)
            
            return EvaluationResult(
                score=avg_score,
                global_feedback=combined_feedback,
                agent_feedback=combined_agent_feedback,
                metrics={}
            )
    
    def _parse_aggregated_feedback(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for aggregated feedback."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                if 'global_feedback' not in parsed_response:
                    raise LLMServiceError(
                        message="Missing 'global_feedback' field in aggregated response",
                        error_type="format_error",
                        original_response=response
                    )
                
                # Convert agent_feedback dictionaries to AgentFeedback objects
                if 'agent_feedback' in parsed_response and isinstance(parsed_response['agent_feedback'], list):
                    agent_feedback_objects = []
                    for feedback_dict in parsed_response['agent_feedback']:
                        if isinstance(feedback_dict, dict):
                            agent_feedback_objects.append(AgentFeedback(
                                agent_id=feedback_dict.get('agent_id', ''),
                                issue=feedback_dict.get('issue', ''),
                                evidence=feedback_dict.get('evidence', ''),
                                suggested_fix=feedback_dict.get('suggested_fix')
                            ))
                        else:
                            # If it's already an AgentFeedback object, keep it
                            agent_feedback_objects.append(feedback_dict)
                    parsed_response['agent_feedback'] = agent_feedback_objects
                
                return parsed_response
            else:
                raise LLMServiceError(
                    message="Could not find JSON structure in aggregated feedback response",
                    error_type="format_error",
                    original_response=response
                )
                
        except LLMServiceError:
            # Re-raise LLMServiceError without modification
            raise
        except json.JSONDecodeError as e:
            raise LLMServiceError(
                message=f"JSON parsing error in aggregated feedback: {str(e)}",
                error_type="parsing_error",
                original_response=response
            )
        except Exception as e:
            raise LLMServiceError(
                message=f"Error parsing aggregated feedback response: {str(e)}",
                error_type="format_error",
                original_response=response
            )
    
    async def _generate_global_suggestions(
        self,
        current_prompts: Dict[str, str],
        evaluation_result: EvaluationResult,
        objective: OptimizationObjective,
        expected_output: Optional[str] = None
    ) -> List[PromptSuggestion]:
        """Generate suggestions based on global feedback."""
        suggestions = []
        
        # Use LLM to generate suggestions
        suggestion_prompt = self.suggestion_prompts[objective]
        
        # Prepare context
        prompts_context = "\n".join([
            f"Agent '{agent_id}': {prompt[:300]}..."
            for agent_id, prompt in current_prompts.items()
        ])
        
        # Prepare agent-specific feedback
        agent_feedback_context = ""
        if evaluation_result.agent_feedback:
            agent_feedback_context = "\n\nAgent-Specific Feedback:\n"
            for feedback in evaluation_result.agent_feedback:
                agent_feedback_context += f"- {feedback.agent_id}: {feedback.issue}\n  Evidence: {feedback.evidence}\n"
        
        full_prompt = suggestion_prompt.format(
            current_prompts=prompts_context,
            global_feedback=evaluation_result.global_feedback + agent_feedback_context,
            score=evaluation_result.score,
            expected_output=expected_output or "Not provided"
        )
        
        try:
            # Use actual LLM call instead of mock
            llm_suggestions = await self._real_llm_suggestions(
                full_prompt, current_prompts, evaluation_result, objective
            )
            
            for suggestion_data in llm_suggestions:
                suggestions.append(PromptSuggestion(
                    agent_id=suggestion_data['agent_id'],
                    new_prompt=suggestion_data['new_prompt'],
                    reason=suggestion_data['reason'],
                    confidence=suggestion_data.get('confidence', 0.7)
                ))
            
        except Exception as e:
            logger.error(f"Error in global suggestion generation: {str(e)}")
        
        return suggestions
        
    def _deduplicate_and_rank_suggestions(
        self,
        suggestions: List[PromptSuggestion]
    ) -> List[PromptSuggestion]:
        """Remove duplicates and rank suggestions by confidence."""
        # Group by agent_id and keep highest confidence
        agent_suggestions = {}
        
        for suggestion in suggestions:
            agent_id = suggestion.agent_id
            if agent_id not in agent_suggestions:
                agent_suggestions[agent_id] = suggestion
            elif suggestion.confidence > agent_suggestions[agent_id].confidence:
                agent_suggestions[agent_id] = suggestion
        
        # Sort by confidence
        ranked_suggestions = sorted(
            agent_suggestions.values(),
            key=lambda x: x.confidence,
            reverse=True
        )
        
        return ranked_suggestions
    
    
    async def _real_llm_suggestions(
        self,
        full_prompt: str,
        current_prompts: Dict[str, str],
        evaluation_result: EvaluationResult,
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """Generate suggestions using Google ADK agent."""
        try:
            # Import the LLM utility functions
            from .llm_utils import call_suggestion_agent
            
            # Prepare the system message
            system_message = self.config.get_suggester_system_message('default')
            
            logger.info(f"Calling suggestion agent with prompt length: {len(full_prompt)}")
            logger.info(f"Suggestion Agent Input Prompt:\n{full_prompt}")
            
            # Use Google ADK agent instead of direct LiteLLM call
            response_text = await call_suggestion_agent(
                suggestion_prompt=full_prompt,
                system_instruction=system_message,
                model_name=self.model_name  # Now properly uses the model_name parameter!
            )
            
            logger.info(f"Suggestion agent response length: {len(response_text)}")
            logger.info(f"Suggestion Agent Raw Response: {response_text}")
            
            # Try to extract JSON from the response
            suggestions = self._parse_llm_response(response_text)
            
            if not suggestions:
                raise LLMServiceError(
                    message="No valid suggestions from suggestion agent - empty or invalid response",
                    error_type="format_error",
                    original_response=response_text
                )
            
            return suggestions
            
        except LLMServiceError:
            # Re-raise LLMServiceError without modification
            raise
        except Exception as e:
            logger.error(f"Suggestion agent service failed: {str(e)}")
            raise LLMServiceError(
                message=f"Suggestion agent service error: {str(e)}",
                error_type="service_error",
                original_response=None
            )
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract suggestion JSON."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                logger.info(f"Extracted suggestions JSON string: {json_str}")
                suggestions = json.loads(json_str)
                logger.info(f"Parsed suggestions JSON object: {suggestions}")
                
                # Validate the structure
                if isinstance(suggestions, list):
                    valid_suggestions = []
                    for i, suggestion in enumerate(suggestions):
                        if (isinstance(suggestion, dict) and 
                            'agent_id' in suggestion and 
                            'new_prompt' in suggestion and 
                            'reason' in suggestion):
                            if 'confidence' not in suggestion:
                                suggestion['confidence'] = 0.7
                            valid_suggestions.append(suggestion)
                            logger.info(f"Valid suggestion {i+1}: agent_id={suggestion['agent_id']}, reason={suggestion['reason'][:50]}...")
                        else:
                            raise LLMServiceError(
                                message=f"Invalid suggestion {i+1}: missing required fields (agent_id, new_prompt, reason). Got: {suggestion}",
                                error_type="format_error",
                                original_response=response_text
                            )
                    
                    logger.info(f"Successfully parsed {len(valid_suggestions)} valid suggestions from LLM")
                    return valid_suggestions
                else:
                    raise LLMServiceError(
                        message=f"Expected list of suggestions, got: {type(suggestions)}",
                        error_type="format_error",
                        original_response=response_text
                    )
            else:
                raise LLMServiceError(
                    message="Could not find JSON array structure in LLM response",
                    error_type="format_error",
                    original_response=response_text
                )
            
        except LLMServiceError:
            # Re-raise LLMServiceError without modification
            raise
        except json.JSONDecodeError as e:
            raise LLMServiceError(
                message=f"JSON parsing error: {str(e)}",
                error_type="parsing_error",
                original_response=response_text
            )
        except Exception as e:
            raise LLMServiceError(
                message=f"Error parsing LLM response: {str(e)}",
                error_type="format_error",
                original_response=response_text
            )
    
