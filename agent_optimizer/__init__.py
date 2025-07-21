"""
Agent Optimizer - A system for iteratively improving agent workflow configurations.

This module provides tools to optimize agent prompts by:
1. Running agent workflows
2. Evaluating outputs against expected results
3. Generating suggestions for improvement
4. Updating agent configurations
5. Iterating until convergence or maximum iterations

Main components:
- AgentOptimizer: Main orchestrator
- WorkflowRunner: Executes agent workflows
- OutputEvaluator: Evaluates and scores outputs
- SuggestionGenerator: Generates improvement suggestions
- PromptUpdater: Updates agent configurations
- TraceExtractor: Extracts execution traces
"""

from .optimizer import AgentOptimizer
from .runner import WorkflowRunner
from .critic import OutputEvaluator
from .suggester import SuggestionGenerator
from .updater import PromptUpdater
from .trace import TraceExtractor
from .types import (
    OptimizationInput,
    OptimizationResult,
    OptimizationConfig,
    OptimizationObjective,
    InputOutputPair,
    AggregationStrategy,
    EvaluationResult,
    PromptSuggestion,
    WorkflowTrace,
    AgentTrace,
    LLMServiceError
)

__version__ = "1.0.0"
__author__ = "Agent Optimizer Team"

__all__ = [
    'AgentOptimizer',
    'WorkflowRunner',
    'OutputEvaluator',
    'SuggestionGenerator',
    'PromptUpdater',
    'TraceExtractor',
    'OptimizationInput',
    'OptimizationResult',
    'OptimizationConfig',
    'OptimizationObjective',
    'InputOutputPair',
    'AggregationStrategy',
    'EvaluationResult',
    'PromptSuggestion',
    'WorkflowTrace',
    'AgentTrace',
    'LLMServiceError'
]