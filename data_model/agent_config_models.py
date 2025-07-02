#!/usr/bin/env python3
"""
Data models for agent configurations using Pydantic for validation.

This module defines the data structures required to validate and instantiate
Google ADK agents from JSON configurations.
"""

from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import json
from pathlib import Path


class ToolConfig(BaseModel):
    """Configuration for a tool that can be used by an agent."""
    
    class_: str = Field(alias="class", description="Tool class name")
    module: str = Field(description="Module where the tool class is defined")
    function_name: Optional[str] = Field(None, description="Function name for FunctionTool")
    function_module: Optional[str] = Field(None, description="Module where the function is defined")
    agent: Optional['AgentConfig'] = Field(None, description="Agent configuration for AgentTool")
    
    @model_validator(mode='after')
    def validate_tool_fields(self):
        """Validate that tools have required fields based on their class."""
        if self.class_ in ['FunctionTool', 'LongRunningFunctionTool']:
            if not self.function_name or not self.function_module:
                raise ValueError(f"function_name and function_module are required for {self.class_}")
        elif self.class_ == 'AgentTool':
            if not self.agent:
                raise ValueError("agent field is required for AgentTool")
        return self


class BaseAgentConfig(BaseModel):
    """Base configuration for all agent types."""
    
    name: str = Field(description="Unique name for the agent")
    class_: str = Field(alias="class", description="Agent class name")
    module: str = Field(description="Module where the agent class is defined")
    description: Optional[str] = Field(None, description="Human-readable description of the agent")
    
    @field_validator('class_')
    @classmethod
    def validate_agent_class(cls, v):
        """Validate that the agent class is supported."""
        valid_classes = ['Agent', 'SequentialAgent', 'ParallelAgent', 'LoopAgent']
        if v not in valid_classes:
            raise ValueError(f"Agent class must be one of {valid_classes}, got {v}")
        return v


class AgentConfig(BaseAgentConfig):
    """Configuration for a base Agent (LLM agent)."""
    
    model: Optional[str] = Field(None, description="Model identifier (e.g., 'openai:gpt-4o')")
    instruction: Optional[str] = Field(None, description="System instruction for the agent")
    output_key: Optional[str] = Field(None, description="Key for storing agent output")
    tools: Optional[List[Union[str, ToolConfig]]] = Field(default_factory=list, description="Tools available to the agent")
    
    # Additional optional parameters supported by Google ADK
    global_instruction: Optional[str] = Field(None, description="Global instruction for the agent")
    generate_content_config: Optional[Dict[str, Any]] = Field(None, description="Content generation configuration")
    disallow_transfer_to_parent: Optional[bool] = Field(None, description="Disallow transfer to parent agent")
    disallow_transfer_to_peers: Optional[bool] = Field(None, description="Disallow transfer to peer agents")
    include_contents: Optional[bool] = Field(None, description="Include contents in agent context")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input validation schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output validation schema")
    planner: Optional[Dict[str, Any]] = Field(None, description="Planner configuration")
    code_executor: Optional[Dict[str, Any]] = Field(None, description="Code executor configuration")
    
    @model_validator(mode='after')
    def validate_agent_requirements(self):
        """Validate that Agent class has appropriate fields."""
        if self.class_ == 'Agent':
            # For Agent class, name is required (already validated by BaseAgentConfig)
            # Other fields are optional but model is typically expected
            pass
        return self


class CompositeAgentConfig(BaseAgentConfig):
    """Configuration for composite agents (Sequential, Parallel, Loop)."""
    
    sub_agents: Optional[List['AgentConfig']] = Field(default_factory=list, description="Sub-agents for composite agents")
    max_iterations: Optional[int] = Field(None, description="Maximum iterations for LoopAgent")
    
    # Callback configurations
    before_agent_callback: Optional[Dict[str, Any]] = Field(None, description="Callback before agent execution")
    after_agent_callback: Optional[Dict[str, Any]] = Field(None, description="Callback after agent execution")
    parent_agent: Optional[str] = Field(None, description="Parent agent reference")
    
    @model_validator(mode='after')
    def validate_composite_agent_requirements(self):
        """Validate composite agent specific requirements."""
        if self.class_ == 'LoopAgent':
            # LoopAgent can have max_iterations
            if self.max_iterations is not None and (not isinstance(self.max_iterations, int) or self.max_iterations < 1):
                raise ValueError("max_iterations must be a positive integer")
        
        elif self.class_ in ['SequentialAgent', 'ParallelAgent']:
            # These agents should not have max_iterations
            if self.max_iterations is not None:
                raise ValueError(f"{self.class_} does not support max_iterations parameter")
        
        return self


