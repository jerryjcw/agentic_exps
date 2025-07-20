"""
Data structures and type definitions for the agent workflow optimization system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import json


class OptimizationObjective(Enum):
    """Optimization objectives for the agent workflow."""
    ACCURACY = "accuracy"
    FLUENCY = "fluency"
    FACTUALITY = "factuality"
    INSTRUCTION_FOLLOWING = "instruction-following"


class AggregationStrategy(Enum):
    """Strategies for aggregating scores across multiple input-output pairs."""
    AVERAGE = "average"  # Simple average
    WEIGHTED_AVERAGE = "weighted_average"  # Weighted by pair weights
    MIN = "min"  # Minimum score (worst case)
    MAX = "max"  # Maximum score (best case)
    MEDIAN = "median"  # Median score


@dataclass
class AgentTrace:
    """Trace information for a single agent execution."""
    agent_id: str
    input_data: str
    output_data: str
    prompt: str
    tools_used: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class WorkflowTrace:
    """Complete trace of workflow execution."""
    agent_traces: Dict[str, AgentTrace] = field(default_factory=dict)
    total_execution_time: Optional[float] = None
    final_output: Optional[str] = None


@dataclass
class AgentFeedback:
    """Feedback for a specific agent."""
    agent_id: str
    issue: str
    evidence: str
    suggested_fix: Optional[str] = None


@dataclass
class EvaluationResult:
    """Result of output evaluation."""
    score: float
    global_feedback: str
    agent_feedback: List[AgentFeedback] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PromptSuggestion:
    """Suggestion for updating an agent's prompt."""
    agent_id: str
    new_prompt: str
    reason: str
    confidence: float = 0.0


@dataclass
class OptimizationIteration:
    """Information about a single optimization iteration."""
    iteration: int
    score: float
    changed_prompts: List[PromptSuggestion] = field(default_factory=list)
    evaluation_result: Optional[EvaluationResult] = None
    trace: Optional[WorkflowTrace] = None
    critic_response: Optional[str] = None
    suggester_response: Optional[str] = None
    generated_suggestions: List[PromptSuggestion] = field(default_factory=list)


@dataclass
class OptimizationConfig:
    """Configuration for the optimization process."""
    max_iterations: int = 5
    convergence_threshold: float = 0.9
    optimization_objective: OptimizationObjective = OptimizationObjective.ACCURACY
    enable_tracing: bool = True
    plateau_threshold: float = 0.01
    plateau_patience: int = 3
    aggregation_strategy: AggregationStrategy = AggregationStrategy.AVERAGE


@dataclass
class OptimizationResult:
    """Final result of the optimization process."""
    final_score: float
    iterations_run: int
    final_agent_config: Dict[str, Any]
    history: List[OptimizationIteration] = field(default_factory=list)
    convergence_achieved: bool = False
    termination_reason: str = ""
    baseline_score: Optional[float] = None
    baseline_evaluation: Optional[EvaluationResult] = None


@dataclass
class InputOutputPair:
    """A single input-output pair for evaluation."""
    input_data: Any
    expected_output: str
    weight: float = 1.0  # Weight for this pair in aggregation


@dataclass
class OptimizationInput:
    """Input data for the optimization process."""
    agent_config: Dict[str, Any]
    input_output_pairs: List[InputOutputPair]
    config: OptimizationConfig = field(default_factory=OptimizationConfig)
    job_config: Optional[Dict[str, Any]] = None
    template_config: Optional[Dict[str, Any]] = None
    
    # Backward compatibility - deprecated fields
    input_data: Optional[Any] = None
    expected_output: Optional[str] = None
    
    def __post_init__(self):
        """Ensure backward compatibility by converting old format to new format."""
        if self.input_data is not None and self.expected_output is not None:
            # Convert old single pair format to new multiple pairs format
            if not self.input_output_pairs:
                self.input_output_pairs = [
                    InputOutputPair(
                        input_data=self.input_data,
                        expected_output=self.expected_output,
                        weight=1.0
                    )
                ]
        
        if not self.input_output_pairs:
            raise ValueError("Must provide either input_output_pairs or input_data/expected_output")


class AgentConfigUpdater:
    """Utility class for updating agent configurations."""
    
    @staticmethod
    def update_agent_prompt(config: Dict[str, Any], agent_id: str, new_prompt: str) -> Dict[str, Any]:
        """Update the prompt for a specific agent in the configuration."""
        updated_config = json.loads(json.dumps(config))  # Deep copy
        
        def update_recursive(agent_dict: Dict[str, Any], target_id: str, prompt: str) -> bool:
            if agent_dict.get('name') == target_id:
                agent_dict['instruction'] = prompt
                return True
            
            if 'sub_agents' in agent_dict:
                for sub_agent in agent_dict['sub_agents']:
                    if update_recursive(sub_agent, target_id, prompt):
                        return True
            
            return False
        
        update_recursive(updated_config, agent_id, new_prompt)
        return updated_config
    
    @staticmethod
    def extract_agent_prompts(config: Dict[str, Any]) -> Dict[str, str]:
        """Extract all agent prompts from the configuration."""
        prompts = {}
        
        def extract_recursive(agent_dict: Dict[str, Any]):
            if 'name' in agent_dict and 'instruction' in agent_dict:
                prompts[agent_dict['name']] = agent_dict['instruction']
            
            if 'sub_agents' in agent_dict:
                for sub_agent in agent_dict['sub_agents']:
                    extract_recursive(sub_agent)
        
        extract_recursive(config)
        return prompts


@dataclass
class ScoringMetrics:
    """Metrics for evaluating output quality."""
    semantic_similarity: float = 0.0
    exact_match: float = 0.0
    bleu_score: float = 0.0
    rouge_score: float = 0.0
    custom_score: float = 0.0
    
    def weighted_average(self, weights: Dict[str, float] = None) -> float:
        """Calculate weighted average of all metrics."""
        if weights is None:
            weights = {
                'semantic_similarity': 0.4,
                'exact_match': 0.2,
                'bleu_score': 0.2,
                'rouge_score': 0.2
            }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if hasattr(self, metric):
                total_score += getattr(self, metric) * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0