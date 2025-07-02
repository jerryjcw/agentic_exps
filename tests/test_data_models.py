#!/usr/bin/env python3
"""
Test the data models with existing JSON configuration examples.
"""

import unittest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_model import (
    AgentConfigValidator,
    validate_configuration_file,
    validate_configuration_dict
)
from pydantic import ValidationError


class TestDataModels(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_dir = Path(__file__).parent.parent / "config" / "json_examples"
        self.test_configs = [
            "code_improvement_workflow.json",
            "financial_analysis_workflow.json", 
            "example_agent_config.json"
        ]
    
    def test_validate_code_improvement_workflow(self):
        """Test validation of the code improvement workflow configuration."""
        config_path = self.config_dir / "code_improvement_workflow.json"
        
        try:
            config, warnings = validate_configuration_file(config_path)
            
            # Verify basic properties
            self.assertEqual(config.name, "CodeImprovementWorkflow")
            self.assertEqual(config.class_, "SequentialAgent")
            self.assertEqual(config.module, "google.adk.agents")
            
            # Verify sub-agents exist
            self.assertTrue(hasattr(config, 'sub_agents'))
            self.assertGreater(len(config.sub_agents), 0)
            
            # Check that we have expected agents
            agent_names = [agent.name for agent in config.sub_agents]
            expected_agents = [
                "CodebaseAnalysisAgent",
                "IssueIdentificationLoop", 
                "SolutionDesignParallel",
                "QualityAssuranceReview",
                "DocumentationGenerator"
            ]
            
            for expected_agent in expected_agents:
                self.assertIn(expected_agent, agent_names)
            
            # Verify loop agent has max_iterations
            loop_agent = next(agent for agent in config.sub_agents if agent.name == "IssueIdentificationLoop")
            self.assertEqual(loop_agent.class_, "LoopAgent")
            if hasattr(loop_agent, 'max_iterations'):
                self.assertEqual(loop_agent.max_iterations, 4)
            
            # Verify parallel agent structure
            parallel_agent = next(agent for agent in config.sub_agents if agent.name == "SolutionDesignParallel")
            self.assertEqual(parallel_agent.class_, "ParallelAgent")
            self.assertGreater(len(parallel_agent.sub_agents), 0)
            
            print(f"✓ Code improvement workflow validation passed with {len(warnings)} warnings")
            for warning in warnings:
                print(f"  Warning: {warning}")
                
        except ValidationError as e:
            self.fail(f"Code improvement workflow validation failed: {e}")
    
    def test_validate_financial_analysis_workflow(self):
        """Test validation of the financial analysis workflow configuration."""
        config_path = self.config_dir / "financial_analysis_workflow.json"
        
        try:
            config, warnings = validate_configuration_file(config_path)
            
            # Verify basic properties
            self.assertEqual(config.name, "FinancialAnalysisWorkflow")
            self.assertEqual(config.class_, "SequentialAgent")
            
            # Verify sub-agents exist and have expected structure
            self.assertTrue(hasattr(config, 'sub_agents'))
            self.assertGreater(len(config.sub_agents), 0)
            
            # Find and verify data collection agent has tools
            data_collection_agent = next(
                agent for agent in config.sub_agents 
                if agent.name == "DataCollectionAgent"
            )
            self.assertTrue(hasattr(data_collection_agent, 'tools'))
            self.assertGreater(len(data_collection_agent.tools), 0)
            
            print(f"✓ Financial analysis workflow validation passed with {len(warnings)} warnings")
            for warning in warnings:
                print(f"  Warning: {warning}")
                
        except ValidationError as e:
            self.fail(f"Financial analysis workflow validation failed: {e}")
    
    def test_validate_example_agent_config(self):
        """Test validation of the simple example agent configuration."""
        config_path = self.config_dir / "example_agent_config.json"
        
        try:
            config, warnings = validate_configuration_file(config_path)
            
            # This should default to Agent class since it's not specified
            self.assertEqual(config.name, "MyAwesomeAgent")
            self.assertEqual(config.model, "openai:gpt-4o")
            self.assertIsNotNone(config.instruction)
            
            # Verify tools (should be string references)
            self.assertTrue(hasattr(config, 'tools'))
            self.assertGreater(len(config.tools), 0)
            
            print(f"✓ Example agent config validation passed with {len(warnings)} warnings")
            for warning in warnings:
                print(f"  Warning: {warning}")
                
        except ValidationError as e:
            self.fail(f"Example agent config validation failed: {e}")
    
    def test_validate_all_configs(self):
        """Test validation of all available configuration files."""
        valid_configs = 0
        total_warnings = 0
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                config, warnings = validate_configuration_file(config_file)
                valid_configs += 1
                total_warnings += len(warnings)
                print(f"✓ {config_file.name}: Valid ({len(warnings)} warnings)")
            except Exception as e:
                print(f"✗ {config_file.name}: Invalid - {e}")
        
        print(f"\nValidation Summary:")
        print(f"  Valid configs: {valid_configs}")
        print(f"  Total warnings: {total_warnings}")
        
        # At least some configs should be valid
        self.assertGreater(valid_configs, 0)
    
    def test_invalid_config_validation(self):
        """Test that invalid configurations are properly rejected."""
        
        # Test missing required fields
        invalid_config = {
            "class": "Agent",
            "module": "google.adk.agents"
            # Missing 'name' field
        }
        
        with self.assertRaises(ValidationError):
            validate_configuration_dict(invalid_config)
        
        # Test invalid agent class
        invalid_config = {
            "name": "TestAgent",
            "class": "InvalidAgentClass",
            "module": "google.adk.agents"
        }
        
        with self.assertRaises((ValidationError, ValueError)):
            validate_configuration_dict(invalid_config)
        
        # Test invalid max_iterations for non-loop agent
        invalid_config = {
            "name": "TestAgent",
            "class": "SequentialAgent", 
            "module": "google.adk.agents",
            "max_iterations": 5  # Invalid for SequentialAgent
        }
        
        with self.assertRaises(ValidationError):
            validate_configuration_dict(invalid_config)
    
    def test_tool_config_validation(self):
        """Test validation of tool configurations."""
        
        # Valid function tool
        valid_function_tool = {
            "class": "FunctionTool",
            "module": "google.adk.tools",
            "function_name": "test_function",
            "function_module": "test.module"
        }
        
        from data_model.agent_config_models import ToolConfig
        tool_config = ToolConfig(**valid_function_tool)
        self.assertEqual(tool_config.class_, "FunctionTool")
        
        # Invalid function tool (missing function_name)
        invalid_function_tool = {
            "class": "FunctionTool",
            "module": "google.adk.tools",
            "function_module": "test.module"
            # Missing function_name
        }
        
        with self.assertRaises(ValidationError):
            ToolConfig(**invalid_function_tool)
    
    def test_hierarchy_validation(self):
        """Test validation of agent hierarchies."""
        
        # Create a deeply nested configuration to test warnings
        deep_config = {
            "name": "Level1",
            "class": "SequentialAgent",
            "module": "google.adk.agents",
            "sub_agents": [
                {
                    "name": "Level2",
                    "class": "SequentialAgent",
                    "module": "google.adk.agents",
                    "sub_agents": [
                        {
                            "name": "Level3",
                            "class": "SequentialAgent", 
                            "module": "google.adk.agents",
                            "sub_agents": [
                                {
                                    "name": "Level4",
                                    "class": "SequentialAgent",
                                    "module": "google.adk.agents",
                                    "sub_agents": [
                                        {
                                            "name": "Level5",
                                            "class": "SequentialAgent",
                                            "module": "google.adk.agents",
                                            "sub_agents": [
                                                {
                                                    "name": "Level6",
                                                    "class": "Agent",
                                                    "module": "google.adk.agents",
                                                    "model": "test-model"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        config, warnings = validate_configuration_dict(deep_config)
        
        # Should generate a warning about deep nesting
        deep_nesting_warnings = [w for w in warnings if "Deep nesting" in w]
        self.assertGreater(len(deep_nesting_warnings), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)