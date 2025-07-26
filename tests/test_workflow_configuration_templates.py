#!/usr/bin/env python3
"""
Unit tests for workflow configuration template integration.

Tests the integration of template processing with the workflow configuration system,
ensuring proper separation between template processing and file content attachment.
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

from utils.workflow_configuration import WorkflowConfiguration
from utils.template_processor import get_template_variable_info


class TestWorkflowConfigurationTemplates(unittest.TestCase):
    """Test template integration with workflow configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = WorkflowConfiguration(base_path=Path(self.temp_dir))
        
        # Sample template config with mixed global/local variables
        self.template_config = {
            "template_name": "Test Template",
            "template_content": "Test content with {{ local_var }} and {{ global_var }}",
            "template_variables": {
                "global_var": {
                    "description": "Global variable",
                    "type": "string", 
                    "default": "global_value",
                    "apply_to_instructions": True
                },
                "local_var": {
                    "description": "Local variable",
                    "type": "string",
                    "default": "local_value", 
                    "apply_to_instructions": False
                },
                "another_global": {
                    "description": "Another global variable",
                    "type": "string",
                    "default": "another_global_value",
                    "apply_to_instructions": True
                }
            }
        }
        
        # Sample agent config with template variables
        self.agent_config = {
            "name": "TestWorkflowAgent",
            "class": "SequentialAgent",
            "module": "google.adk.agents",
            "description": "Workflow for {{ global_var }} testing",
            "sub_agents": [
                {
                    "name": "Agent1",
                    "class": "Agent",
                    "module": "google.adk.agents",
                    "model": "openai/gpt-4o",
                    "instruction": "You are specialized in {{ global_var }} with {{ another_global }} context.",
                    "description": "Agent 1 for {{ global_var }}"
                },
                {
                    "name": "Agent2",
                    "class": "Agent", 
                    "module": "google.adk.agents",
                    "model": "openai/gpt-4o",
                    "instruction": "You handle {{ global_var }} processing for {{ another_global }}.",
                    "description": "Agent 2 specialized in {{ global_var }}"
                }
            ]
        }
        
        # Set up configuration
        self.config.template_config = self.template_config
        self.config.agent_config = self.agent_config
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_apply_template_variables_to_agent_config(self):
        """Test applying template variables to agent configuration."""
        processed_config = self.config.apply_template_variables_to_agent_config()
        
        # Check that global variables were applied
        expected_description = "Workflow for global_value testing"
        self.assertEqual(processed_config["description"], expected_description)
        
        # Check sub-agent instructions
        agent1_instruction = processed_config["sub_agents"][0]["instruction"]
        expected_agent1 = "You are specialized in global_value with another_global_value context."
        self.assertEqual(agent1_instruction, expected_agent1)
        
        agent2_instruction = processed_config["sub_agents"][1]["instruction"]
        expected_agent2 = "You handle global_value processing for another_global_value."
        self.assertEqual(agent2_instruction, expected_agent2)
        
        # Check that original config is unchanged
        self.assertIn("{{ global_var }}", self.config.agent_config["description"])
        self.assertIn("{{ global_var }}", self.config.agent_config["sub_agents"][0]["instruction"])
    
    def test_template_processing_without_template_config(self):
        """Test template processing when template config is missing."""
        self.config.template_config = None
        
        # Should return original config when no template config
        processed_config = self.config.apply_template_variables_to_agent_config()
        self.assertEqual(processed_config, self.agent_config)
    
    def test_file_content_attachment_after_template_processing(self):
        """Test that file content attachment works after template processing."""
        # First apply template variables
        processed_config = self.config.apply_template_variables_to_agent_config()
        
        # Update the agent config with processed version
        self.config.agent_config = processed_config
        
        # Simulate file content with template-like patterns
        file_content_with_templates = """
        def example_function():
            # This contains {{ template_like }} patterns
            config = {
                "setting": "{{ value }}",
                "another": "{% if condition %}value{% endif %}"
            }
            return config
        """
        
        # Simulate targeted files
        self.config.targeted_files_by_agent = {
            "Agent1": [
                {
                    "file_name": "test_file.py",
                    "file_type": "python",
                    "file_content": file_content_with_templates
                }
            ]
        }
        
        # Apply file content
        modified_count = self.config.apply_targeted_files_to_agent_config()
        self.assertEqual(modified_count, 1)
        
        # Check that agent instruction was updated with file content
        agent1_instruction = self.config.agent_config["sub_agents"][0]["instruction"]
        
        # Should contain both processed template variables AND escaped file content
        self.assertIn("global_value", agent1_instruction)  # From template processing
        self.assertIn("another_global_value", agent1_instruction)  # From template processing
        self.assertIn("test_file.py", agent1_instruction)  # From file content attachment
        
        # File content should be escaped to prevent template processing
        self.assertIn("&#123;&#123; template_like &#125;&#125;", agent1_instruction)
        self.assertIn("&#123;&#123; value &#125;&#125;", agent1_instruction)
    
    def test_template_variable_info_extraction(self):
        """Test extraction of template variable information."""
        info = get_template_variable_info(self.template_config)
        
        # Check global variables
        self.assertEqual(info["global_var"]["scope"], "global")
        self.assertTrue(info["global_var"]["apply_to_instructions"])
        self.assertEqual(info["global_var"]["default"], "global_value")
        
        self.assertEqual(info["another_global"]["scope"], "global")
        self.assertTrue(info["another_global"]["apply_to_instructions"])
        
        # Check local variable
        self.assertEqual(info["local_var"]["scope"], "local")
        self.assertFalse(info["local_var"]["apply_to_instructions"])
        self.assertEqual(info["local_var"]["default"], "local_value")
    
    def test_template_processing_order(self):
        """Test that template processing happens before file content attachment."""
        # This test ensures the correct order of operations:
        # 1. Template variables applied to agent instructions
        # 2. File content attached with proper escaping
        
        # Step 1: Apply template variables
        processed_config = self.config.apply_template_variables_to_agent_config()
        
        # Verify template variables were processed
        self.assertNotIn("{{ global_var }}", processed_config["description"])
        self.assertIn("global_value", processed_config["description"])
        
        # Step 2: Set processed config and add file content
        self.config.agent_config = processed_config
        
        file_with_template_patterns = {
            "file_name": "config.py",
            "file_type": "python", 
            "file_content": "CONFIG = {'value': '{{ should_not_be_processed }}'}"
        }
        
        self.config.targeted_files_by_agent = {
            "Agent1": [file_with_template_patterns]
        }
        
        # Step 3: Apply file content
        self.config.apply_targeted_files_to_agent_config()
        
        # Verify final state
        final_instruction = self.config.agent_config["sub_agents"][0]["instruction"]
        
        # Should have processed template variables
        self.assertIn("global_value", final_instruction)
        self.assertIn("another_global_value", final_instruction)
        
        # Should have escaped file content patterns
        self.assertIn("&#123;&#123; should_not_be_processed &#125;&#125;", final_instruction)
        
        # Should NOT have unprocessed global template variables
        self.assertNotIn("{{ global_var }}", final_instruction)
    
    def test_error_handling_in_template_processing(self):
        """Test error handling during template processing."""
        # Create invalid template in agent config
        invalid_agent_config = {
            "name": "InvalidAgent",
            "instruction": "Invalid template {{ unclosed_brace",
            "class": "Agent"
        }
        
        self.config.agent_config = invalid_agent_config
        
        # Should handle errors gracefully and return original config
        processed_config = self.config.apply_template_variables_to_agent_config()
        
        # Should return original config on error
        self.assertEqual(processed_config["instruction"], "Invalid template {{ unclosed_brace")
    
    def test_load_template_config_from_content(self):
        """Test loading template config from YAML content string."""
        yaml_content = """
        template_name: "Test Template"
        template_variables:
          test_var:
            description: "Test variable"
            type: "string"
            default: "test_value"
            apply_to_instructions: true
        """
        
        loaded_config = self.config.load_template_config_from_content(yaml_content)
        
        self.assertEqual(loaded_config["template_name"], "Test Template")
        self.assertTrue(loaded_config["template_variables"]["test_var"]["apply_to_instructions"])
        self.assertEqual(loaded_config["template_variables"]["test_var"]["default"], "test_value")
    
    def test_load_agent_config_from_content(self):
        """Test loading agent config from YAML content string."""
        yaml_content = """
        name: "TestAgent"
        class: "Agent"
        instruction: "You are a {{ language }} expert."
        """
        
        loaded_config = self.config.load_agent_config_from_content(yaml_content)
        
        self.assertEqual(loaded_config["name"], "TestAgent")
        self.assertEqual(loaded_config["class"], "Agent")
        self.assertIn("{{ language }}", loaded_config["instruction"])


