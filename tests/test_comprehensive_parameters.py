#!/usr/bin/env python3
"""
Comprehensive test for all agent parameters in the strengthened agent_io module.

This test verifies that all required parameters are properly handled:
- name, model, instruction, description, output_key, tools, sub_agents, max_iteration
"""

import unittest
import os
import json
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent
from tools.gadk.tools import get_current_time, get_temperature, google_search
from google.adk.tools import FunctionTool

from agent_io.agent_io import (
    save_agent_to_config, 
    create_agent_from_config,
    create_comprehensive_agent_config
)

class TestComprehensiveAgentParameters(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for config files."""
        self.temp_dir = "temp_comprehensive_test"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.config_path = os.path.join(self.temp_dir, "comprehensive_agent_config.json")

    def tearDown(self):
        """Clean up the temporary directory and files."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_agent_with_all_parameters(self):
        """Test Agent with all supported parameters."""
        # Create agent with all parameters
        original_agent = Agent(
            name="ComprehensiveAgent",
            model="gpt-4o",
            instruction="You are a comprehensive test agent with all parameters.",
            description="A test agent that includes all possible parameters.",
            output_key="test_output",
            tools=[
                FunctionTool(get_current_time), 
                FunctionTool(get_temperature),
                FunctionTool(google_search)
            ]
        )
        
        # Save and load
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)
        
        # Verify all parameters are preserved
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(original_agent.model, loaded_agent.model.model)
        self.assertEqual(original_agent.instruction, loaded_agent.instruction)
        self.assertEqual(getattr(original_agent, 'description', None), getattr(loaded_agent, 'description', None))
        self.assertEqual(getattr(original_agent, 'output_key', None), getattr(loaded_agent, 'output_key', None))
        self.assertEqual(len(original_agent.tools), len(loaded_agent.tools))
        
        # Verify the config file contains all parameters
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        expected_keys = ['name', 'model', 'instruction', 'description', 'output_key', 'tools', 'class', 'module']
        for key in expected_keys:
            if key == 'description' or key == 'output_key':
                # These might not be in config if they're None
                continue
            self.assertIn(key, config, f"Missing key: {key}")

    def test_loop_agent_with_max_iterations(self):
        """Test LoopAgent with max_iterations parameter."""
        sub_agent = Agent(
            name="LoopSubAgent",
            model="loop-model",
            instruction="This agent will be looped.",
            output_key="loop_result"
        )
        
        original_agent = LoopAgent(
            name="TestLoopAgent", 
            description="A loop agent with max_iterations.",
            sub_agents=[sub_agent],
            max_iterations=5
        )
        
        # Save and load
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)
        
        # Verify parameters
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(original_agent.max_iterations, loaded_agent.max_iterations)
        self.assertEqual(getattr(original_agent, 'description', None), getattr(loaded_agent, 'description', None))
        self.assertEqual(len(original_agent.sub_agents), len(loaded_agent.sub_agents))
        self.assertEqual(original_agent.sub_agents[0].name, loaded_agent.sub_agents[0].name)

    def test_sequential_agent_with_output_key(self):
        """Test SequentialAgent with sub-agents that have output_key."""
        sub_agent1 = Agent(
            name="SeqStep1",
            model="seq-model-1", 
            instruction="First step with output.",
            output_key="step1_output"
        )
        
        sub_agent2 = Agent(
            name="SeqStep2",
            model="seq-model-2",
            instruction="Second step with output.",
            output_key="step2_output"
        )
        
        original_agent = SequentialAgent(
            name="TestSequentialAgent",
            description="A sequential agent with sub-agents that have output keys.",
            sub_agents=[sub_agent1, sub_agent2]
        )
        
        # Save and load
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)
        
        # Verify parameters
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(getattr(original_agent, 'description', None), getattr(loaded_agent, 'description', None))
        self.assertEqual(len(original_agent.sub_agents), len(loaded_agent.sub_agents))
        
        # Verify sub-agent output keys
        self.assertEqual(getattr(original_agent.sub_agents[0], 'output_key', None), 
                        getattr(loaded_agent.sub_agents[0], 'output_key', None))
        self.assertEqual(getattr(original_agent.sub_agents[1], 'output_key', None),
                        getattr(loaded_agent.sub_agents[1], 'output_key', None))

    def test_parallel_agent_with_description(self):
        """Test ParallelAgent with description parameter."""
        sub_agent1 = Agent(
            name="ParallelTask1",
            model="parallel-model-1",
            instruction="First parallel task.",
            description="Task 1 description"
        )
        
        sub_agent2 = Agent(
            name="ParallelTask2", 
            model="parallel-model-2",
            instruction="Second parallel task.",
            description="Task 2 description"
        )
        
        original_agent = ParallelAgent(
            name="TestParallelAgent",
            description="A parallel agent with detailed descriptions.",
            sub_agents=[sub_agent1, sub_agent2]
        )
        
        # Save and load
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)
        
        # Verify parameters
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(getattr(original_agent, 'description', None), getattr(loaded_agent, 'description', None))
        self.assertEqual(len(original_agent.sub_agents), len(loaded_agent.sub_agents))
        
        # Verify sub-agent descriptions
        self.assertEqual(getattr(original_agent.sub_agents[0], 'description', None),
                        getattr(loaded_agent.sub_agents[0], 'description', None))
        self.assertEqual(getattr(original_agent.sub_agents[1], 'description', None),
                        getattr(loaded_agent.sub_agents[1], 'description', None))

    def test_comprehensive_config_creation(self):
        """Test the create_comprehensive_agent_config function."""
        basic_config = {
            "name": "BasicAgent",
            "model": "test-model"
        }
        
        comprehensive_config = create_comprehensive_agent_config(basic_config)
        
        # Verify all expected keys are present
        expected_keys = [
            'name', 'model', 'instruction', 'description', 'output_key', 
            'tools', 'sub_agents', 'max_iterations', 'class', 'module'
        ]
        
        for key in expected_keys:
            self.assertIn(key, comprehensive_config)
        
        # Verify provided values are preserved
        self.assertEqual(comprehensive_config['name'], 'BasicAgent')
        self.assertEqual(comprehensive_config['model'], 'test-model')
        
        # Verify defaults are set
        self.assertEqual(comprehensive_config['tools'], [])
        self.assertEqual(comprehensive_config['sub_agents'], [])
        self.assertIsNone(comprehensive_config['instruction'])

    def test_financial_tools_integration(self):
        """Test that financial tools can be serialized and deserialized."""
        try:
            from tools.gadk.financial_tools import get_earnings_report, get_company_news
            
            original_agent = Agent(
                name="FinancialAgent",
                model="financial-model",
                instruction="You are a financial analysis agent.",
                description="Agent with financial tools",
                tools=[
                    FunctionTool(get_earnings_report),
                    FunctionTool(get_company_news),
                    FunctionTool(get_current_time)
                ]
            )
            
            # Save and load
            save_agent_to_config(original_agent, self.config_path)
            loaded_agent = create_agent_from_config(self.config_path)
            
            # Verify tools are preserved
            self.assertEqual(len(original_agent.tools), len(loaded_agent.tools))
            
            tool_names = [tool.func.__name__ for tool in loaded_agent.tools]
            self.assertIn('get_earnings_report', tool_names)
            self.assertIn('get_company_news', tool_names)
            self.assertIn('get_current_time', tool_names)
            
        except ImportError:
            self.skipTest("Financial tools not available")

    def test_nested_agents_with_all_parameters(self):
        """Test deeply nested agents with all parameters."""
        # Inner agent with all parameters
        inner_agent = Agent(
            name="InnerAgent",
            model="inner-model",
            instruction="Inner agent instruction.",
            description="Inner agent description",
            output_key="inner_output",
            tools=[FunctionTool(get_current_time)]
        )
        
        # Loop agent with inner agent
        loop_agent = LoopAgent(
            name="NestedLoopAgent",
            description="Loop agent with nested inner agent",
            sub_agents=[inner_agent],
            max_iterations=3
        )
        
        # Sequential agent containing the loop
        sequential_agent = SequentialAgent(
            name="MainSequentialAgent",
            description="Main sequential workflow",
            sub_agents=[loop_agent]
        )
        
        # Save and load
        save_agent_to_config(sequential_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)
        
        # Verify nested structure and parameters
        self.assertIsInstance(loaded_agent, SequentialAgent)
        self.assertEqual(loaded_agent.name, "MainSequentialAgent")
        self.assertEqual(getattr(loaded_agent, 'description', None), "Main sequential workflow")
        
        # Verify nested loop agent
        nested_loop = loaded_agent.sub_agents[0]
        self.assertIsInstance(nested_loop, LoopAgent)
        self.assertEqual(nested_loop.name, "NestedLoopAgent")
        self.assertEqual(nested_loop.max_iterations, 3)
        
        # Verify inner agent
        inner = nested_loop.sub_agents[0]
        self.assertIsInstance(inner, Agent)
        self.assertEqual(inner.name, "InnerAgent")
        self.assertEqual(inner.model.model, "inner-model")
        self.assertEqual(getattr(inner, 'output_key', None), "inner_output")
        self.assertEqual(len(inner.tools), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)