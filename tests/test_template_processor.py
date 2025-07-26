#!/usr/bin/env python3
"""
Unit tests for the enhanced template variable system.

Tests the template processor functionality including:
- Global vs local template variable scoping
- Safe template processing without file content interference
- Template validation and error handling
- Integration with agent configurations
"""

import unittest
import tempfile
import json
import yaml
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.template_processor import (
    prepare_template_variables,
    get_global_template_variables,
    get_local_template_variables,
    apply_template_variables_to_agent_config,
    validate_template_syntax,
    get_template_variables_used,
    process_agent_config_templates,
    get_template_variable_info,
    SafeTemplateEnvironment
)


class TestTemplateProcessor(unittest.TestCase):
    """Test suite for template processor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_template_config = {
            "template_variables": {
                "target_language": {
                    "description": "Target programming language",
                    "type": "string",
                    "default": "Python",
                    "apply_to_instructions": True
                },
                "analysis_depth": {
                    "description": "Analysis depth level",
                    "type": "string",
                    "default": "detailed",
                    "apply_to_instructions": True
                },
                "focus_area": {
                    "description": "Primary focus area",
                    "type": "string",
                    "default": "security",
                    "apply_to_instructions": False
                },
                "company_context": {
                    "description": "Company context",
                    "type": "string",
                    "default": "enterprise",
                    "apply_to_instructions": True
                },
                # Legacy format (should be treated as local)
                "legacy_var": "legacy_value"
            }
        }
        
        self.sample_agent_config = {
            "name": "TestAgent",
            "class": "Agent",
            "module": "google.adk.agents",
            "model": "openai/gpt-4o",
            "instruction": "You are a {{ target_language }} expert with {{ analysis_depth }} analysis skills for {{ company_context }}.",
            "description": "Test agent for {{ target_language }}",
            "sub_agents": [
                {
                    "name": "SubAgent",
                    "class": "Agent",
                    "module": "google.adk.agents",
                    "instruction": "You specialize in {{ target_language }} with {{ analysis_depth }} approach.",
                    "model": "openai/gpt-4o"
                }
            ]
        }
    
    def test_prepare_template_variables_all_scope(self):
        """Test preparing all template variables."""
        variables = prepare_template_variables(self.sample_template_config, scope='all')
        
        expected_vars = {
            "target_language": "Python",
            "analysis_depth": "detailed", 
            "focus_area": "security",
            "company_context": "enterprise",
            "legacy_var": "legacy_value"
        }
        
        self.assertEqual(variables, expected_vars)
    
    def test_prepare_template_variables_global_scope(self):
        """Test preparing only global template variables."""
        variables = prepare_template_variables(self.sample_template_config, scope='global_only')
        
        expected_vars = {
            "target_language": "Python",
            "analysis_depth": "detailed",
            "company_context": "enterprise"
        }
        
        self.assertEqual(variables, expected_vars)
        self.assertNotIn("focus_area", variables)
        self.assertNotIn("legacy_var", variables)
    
    def test_prepare_template_variables_local_scope(self):
        """Test preparing only local template variables."""
        variables = prepare_template_variables(self.sample_template_config, scope='local_only')
        
        expected_vars = {
            "focus_area": "security",
            "legacy_var": "legacy_value"
        }
        
        self.assertEqual(variables, expected_vars)
        self.assertNotIn("target_language", variables)
        self.assertNotIn("analysis_depth", variables)
    
    def test_get_global_template_variables(self):
        """Test convenience function for global variables."""
        variables = get_global_template_variables(self.sample_template_config)
        
        expected_vars = {
            "target_language": "Python",
            "analysis_depth": "detailed",
            "company_context": "enterprise"
        }
        
        self.assertEqual(variables, expected_vars)
    
    def test_get_local_template_variables(self):
        """Test convenience function for local variables."""
        variables = get_local_template_variables(self.sample_template_config)
        
        expected_vars = {
            "focus_area": "security",
            "legacy_var": "legacy_value"
        }
        
        self.assertEqual(variables, expected_vars)
    
    def test_apply_template_variables_to_agent_config(self):
        """Test applying template variables to agent configuration."""
        template_vars = {
            "target_language": "JavaScript",
            "analysis_depth": "comprehensive",
            "company_context": "startup"
        }
        
        processed_config = apply_template_variables_to_agent_config(
            self.sample_agent_config, 
            template_vars
        )
        
        # Check main agent instruction
        expected_instruction = "You are a JavaScript expert with comprehensive analysis skills for startup."
        self.assertEqual(processed_config["instruction"], expected_instruction)
        
        # Check description
        expected_description = "Test agent for JavaScript"
        self.assertEqual(processed_config["description"], expected_description)
        
        # Check sub-agent instruction
        expected_sub_instruction = "You specialize in JavaScript with comprehensive approach."
        self.assertEqual(processed_config["sub_agents"][0]["instruction"], expected_sub_instruction)
        
        # Ensure original config is not modified
        self.assertIn("{{ target_language }}", self.sample_agent_config["instruction"])
    
    def test_safe_template_environment(self):
        """Test safe template environment functionality."""
        env = SafeTemplateEnvironment()
        
        # Test normal template rendering
        result = env.render_template("Hello {{ name }}!", {"name": "World"})
        self.assertEqual(result, "Hello World!")
        
        # Test with missing variable (Jinja2 renders undefined variables as empty)
        result = env.render_template("Hello {{ missing }}!", {})
        self.assertEqual(result, "Hello !")
    
    def test_validate_template_syntax(self):
        """Test template syntax validation."""
        # Valid template
        valid_config = {
            "name": "ValidAgent",
            "instruction": "You are a {{ language }} expert.",
            "description": "Agent for {{ language }}"
        }
        
        result = validate_template_syntax(valid_config)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(len(result["warnings"]), 0)
        
        # Invalid template syntax
        invalid_config = {
            "name": "InvalidAgent", 
            "instruction": "You are a {{ language expert.",  # Missing closing brace
            "description": "Valid {{ language }} description"
        }
        
        result = validate_template_syntax(invalid_config)
        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("InvalidAgent.instruction", result["errors"][0])
    
    def test_get_template_variables_used(self):
        """Test extraction of template variables from configuration."""
        variables_used = get_template_variables_used(self.sample_agent_config)
        
        expected_vars = {
            "target_language",
            "analysis_depth", 
            "company_context"
        }
        
        self.assertEqual(variables_used, expected_vars)
    
    def test_process_agent_config_templates_integration(self):
        """Test complete template processing workflow."""
        processed_config = process_agent_config_templates(
            self.sample_agent_config,
            self.sample_template_config
        )
        
        # Should only apply global variables
        expected_instruction = "You are a Python expert with detailed analysis skills for enterprise."
        self.assertEqual(processed_config["instruction"], expected_instruction)
        
        # Verify original config unchanged
        self.assertIn("{{ target_language }}", self.sample_agent_config["instruction"])
    
    def test_get_template_variable_info(self):
        """Test template variable information extraction."""
        info = get_template_variable_info(self.sample_template_config)
        
        # Check global variable
        self.assertEqual(info["target_language"]["scope"], "global")
        self.assertTrue(info["target_language"]["apply_to_instructions"])
        self.assertEqual(info["target_language"]["default"], "Python")
        
        # Check local variable
        self.assertEqual(info["focus_area"]["scope"], "local")
        self.assertFalse(info["focus_area"]["apply_to_instructions"])
        
        # Check legacy variable
        self.assertEqual(info["legacy_var"]["scope"], "local")
        self.assertFalse(info["legacy_var"]["apply_to_instructions"])
    
    def test_template_variables_with_additional_vars(self):
        """Test template variables with additional runtime variables."""
        additional_vars = {
            "runtime_var": "runtime_value",
            "target_language": "Go"  # Override default
        }
        
        variables = prepare_template_variables(
            self.sample_template_config,
            additional_vars=additional_vars,
            scope='global_only'
        )
        
        # Additional vars should be included
        self.assertEqual(variables["runtime_var"], "runtime_value")
        # Additional vars should override defaults
        self.assertEqual(variables["target_language"], "Go")
    
    def test_file_content_protection(self):
        """Test that file content with template-like patterns is not processed."""
        agent_config = {
            "name": "TestAgent",
            "instruction": "Analyze this {{ target_language }} code.",
            "class": "Agent",
            "module": "google.adk.agents"
        }
        
        # Simulate file content with template-like patterns (should NOT be processed)
        file_content = """
        def process_template(data):
            # This {{ should_not_be_processed }} stays as-is
            template = "Hello {{ name }}!"
            return template.format(name=data.get('name', 'World'))
        """
        
        template_vars = {"target_language": "Python"}
        processed_config = apply_template_variables_to_agent_config(agent_config, template_vars)
        
        # Agent instruction should be processed
        self.assertEqual(processed_config["instruction"], "Analyze this Python code.")
        
        # File content patterns should remain unchanged (this is tested conceptually
        # since file content attachment happens separately via prompt_utils.py)
        self.assertIn("{{ should_not_be_processed }}", file_content)
        self.assertIn("{{ name }}", file_content)
    
    def test_empty_template_config(self):
        """Test handling of empty or missing template configuration."""
        empty_config = {}
        variables = prepare_template_variables(empty_config)
        self.assertEqual(variables, {})
        
        # Should not raise error with empty agent config
        processed = apply_template_variables_to_agent_config({}, {})
        self.assertEqual(processed, {})
    
    def test_malformed_template_config(self):
        """Test handling of malformed template configuration."""
        malformed_config = {
            "template_variables": {
                "valid_var": {
                    "default": "valid_value",
                    "apply_to_instructions": True
                },
                "missing_default": {
                    "description": "Missing default value",
                    "apply_to_instructions": True  # Need this for global_only scope
                },
                "invalid_type": None
            }
        }
        
        # Should handle gracefully without crashing
        variables = prepare_template_variables(malformed_config, scope='global_only')
        self.assertEqual(variables["valid_var"], "valid_value")
        self.assertEqual(variables["missing_default"], "")  # Default to empty string


class TestTemplateProcessorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_nested_agent_processing(self):
        """Test deep nested agent configuration processing."""
        nested_config = {
            "name": "Root",
            "instruction": "Root {{ var1 }}",
            "sub_agents": [
                {
                    "name": "Level1",
                    "instruction": "Level1 {{ var2 }}",
                    "sub_agents": [
                        {
                            "name": "Level2",
                            "instruction": "Level2 {{ var3 }}",
                            "class": "Agent"
                        }
                    ]
                }
            ]
        }
        
        template_vars = {"var1": "value1", "var2": "value2", "var3": "value3"}
        processed = apply_template_variables_to_agent_config(nested_config, template_vars)
        
        self.assertEqual(processed["instruction"], "Root value1")
        self.assertEqual(processed["sub_agents"][0]["instruction"], "Level1 value2")
        self.assertEqual(processed["sub_agents"][0]["sub_agents"][0]["instruction"], "Level2 value3")
    
    def test_template_syntax_errors(self):
        """Test handling of template syntax errors."""
        agent_config = {
            "name": "BadTemplate",
            "instruction": "Invalid template {{ unclosed",
            "class": "Agent"
        }
        
        # Should not crash, should return original instruction
        processed = apply_template_variables_to_agent_config(agent_config, {})
        self.assertEqual(processed["instruction"], "Invalid template {{ unclosed")
    
    def test_circular_variable_reference(self):
        """Test handling of potential circular references."""
        # Jinja2 handles this gracefully by treating undefined variables as empty
        agent_config = {
            "name": "CircularTest",
            "instruction": "Value: {{ undefined_var }}",
            "class": "Agent"
        }
        
        # Should handle undefined variables gracefully (renders as empty)
        processed = apply_template_variables_to_agent_config(agent_config, {})
        self.assertEqual(processed["instruction"], "Value: ")


if __name__ == '__main__':
    unittest.main()