class TestTemplateProcessingIntegration(unittest.TestCase):
    """Integration tests for complete template processing workflow."""
    
    def test_end_to_end_template_workflow(self):
        """Test complete end-to-end template processing workflow."""
        # Create a complete workflow configuration
        config = WorkflowConfiguration()
        
        # Template config with mixed variables
        template_config = {
            "template_variables": {
                "analysis_type": {
                    "description": "Type of analysis",
                    "default": "security",
                    "apply_to_instructions": True
                },
                "output_format": {
                    "description": "Output format",
                    "default": "detailed",
                    "apply_to_instructions": False
                }
            }
        }
        
        # Agent config with templates
        agent_config = {
            "name": "AnalysisWorkflow",
            "class": "SequentialAgent", 
            "description": "Performs {{ analysis_type }} analysis",
            "sub_agents": [
                {
                    "name": "Analyzer",
                    "class": "Agent",
                    "instruction": "Perform {{ analysis_type }} analysis with comprehensive review.",
                    "model": "openai/gpt-4o"
                }
            ]
        }
        
        config.template_config = template_config
        config.agent_config = agent_config
        
        # Process templates
        processed_config = config.apply_template_variables_to_agent_config()
        
        # Verify processing
        self.assertEqual(processed_config["description"], "Performs security analysis")
        self.assertEqual(
            processed_config["sub_agents"][0]["instruction"],
            "Perform security analysis with comprehensive review."
        )
        
        # Verify original config unchanged
        self.assertIn("{{ analysis_type }}", agent_config["description"])


if __name__ == '__main__':
    unittest.main()