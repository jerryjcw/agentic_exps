"""
Prompt Updater - Applies prompt changes to agent configurations.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from copy import deepcopy

from .types import PromptSuggestion, AgentConfigUpdater

logger = logging.getLogger(__name__)


class PromptUpdater:
    """Updates agent prompts in configurations while preserving structure."""
    
    def __init__(self):
        self.config_updater = AgentConfigUpdater()
        self.update_history = []
    
    def apply_suggestions(
        self,
        agent_config: Dict[str, Any],
        suggestions: List[PromptSuggestion],
        max_suggestions: Optional[int] = None
    ) -> Tuple[Dict[str, Any], List[PromptSuggestion]]:
        """
        Apply prompt suggestions to agent configuration.
        
        Args:
            agent_config: Current agent configuration
            suggestions: List of prompt suggestions to apply
            max_suggestions: Maximum number of suggestions to apply
            
        Returns:
            Tuple of (updated_config, applied_suggestions)
        """
        updated_config = deepcopy(agent_config)
        applied_suggestions = []
        
        # Limit number of suggestions if specified
        if max_suggestions:
            suggestions = suggestions[:max_suggestions]
        
        # Track changes for history
        changes = []
        
        for suggestion in suggestions:
            try:
                # Get current prompt before update
                current_prompts = self.config_updater.extract_agent_prompts(updated_config)
                old_prompt = current_prompts.get(suggestion.agent_id, "")
                logger.info(f"Updating {suggestion.agent_id}: old_prompt={len(old_prompt)} chars")
                
                # Apply the suggestion
                updated_config = self.config_updater.update_agent_prompt(
                    updated_config,
                    suggestion.agent_id,
                    suggestion.new_prompt
                )
                
                # Verify the update was successful
                new_prompts = self.config_updater.extract_agent_prompts(updated_config)
                new_prompt = new_prompts.get(suggestion.agent_id, "")
                logger.info(f"After update {suggestion.agent_id}: new_prompt={len(new_prompt)} chars")
                
                if new_prompt != old_prompt:
                    applied_suggestions.append(suggestion)
                    changes.append({
                        'agent_id': suggestion.agent_id,
                        'old_prompt': old_prompt,
                        'new_prompt': new_prompt,
                        'reason': suggestion.reason,
                        'confidence': suggestion.confidence
                    })
                    logger.info(f"Applied suggestion for {suggestion.agent_id}: {suggestion.reason}")
                    logger.info(f"Old prompt = {old_prompt}, New prompt = {new_prompt}")
                else:
                    logger.warning(f"Failed to apply suggestion for {suggestion.agent_id}")
                    
            except Exception as e:
                logger.error(f"Error applying suggestion for {suggestion.agent_id}: {str(e)}")
                continue
        
        # Add to history
        self.update_history.append({
            'changes': changes,
            'total_suggestions': len(suggestions),
            'applied_suggestions': len(applied_suggestions)
        })
        
        return updated_config, applied_suggestions
    
    def validate_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that the configuration is still valid after updates.
        
        Args:
            config: Agent configuration to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check basic structure
            if not isinstance(config, dict):
                errors.append("Configuration must be a dictionary")
                return False, errors
            
            # Check required fields
            required_fields = ['name', 'class', 'module']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Validate agent structure recursively
            self._validate_agent_structure(config, errors, "root")
            
            # Check for empty prompts
            prompts = self.config_updater.extract_agent_prompts(config)
            for agent_id, prompt in prompts.items():
                if not prompt or not prompt.strip():
                    errors.append(f"Empty prompt for agent: {agent_id}")
            
            # Check for circular references (basic check)
            self._check_circular_references(config, errors)
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_agent_structure(
        self,
        agent_dict: Dict[str, Any],
        errors: List[str],
        path: str
    ) -> None:
        """Recursively validate agent structure."""
        if not isinstance(agent_dict, dict):
            errors.append(f"Agent at {path} must be a dictionary")
            return
        
        # Check for required fields in agents
        if 'name' in agent_dict:
            if 'class' not in agent_dict:
                errors.append(f"Agent {path} missing 'class' field")
            if 'module' not in agent_dict:
                errors.append(f"Agent {path} missing 'module' field")
        
        # Validate sub-agents
        if 'sub_agents' in agent_dict:
            if not isinstance(agent_dict['sub_agents'], list):
                errors.append(f"sub_agents at {path} must be a list")
            else:
                for i, sub_agent in enumerate(agent_dict['sub_agents']):
                    sub_path = f"{path}.sub_agents[{i}]"
                    self._validate_agent_structure(sub_agent, errors, sub_path)
    
    def _check_circular_references(self, config: Dict[str, Any], errors: List[str]) -> None:
        """Check for circular references in agent structure."""
        visited = set()
        
        def check_agent(agent_dict: Dict[str, Any], path: List[str]):
            agent_name = agent_dict.get('name', 'unnamed')
            
            if agent_name in visited:
                errors.append(f"Circular reference detected: {' -> '.join(path + [agent_name])}")
                return
            
            visited.add(agent_name)
            
            if 'sub_agents' in agent_dict:
                for sub_agent in agent_dict['sub_agents']:
                    check_agent(sub_agent, path + [agent_name])
            
            visited.remove(agent_name)
        
        check_agent(config, [])
    
    def get_prompt_diff(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        Get differences between prompts in old and new configurations.
        
        Args:
            old_config: Original configuration
            new_config: Updated configuration
            
        Returns:
            Dictionary mapping agent_id to {'old': old_prompt, 'new': new_prompt}
        """
        old_prompts = self.config_updater.extract_agent_prompts(old_config)
        new_prompts = self.config_updater.extract_agent_prompts(new_config)
        
        diff = {}
        
        # Find changed prompts
        for agent_id in set(old_prompts.keys()) | set(new_prompts.keys()):
            old_prompt = old_prompts.get(agent_id, "")
            new_prompt = new_prompts.get(agent_id, "")
            
            if old_prompt != new_prompt:
                diff[agent_id] = {
                    'old': old_prompt,
                    'new': new_prompt
                }
        
        return diff
    
