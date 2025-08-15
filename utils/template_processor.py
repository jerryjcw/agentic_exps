"""
Template Variable Processor for Agent Configurations

This module provides safe template variable processing for agent instructions
without interfering with file content attachment.

Key Design Principles:
1. Template processing happens BEFORE file content attachment
2. Only original agent instructions are processed for templates
3. File contents are never processed as templates (they're escaped during attachment)
4. Two-phase approach ensures clean separation of concerns
"""

import logging
from typing import Dict, Any, Optional
from jinja2 import Template, Environment, BaseLoader, TemplateSyntaxError
import copy

logger = logging.getLogger(__name__)


class SafeTemplateEnvironment:
    """
    Safe Jinja2 environment for processing agent instruction templates.
    
    This environment is configured to be safe and predictable for processing
    agent instructions while avoiding interference with file content.
    """
    
    def __init__(self):
        """Initialize safe template environment."""
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # We want raw text output
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    def render_template(self, template_string: str, variables: Dict[str, Any]) -> str:
        """
        Safely render a template string with given variables.
        
        Args:
            template_string: The template string to render
            variables: Dictionary of template variables
            
        Returns:
            Rendered string
            
        Raises:
            TemplateSyntaxError: If template syntax is invalid
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**variables)
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            # Return original string if rendering fails
            return template_string


def prepare_template_variables(template_config: Dict[str, Any], 
                             additional_vars: Optional[Dict[str, Any]] = None,
                             scope: str = 'all') -> Dict[str, Any]:
    """
    Prepare template variables from template configuration and additional variables.
    
    Args:
        template_config: Template configuration dictionary
        additional_vars: Additional variables to include
        scope: Variable scope filter ('all', 'global_only', 'local_only')
               - 'all': Return all variables
               - 'global_only': Return only variables with apply_to_instructions=true
               - 'local_only': Return only variables with apply_to_instructions=false/unset
        
    Returns:
        Dictionary of template variables with their values based on scope
    """
    variables = {}
    
    # Extract variables from template_variables based on scope
    template_variables = template_config.get('template_variables', {})
    for var_name, var_config in template_variables.items():
        if isinstance(var_config, dict):
            # Get default value
            default_value = var_config.get('default', '')
            
            # Check apply_to_instructions flag (defaults to False for backward compatibility)
            apply_to_instructions = var_config.get('apply_to_instructions', False)
            
            # Filter based on scope
            if scope == 'all':
                variables[var_name] = default_value
            elif scope == 'global_only' and apply_to_instructions:
                variables[var_name] = default_value
            elif scope == 'local_only' and not apply_to_instructions:
                variables[var_name] = default_value
        else:
            # Handle simple string values (legacy format - treated as local scope)
            if scope in ['all', 'local_only']:
                variables[var_name] = var_config
    
    # Add any additional variables (always included regardless of scope)
    if additional_vars:
        variables.update(additional_vars)
    
    logger.debug(f"Prepared template variables for scope '{scope}': {list(variables.keys())}")
    return variables


def get_global_template_variables(template_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get only template variables marked for global application to agent instructions.
    
    Args:
        template_config: Template configuration dictionary
        
    Returns:
        Dictionary of template variables that should be applied globally
    """
    return prepare_template_variables(template_config, scope='global_only')