# Update forward references  
ToolConfig.model_rebuild()
CompositeAgentConfig.model_rebuild()

# Union type for any agent configuration (after class definitions)
AgentConfigUnion = Union[AgentConfig, CompositeAgentConfig]


class AgentConfigValidator:
    """Validator class for agent configurations."""
    
    @staticmethod
    def validate_json_file(file_path: Union[str, Path]) -> AgentConfigUnion:
        """
        Validate a JSON configuration file and return the parsed agent config.
        
        Args:
            file_path: Path to the JSON configuration file
            
        Returns:
            AgentConfig: Validated agent configuration
            
        Raises:
            ValidationError: If the configuration is invalid
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the JSON is malformed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        return AgentConfigValidator.validate_dict(config_data)
    
    @staticmethod
    def validate_dict(config_data: Dict[str, Any]) -> AgentConfigUnion:
        """
        Validate a configuration dictionary and return the parsed agent config.
        
        Args:
            config_data: Dictionary containing agent configuration
            
        Returns:
            AgentConfig: Validated agent configuration
            
        Raises:
            ValidationError: If the configuration is invalid
        """
        # Make a copy to avoid modifying the original
        config = config_data.copy()
        
        # Determine agent type based on class field
        agent_class = config.get('class', 'Agent')
        
        # Add default values for simple configs
        if 'class' not in config:
            config['class'] = 'Agent'
        if 'module' not in config:
            config['module'] = 'google.adk.agents'
        
        if agent_class == 'Agent':
            return AgentConfig(**config)
        elif agent_class in ['SequentialAgent', 'ParallelAgent', 'LoopAgent']:
            return CompositeAgentConfig(**config)
        else:
            raise ValueError(f"Unknown agent class: {agent_class}")
    
    @staticmethod
    def validate_agent_hierarchy(config: AgentConfigUnion) -> List[str]:
        """
        Validate the agent hierarchy and return any validation warnings.
        
        Args:
            config: Agent configuration to validate
            
        Returns:
            List[str]: List of validation warnings
        """
        warnings = []
        
        def _validate_recursive(agent_config: AgentConfigUnion, depth: int = 0, path: str = ""):
            current_path = f"{path}.{agent_config.name}" if path else agent_config.name
            
            # Check nesting depth
            if depth > 5:
                warnings.append(f"Deep nesting detected at {current_path} (depth: {depth})")
            
            # Check for agents with same name
            names_at_level = set()
            if hasattr(agent_config, 'sub_agents') and agent_config.sub_agents:
                for sub_agent in agent_config.sub_agents:
                    if sub_agent.name in names_at_level:
                        warnings.append(f"Duplicate agent name '{sub_agent.name}' at {current_path}")
                    names_at_level.add(sub_agent.name)
                    _validate_recursive(sub_agent, depth + 1, current_path)
            
            # Validate agent-specific requirements
            if agent_config.class_ == 'Agent':
                if not hasattr(agent_config, 'model') or not hasattr(agent_config, 'instruction'):
                    pass  # These are optional for Agent
                elif not agent_config.model and not agent_config.instruction:
                    warnings.append(f"Agent {current_path} has neither model nor instruction")
            
            if agent_config.class_ in ['SequentialAgent', 'ParallelAgent', 'LoopAgent']:
                if not hasattr(agent_config, 'sub_agents') or not agent_config.sub_agents:
                    warnings.append(f"Composite agent {current_path} has no sub-agents")
        
        _validate_recursive(config)
        return warnings


def validate_configuration_file(file_path: Union[str, Path]) -> tuple[AgentConfigUnion, List[str]]:
    """
    Convenience function to validate a configuration file and return config with warnings.
    
    Args:
        file_path: Path to the JSON configuration file
        
    Returns:
        tuple: (validated_config, list_of_warnings)
    """
    config = AgentConfigValidator.validate_json_file(file_path)
    warnings = AgentConfigValidator.validate_agent_hierarchy(config)
    return config, warnings


def validate_configuration_dict(config_dict: Dict[str, Any]) -> tuple[AgentConfigUnion, List[str]]:
    """
    Convenience function to validate a configuration dictionary and return config with warnings.
    
    Args:
        config_dict: Dictionary containing agent configuration
        
    Returns:
        tuple: (validated_config, list_of_warnings)
    """
    config = AgentConfigValidator.validate_dict(config_dict)
    warnings = AgentConfigValidator.validate_agent_hierarchy(config)
    return config, warnings