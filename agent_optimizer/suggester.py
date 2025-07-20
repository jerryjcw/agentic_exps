"""
Suggestion Generator Agent - Generates prompt modification suggestions based on feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from .types import (
    EvaluationResult, PromptSuggestion, OptimizationObjective, 
    WorkflowTrace, AgentTrace, InputOutputPair
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
        Generate suggestions for improving agent prompts.
        
        Args:
            current_prompts: Current prompts for each agent
            evaluation_result: Result from output evaluation
            trace: Optional workflow trace
            objective: Optimization objective
            expected_output: Expected output for context
            
        Returns:
            List of PromptSuggestion objects
        """
        try:
            suggestions = []
            
            # Generate suggestions based on global feedback
            global_suggestions = await self._generate_global_suggestions(
                current_prompts, evaluation_result, objective, expected_output
            )
            suggestions.extend(global_suggestions)
            
            # Generate suggestions based on agent-specific feedback
            agent_suggestions = await self._generate_agent_specific_suggestions(
                current_prompts, evaluation_result, trace, objective
            )
            suggestions.extend(agent_suggestions)
            
            # Generate suggestions based on trace analysis
            if trace:
                trace_suggestions = await self._generate_trace_based_suggestions(
                    current_prompts, trace, evaluation_result, objective
                )
                suggestions.extend(trace_suggestions)
            
            # Remove duplicates and rank suggestions
            suggestions = self._deduplicate_and_rank_suggestions(suggestions)
            
            print(f"######## The suggestions are {suggestions} ########")

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
            
            # Step 2: Generate global suggestions based on aggregated feedback
            global_suggestions = await self._generate_global_suggestions(
                current_prompts=current_prompts,
                evaluation_result=aggregated_feedback,
                objective=objective,
                expected_output="Multiple input-output pairs analyzed"
            )
            
            # Step 3: Generate agent-specific suggestions based on aggregated feedback
            agent_suggestions = await self._generate_agent_specific_suggestions(
                current_prompts=current_prompts,
                evaluation_result=aggregated_feedback,
                trace=None,  # Use aggregated feedback instead of trace
                objective=objective
            )
            
            # Combine and deduplicate suggestions
            all_suggestions = global_suggestions + agent_suggestions
            final_suggestions = self._deduplicate_and_rank_suggestions(all_suggestions)
            
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
                return parsed_response
                
        except Exception as e:
            logger.warning(f"Could not parse aggregated feedback as JSON: {str(e)}")
        
        # Fallback: treat as plain text
        return {
            'global_feedback': response,
            'agent_feedback': []
        }
    
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
    
    async def _generate_agent_specific_suggestions(
        self,
        current_prompts: Dict[str, str],
        evaluation_result: EvaluationResult,
        trace: Optional[WorkflowTrace],
        objective: OptimizationObjective
    ) -> List[PromptSuggestion]:
        """Generate suggestions based on agent-specific feedback."""
        suggestions = []
        
        for agent_feedback in evaluation_result.agent_feedback:
            agent_id = agent_feedback.agent_id
            
            if agent_id in current_prompts:
                # Generate specific suggestion for this agent
                suggestion = await self._generate_specific_agent_suggestion(
                    agent_id,
                    current_prompts[agent_id],
                    agent_feedback,
                    trace,
                    objective
                )
                
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    async def _generate_specific_agent_suggestion(
        self,
        agent_id: str,
        current_prompt: str,
        agent_feedback,
        trace: Optional[WorkflowTrace],
        objective: OptimizationObjective
    ) -> Optional[PromptSuggestion]:
        """Generate a specific suggestion for an agent."""
        try:
            # Analyze the feedback to determine improvement strategy
            issue = agent_feedback.issue.lower()
            
            # Get agent trace if available
            agent_trace = None
            if trace and agent_id in trace.agent_traces:
                agent_trace = trace.agent_traces[agent_id]
            
            # Generate suggestion based on issue type
            if 'accuracy' in issue or 'incorrect' in issue:
                new_prompt = self._improve_accuracy_prompt(current_prompt, agent_feedback)
            elif 'detail' in issue or 'brief' in issue:
                new_prompt = self._improve_detail_prompt(current_prompt, agent_feedback)
            elif 'format' in issue or 'structure' in issue:
                new_prompt = self._improve_format_prompt(current_prompt, agent_feedback)
            elif 'context' in issue or 'understanding' in issue:
                new_prompt = self._improve_context_prompt(current_prompt, agent_feedback)
            else:
                new_prompt = self._generic_improvement_prompt(current_prompt, agent_feedback)
            
            return PromptSuggestion(
                agent_id=agent_id,
                new_prompt=new_prompt,
                reason=f"Address issue: {agent_feedback.issue}",
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error generating specific suggestion for {agent_id}: {str(e)}")
            return None
    
    async def _generate_trace_based_suggestions(
        self,
        current_prompts: Dict[str, str],
        trace: WorkflowTrace,
        evaluation_result: EvaluationResult,
        objective: OptimizationObjective
    ) -> List[PromptSuggestion]:
        """Generate suggestions based on trace analysis."""
        suggestions = []
        
        # Analyze trace patterns
        for agent_id, agent_trace in trace.agent_traces.items():
            if agent_id in current_prompts:
                # Check for common issues
                if agent_trace.error:
                    suggestion = self._create_error_handling_suggestion(
                        agent_id, current_prompts[agent_id], agent_trace
                    )
                    if suggestion:
                        suggestions.append(suggestion)
                
                # Check output length patterns
                if len(agent_trace.output_data) < 100:
                    suggestion = self._create_output_length_suggestion(
                        agent_id, current_prompts[agent_id], agent_trace
                    )
                    if suggestion:
                        suggestions.append(suggestion)
        
        return suggestions
    
    def _improve_accuracy_prompt(self, current_prompt: str, agent_feedback) -> str:
        """Improve prompt for accuracy issues."""
        accuracy_additions = self.config.get_improvement_additions('accuracy_additions')
        
        # Add accuracy-focused instructions
        improved_prompt = current_prompt.rstrip()
        improved_prompt += "\n\nACCURACY FOCUS:\n"
        improved_prompt += "\n".join(accuracy_additions)
        
        return improved_prompt
    
    def _improve_detail_prompt(self, current_prompt: str, agent_feedback) -> str:
        """Improve prompt for detail/completeness issues."""
        detail_additions = self.config.get_improvement_additions('detail_additions')
        
        improved_prompt = current_prompt.rstrip()
        improved_prompt += "\n\nDETAIL REQUIREMENTS:\n"
        improved_prompt += "\n".join(detail_additions)
        
        return improved_prompt
    
    def _improve_format_prompt(self, current_prompt: str, agent_feedback) -> str:
        """Improve prompt for format/structure issues."""
        format_additions = self.config.get_improvement_additions('format_additions')
        
        improved_prompt = current_prompt.rstrip()
        improved_prompt += "\n\nFORMATTING REQUIREMENTS:\n"
        improved_prompt += "\n".join(format_additions)
        
        return improved_prompt
    
    def _improve_context_prompt(self, current_prompt: str, agent_feedback) -> str:
        """Improve prompt for context understanding issues."""
        context_additions = self.config.get_improvement_additions('context_additions')
        
        improved_prompt = current_prompt.rstrip()
        improved_prompt += "\n\nCONTEXT AWARENESS:\n"
        improved_prompt += "\n".join(context_additions)
        
        return improved_prompt
    
    def _generic_improvement_prompt(self, current_prompt: str, agent_feedback) -> str:
        """Generic prompt improvement."""
        improved_prompt = current_prompt.rstrip()
        improved_prompt += f"\n\nIMPROVEMENT NOTE:\n"
        improved_prompt += f"Address the following issue: {agent_feedback.issue}\n"
        improved_prompt += f"Evidence: {agent_feedback.evidence}"
        
        return improved_prompt
    
    def _create_error_handling_suggestion(
        self,
        agent_id: str,
        current_prompt: str,
        agent_trace: AgentTrace
    ) -> Optional[PromptSuggestion]:
        """Create suggestion for error handling."""
        error_handling_addition = self.config.get_improvement_template('error_handling')
        
        new_prompt = current_prompt.rstrip() + "\n" + error_handling_addition
        
        return PromptSuggestion(
            agent_id=agent_id,
            new_prompt=new_prompt,
            reason=f"Improve error handling (previous error: {agent_trace.error})",
            confidence=0.7
        )
    
    def _create_output_length_suggestion(
        self,
        agent_id: str,
        current_prompt: str,
        agent_trace: AgentTrace
    ) -> Optional[PromptSuggestion]:
        """Create suggestion for output length issues."""
        length_addition = self.config.get_improvement_template('output_length')
        
        new_prompt = current_prompt.rstrip() + "\n" + length_addition
        
        return PromptSuggestion(
            agent_id=agent_id,
            new_prompt=new_prompt,
            reason=f"Increase output detail (previous output: {len(agent_trace.output_data)} chars)",
            confidence=0.6
        )
    
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
    
    async def _mock_llm_suggestions(
        self,
        current_prompts: Dict[str, str],
        evaluation_result: EvaluationResult,
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """Mock LLM suggestions for testing purposes."""
        logger.warning("🚨 USING MOCK LLM SUGGESTIONS - Google ADK agent integration failed!")
        suggestions = []
        
        # Generate simple suggestions based on score
        logger.info(f"Mock LLM suggestions: score={evaluation_result.score:.3f}, threshold=0.5")
        if evaluation_result.score < 0.5:
            logger.info(f"Generating suggestions for {len(current_prompts)} agents")
            for agent_id in current_prompts.keys():
                new_prompt = current_prompts[agent_id] + "\n\nPlease provide more detailed and accurate analysis."
                suggestions.append({
                    'agent_id': agent_id,
                    'new_prompt': new_prompt,
                    'reason': f"Low evaluation score ({evaluation_result.score:.2f})",
                    'confidence': 0.6
                })
                logger.info(f"Generated suggestion for {agent_id}: {len(new_prompt)} chars")
        else:
            logger.info("Score above threshold, no suggestions generated")
        
        return suggestions
    
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
                logger.warning("No valid suggestions from suggestion agent, falling back to mock")
                return await self._mock_llm_suggestions(current_prompts, evaluation_result, objective)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion agent failed: {str(e)}")
            # Fall back to mock suggestions
            return await self._mock_llm_suggestions(current_prompts, evaluation_result, objective)
    
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
                            logger.warning(f"Invalid suggestion {i+1}: missing required fields. Got: {suggestion}")
                    
                    logger.info(f"Successfully parsed {len(valid_suggestions)} valid suggestions from LLM")
                    return valid_suggestions
                else:
                    logger.warning(f"Expected list of suggestions, got: {type(suggestions)}")
            else:
                logger.warning("Could not find JSON array structure in LLM response")
            
            logger.warning("Could not parse valid JSON from LLM response")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Failed to parse JSON string: {json_str if 'json_str' in locals() else 'N/A'}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return []
    