def get_local_template_variables(template_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get only template variables for local application to template_content.
    
    Args:
        template_config: Template configuration dictionary
        
    Returns:
        Dictionary of template variables that should be applied only locally
    """
    return prepare_template_variables(template_config, scope='local_only')


def apply_template_variables_to_agent_config(agent_config: Dict[str, Any], 
                                           template_variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply template variables to agent configuration instructions.
    
    This function processes ONLY the original agent instructions, before any
    file content is attached. It recursively processes all agents in the
    configuration hierarchy.
    
    IMPORTANT: This must be called BEFORE file content attachment to avoid
    processing file contents as templates.
    
    Args:
        agent_config: Agent configuration dictionary (will be deep copied)
        template_variables: Dictionary of template variables
        
    Returns:
        New agent configuration with template variables applied to instructions
    """
    # Deep copy to avoid modifying original config
    processed_config = copy.deepcopy(agent_config)
    
    # Create template environment
    template_env = SafeTemplateEnvironment()
    
    def _process_agent_instruction(agent: Dict[str, Any]) -> None:
        """Recursively process agent instructions with template variables."""
        
        # Process instruction field if it exists and is a string
        if 'instruction' in agent and isinstance(agent['instruction'], str):
            original_instruction = agent['instruction']
            
            # Check if instruction contains template patterns
            if '{{' in original_instruction or '{%' in original_instruction:
                try:
                    processed_instruction = template_env.render_template(
                        original_instruction, 
                        template_variables
                    )
                    agent['instruction'] = processed_instruction
                    logger.info(f"Applied template variables to agent '{agent.get('name', 'unknown')}'")
                    
                except TemplateSyntaxError as e:
                    logger.warning(f"Template syntax error in agent '{agent.get('name', 'unknown')}' instruction: {e}")
                    # Keep original instruction if template processing fails
                
                except Exception as e:
                    logger.warning(f"Failed to process template in agent '{agent.get('name', 'unknown')}': {e}")
                    # Keep original instruction if template processing fails
        
        # Process other potentially templatable fields
        for field in ['description', 'global_instruction']:
            if field in agent and isinstance(agent[field], str):
                if '{{' in agent[field] or '{%' in agent[field]:
                    try:
                        agent[field] = template_env.render_template(
                            agent[field], 
                            template_variables
                        )
                        logger.debug(f"Applied template variables to agent '{agent.get('name', 'unknown')}' {field}")
                    except Exception as e:
                        logger.warning(f"Failed to process template in agent {field}: {e}")
        
        # Recursively process sub_agents
        if 'sub_agents' in agent and agent['sub_agents']:
            for sub_agent in agent['sub_agents']:
                _process_agent_instruction(sub_agent)
    
    # Process the root agent configuration
    _process_agent_instruction(processed_config)
    
    return processed_config


def validate_template_syntax(agent_config: Dict[str, Any]) -> Dict[str, list]:
    """
    Validate template syntax in agent configuration without processing.
    
    Args:
        agent_config: Agent configuration to validate
        
    Returns:
        Dictionary with 'errors' and 'warnings' lists
    """
    errors = []
    warnings = []
    template_env = SafeTemplateEnvironment()
    
    def _validate_agent_templates(agent: Dict[str, Any], path: str = "") -> None:
        """Recursively validate agent template syntax."""
        agent_path = f"{path}.{agent.get('name', 'unknown')}" if path else agent.get('name', 'unknown')
        
        # Check instruction field
        if 'instruction' in agent and isinstance(agent['instruction'], str):
            instruction = agent['instruction']
            if '{{' in instruction or '{%' in instruction:
                try:
                    template_env.env.from_string(instruction)
                except TemplateSyntaxError as e:
                    errors.append(f"Template syntax error in {agent_path}.instruction: {e}")
                except Exception as e:
                    warnings.append(f"Template validation warning in {agent_path}.instruction: {e}")
        
        # Check other fields
        for field in ['description', 'global_instruction']:
            if field in agent and isinstance(agent[field], str):
                field_content = agent[field]
                if '{{' in field_content or '{%' in field_content:
                    try:
                        template_env.env.from_string(field_content)
                    except TemplateSyntaxError as e:
                        errors.append(f"Template syntax error in {agent_path}.{field}: {e}")
                    except Exception as e:
                        warnings.append(f"Template validation warning in {agent_path}.{field}: {e}")
        
        # Validate sub_agents
        if 'sub_agents' in agent and agent['sub_agents']:
            for sub_agent in agent['sub_agents']:
                _validate_agent_templates(sub_agent, agent_path)
    
    _validate_agent_templates(agent_config)
    
    return {
        'errors': errors,
        'warnings': warnings
    }


def get_template_variables_used(agent_config: Dict[str, Any]) -> set:
    """
    Extract all template variables used in agent configuration.
    
    Args:
        agent_config: Agent configuration to analyze
        
    Returns:
        Set of variable names used in templates
    """
    import re
    
    variables_used = set()
    variable_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
    
    def _extract_variables(agent: Dict[str, Any]) -> None:
        """Recursively extract variables from agent templates."""
        
        # Check instruction field
        if 'instruction' in agent and isinstance(agent['instruction'], str):
            matches = re.findall(variable_pattern, agent['instruction'])
            variables_used.update(matches)
        
        # Check other fields
        for field in ['description', 'global_instruction']:
            if field in agent and isinstance(agent[field], str):
                matches = re.findall(variable_pattern, agent[field])
                variables_used.update(matches)
        
        # Process sub_agents
        if 'sub_agents' in agent and agent['sub_agents']:
            for sub_agent in agent['sub_agents']:
                _extract_variables(sub_agent)
    
    _extract_variables(agent_config)
    return variables_used


# Convenience function for backward compatibility
def process_agent_config_templates(agent_config: Dict[str, Any], 
                                 template_config: Dict[str, Any],
                                 additional_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Complete template processing workflow for agent configuration.
    
    This is a convenience function that combines variable preparation and
    template application in one call. Only applies variables marked with
    apply_to_instructions=true to agent instructions.
    
    Args:
        agent_config: Agent configuration dictionary
        template_config: Template configuration dictionary
        additional_vars: Additional variables to include
        
    Returns:
        Agent configuration with global templates processed
    """
    # Prepare only global template variables (apply_to_instructions=true)
    variables = get_global_template_variables(template_config)
    
    # Add any additional variables
    if additional_vars:
        variables.update(additional_vars)
    
    # Apply templates to agent config
    return apply_template_variables_to_agent_config(agent_config, variables)


def get_template_variable_info(template_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information about all template variables and their scope.
    
    Args:
        template_config: Template configuration dictionary
        
    Returns:
        Dictionary with variable info including scope and configuration
    """
    info = {}
    template_variables = template_config.get('template_variables', {})
    
    for var_name, var_config in template_variables.items():
        if isinstance(var_config, dict):
            info[var_name] = {
                'default': var_config.get('default', ''),
                'description': var_config.get('description', ''),
                'type': var_config.get('type', 'string'),
                'apply_to_instructions': var_config.get('apply_to_instructions', False),
                'scope': 'global' if var_config.get('apply_to_instructions', False) else 'local'
            }
        else:
            # Legacy format
            info[var_name] = {
                'default': var_config,
                'description': '',
                'type': 'string',
                'apply_to_instructions': False,
                'scope': 'local'
            }
    
    return info