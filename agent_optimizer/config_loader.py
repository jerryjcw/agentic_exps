"""
Configuration loader for optimizer prompts.

This module provides simple, clean access to YAML configuration files
without making configuration directories into Python modules.
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class OptimizerConfigLoader:
    """Loads and manages optimizer prompts from YAML configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent
            self.config_path = project_root / "config" / "optimizer" / "yaml" / "optimizer_prompts.yaml"
        else:
            self.config_path = Path(config_path)
        
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load the YAML configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Optimizer config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def reload_config(self) -> None:
        """Reload the configuration from file."""
        self._load_config()
    
    # Critic prompts
    def get_critic_prompt(self, prompt_type: str) -> str:
        """Get a critic evaluation prompt."""
        return self._config['critic']['evaluation'][prompt_type]
    
    def get_critic_system_message(self, message_type: str = 'default') -> str:
        """Get a critic system message."""
        return self._config['critic']['system_messages'][message_type]
    
    def get_all_critic_prompts(self) -> Dict[str, str]:
        """Get all critic evaluation prompts."""
        return self._config['critic']['evaluation']
    
    # Suggester prompts
    def get_suggester_prompt(self, prompt_type: str) -> str:
        """Get a suggester generation prompt."""
        return self._config['suggester']['generation'][prompt_type]
    
    def get_suggester_system_message(self, message_type: str = 'default') -> str:
        """Get a suggester system message."""
        return self._config['suggester']['system_messages'][message_type]
    
    def get_all_suggester_prompts(self) -> Dict[str, str]:
        """Get all suggester generation prompts."""
        return self._config['suggester']['generation']
    
    # Improvement templates
    def get_improvement_additions(self, improvement_type: str) -> list:
        """Get improvement additions for prompt enhancement."""
        return self._config['suggester']['improvements'][improvement_type]
    
    def get_improvement_template(self, template_type: str) -> str:
        """Get improvement template."""
        return self._config['suggester']['improvements'][template_type]
    
    # Common templates
    def get_template(self, template_type: str) -> str:
        """Get a reusable template."""
        return self._config['templates'][template_type]
    
    def get_common_instructions(self, instruction_type: str) -> str:
        """Get common instructions."""
        return self._config['templates']['common_instructions'][instruction_type]
    
    # Utility methods
    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary."""
        return self._config.copy()


# Global instance for easy access
_config_loader = None

def get_optimizer_config() -> OptimizerConfigLoader:
    """Get the global optimizer config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = OptimizerConfigLoader()
    return _config_loader

def reload_optimizer_config():
    """Reload optimizer configuration from file."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload_config()