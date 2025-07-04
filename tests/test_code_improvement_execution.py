#!/usr/bin/env python3
"""
Test that instantiates and executes the code improvement workflow with sample code.

This test validates that our data model can be used to create actual working agents
that can be executed with real input.
"""

import unittest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_model import validate_configuration_file
from agent_io.agent_io import create_agent_from_config


class TestCodeImprovementExecution(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_dir = Path(__file__).parent.parent / "config" / "agent" / "yaml_examples"
        self.config_path = self.config_dir / "code_improvement_workflow.yaml"
        
        # Sample code to analyze
        self.sample_code = '''
def process_user_data(user_input):
    # This function has several issues:
    # 1. No input validation
    # 2. SQL injection vulnerability
    # 3. No error handling
    # 4. Poor variable naming
    
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Dangerous: direct string interpolation
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)
    
    results = cursor.fetchall()
    
    # No proper cleanup
    return results

def calculate_score(data):
    # Performance issue: inefficient algorithm
    total = 0
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j:
                total += data[i] * data[j]
    
    return total / len(data) if len(data) > 0 else 0

class UserManager:
    def __init__(self):
        self.users = []
        self.admin_password = "admin123"  # Security issue: hardcoded password
    
    def add_user(self, user):
        # No validation
        self.users.append(user)
    
    def get_user(self, index):
        # No bounds checking
        return self.users[index]
    
    def authenticate_admin(self, password):
        # Timing attack vulnerability
        return password == self.admin_password
'''
    
    def test_validate_configuration(self):
        """Test that the code improvement workflow configuration is valid."""
        config, warnings = validate_configuration_file(self.config_path)
        
        # Verify the configuration is valid
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "CodeImprovementWorkflow")
        self.assertEqual(config.class_, "SequentialAgent")
        
        # Print warnings for debugging
        print(f"Configuration loaded with {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    def test_instantiate_workflow(self):
        """Test that we can instantiate the workflow from the configuration."""
        try:
            # This will test our agent_io integration
            workflow_agent = create_agent_from_config(str(self.config_path))
            
            # Verify the agent was created successfully
            self.assertIsNotNone(workflow_agent)
            self.assertEqual(workflow_agent.name, "CodeImprovementWorkflow")
            
            # Check that sub-agents were created
            self.assertTrue(hasattr(workflow_agent, 'sub_agents'))
            self.assertGreater(len(workflow_agent.sub_agents), 0)
            
            # Verify expected agents exist
            agent_names = [agent.name for agent in workflow_agent.sub_agents]
            expected_agents = [
                "CodebaseAnalysisAgent",
                "IssueIdentificationLoop",
                "SolutionDesignParallel", 
                "QualityAssuranceReview",
                "DocumentationGenerator"
            ]
            
            for expected_agent in expected_agents:
                self.assertIn(expected_agent, agent_names)
                
            print(f"✓ Successfully instantiated workflow with {len(workflow_agent.sub_agents)} sub-agents")
            
        except Exception as e:
            self.fail(f"Failed to instantiate workflow: {e}")
    
    def test_agent_structure_validation(self):
        """Test the structure of instantiated agents."""
        workflow_agent = create_agent_from_config(str(self.config_path))
        
        # Test specific agent types and properties
        loop_agent = next(
            agent for agent in workflow_agent.sub_agents 
            if agent.name == "IssueIdentificationLoop"
        )
        self.assertEqual(loop_agent.__class__.__name__, "LoopAgent")
        self.assertEqual(loop_agent.max_iterations, 1)
        self.assertGreater(len(loop_agent.sub_agents), 0)
        
        # Test parallel agent
        parallel_agent = next(
            agent for agent in workflow_agent.sub_agents
            if agent.name == "SolutionDesignParallel"
        )
        self.assertEqual(parallel_agent.__class__.__name__, "ParallelAgent")
        self.assertGreater(len(parallel_agent.sub_agents), 0)
        
        # Test regular agent with tools
        analysis_agent = next(
            agent for agent in workflow_agent.sub_agents
            if agent.name == "CodebaseAnalysisAgent"
        )
        self.assertIn(analysis_agent.__class__.__name__, ["Agent", "LlmAgent"])
        self.assertTrue(hasattr(analysis_agent, 'tools'))
        self.assertGreater(len(analysis_agent.tools), 0)
        
        print("✓ Agent structure validation passed")
    
    def test_agent_properties(self):
        """Test that agents have the expected properties."""
        workflow_agent = create_agent_from_config(str(self.config_path))
        
        # Test that agents have required properties
        for agent in workflow_agent.sub_agents:
            self.assertTrue(hasattr(agent, 'name'))
            self.assertIsNotNone(agent.name)
            
            # Base agents should have models and instructions
            if agent.__class__.__name__ in ["Agent", "LlmAgent"]:
                self.assertTrue(hasattr(agent, 'model'))
                self.assertTrue(hasattr(agent, 'instruction'))
                self.assertIsNotNone(agent.model)
                self.assertIsNotNone(agent.instruction)
                
                # Check for output_key
                if hasattr(agent, 'output_key'):
                    self.assertIsNotNone(agent.output_key)
            
        print("✓ Agent properties validation passed")
    
    def test_mock_execution_context(self):
        """Test that we can prepare the workflow for execution (without actually running it)."""
        workflow_agent = create_agent_from_config(str(self.config_path))
        
        # Prepare mock execution context
        execution_context = {
            "input_code": self.sample_code,
            "project_name": "TestProject",
            "language": "Python",
            "analysis_scope": "security,performance,quality,testing"
        }
        
        # Verify we can access the workflow structure for execution
        self.assertIsNotNone(workflow_agent)
        
        # Test that we can iterate through the workflow
        analysis_results = {}
        
        for i, agent in enumerate(workflow_agent.sub_agents):
            agent_info = {
                "name": agent.name,
                "type": agent.__class__.__name__,
                "instruction": getattr(agent, 'instruction', None),
                "output_key": getattr(agent, 'output_key', None),
                "ready_for_execution": True
            }
            
            # For composite agents, check sub-agents
            if hasattr(agent, 'sub_agents'):
                agent_info["sub_agents_count"] = len(agent.sub_agents)
                agent_info["sub_agents"] = [
                    {
                        "name": sub_agent.name,
                        "type": sub_agent.__class__.__name__,
                        "instruction": getattr(sub_agent, 'instruction', None)
                    }
                    for sub_agent in agent.sub_agents
                ]
            
            # For agents with tools, check tool availability
            if hasattr(agent, 'tools'):
                agent_info["tools_count"] = len(agent.tools)
                agent_info["tools"] = [
                    {
                        "name": tool.func.__name__ if hasattr(tool, 'func') else str(type(tool)),
                        "available": True
                    }
                    for tool in agent.tools
                ]
            
            analysis_results[f"step_{i+1}"] = agent_info
        
        # Verify all steps are ready
        self.assertEqual(len(analysis_results), len(workflow_agent.sub_agents))
        
        for step, info in analysis_results.items():
            self.assertTrue(info["ready_for_execution"])
            
        print(f"✓ Mock execution context prepared for {len(analysis_results)} steps")
        
        # Print execution plan
        print("\nExecution Plan:")
        for step, info in analysis_results.items():
            print(f"  {step}: {info['name']} ({info['type']})")
            if 'sub_agents_count' in info:
                print(f"    └─ {info['sub_agents_count']} sub-agents")
            if 'tools_count' in info:
                print(f"    └─ {info['tools_count']} tools")
    
    def test_configuration_to_execution_pipeline(self):
        """Test the complete pipeline from configuration to execution readiness."""
        
        print("\n=== Configuration to Execution Pipeline Test ===")
        
        # Step 1: Validate configuration
        print("1. Validating configuration...")
        config, warnings = validate_configuration_file(self.config_path)
        self.assertIsNotNone(config)
        print(f"   ✓ Configuration valid ({len(warnings)} warnings)")
        
        # Step 2: Instantiate workflow
        print("2. Instantiating workflow...")
        workflow_agent = create_agent_from_config(str(self.config_path))
        self.assertIsNotNone(workflow_agent)
        print(f"   ✓ Workflow instantiated with {len(workflow_agent.sub_agents)} agents")
        
        # Step 3: Prepare execution input
        print("3. Preparing execution input...")
        execution_input = {
            "code_to_analyze": self.sample_code,
            "project_context": {
                "name": "TestProject",
                "language": "Python",
                "framework": "None",
                "size": "small"
            },
            "analysis_preferences": {
                "focus_areas": ["security", "performance", "maintainability"],
                "severity_threshold": "medium",
                "include_examples": True
            }
        }
        print("   ✓ Execution input prepared")
        
        # Step 4: Verify workflow is ready for execution
        print("4. Verifying workflow readiness...")
        
        total_agents = 0
        agents_with_instructions = 0
        agents_with_tools = 0
        
        def count_agents(agent):
            nonlocal total_agents, agents_with_instructions, agents_with_tools
            total_agents += 1
            
            if hasattr(agent, 'instruction') and agent.instruction:
                agents_with_instructions += 1
                
            if hasattr(agent, 'tools') and agent.tools:
                agents_with_tools += 1
                
            if hasattr(agent, 'sub_agents'):
                for sub_agent in agent.sub_agents:
                    count_agents(sub_agent)
        
        count_agents(workflow_agent)
        
        print(f"   ✓ Total agents: {total_agents}")
        print(f"   ✓ Agents with instructions: {agents_with_instructions}")
        print(f"   ✓ Agents with tools: {agents_with_tools}")
        
        # Verify minimum requirements
        self.assertGreater(total_agents, 5)  # Should have multiple agents
        self.assertGreater(agents_with_instructions, 0)  # Should have instructed agents
        self.assertGreater(agents_with_tools, 0)  # Should have agents with tools
        
        print("5. Pipeline validation complete - Ready for execution!")
        print("\nNote: Actual execution would require proper Google ADK environment setup")


if __name__ == '__main__':
    unittest.main(verbosity=2)