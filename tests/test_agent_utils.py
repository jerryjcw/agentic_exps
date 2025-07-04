#!/usr/bin/env python3
"""
Test suite for agent_utils functions.

Tests for collect_agent_execution_steps and display_execution_steps_summary functions.
"""

import unittest
import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.agent_utils import (
    ExecutionStep, 
    collect_agent_execution_steps, 
    display_execution_steps_summary
)


def create_mock_agent_class(class_name):
    """Factory function to create mock agent classes with specific names."""
    class MockAgentBase:
        def __init__(self, name, sub_agents=None):
            self.name = name
            self.sub_agents = sub_agents or []
    
    MockAgentBase.__name__ = class_name
    return MockAgentBase


class MockAgent:
    """Mock agent class for testing."""
    
    def __init__(self, name, agent_type="MockAgent", sub_agents=None):
        self.name = name
        self.sub_agents = sub_agents or []
        # Create a dynamic class with the correct name
        self.__class__ = create_mock_agent_class(agent_type)


class TestExecutionStep(unittest.TestCase):
    """Test cases for ExecutionStep dataclass."""
    
    def test_execution_step_creation(self):
        """Test basic ExecutionStep creation."""
        step = ExecutionStep(
            step_id="step_001",
            agent_name="TestAgent",
            agent_type="MockAgent",
            description="Test description"
        )
        
        self.assertEqual(step.step_id, "step_001")
        self.assertEqual(step.agent_name, "TestAgent")
        self.assertEqual(step.agent_type, "MockAgent")
        self.assertEqual(step.description, "Test description")
        self.assertEqual(step.status, "pending")
        self.assertIsNone(step.start_time)
        self.assertIsNone(step.end_time)
        self.assertEqual(step.events_generated, 0)
        self.assertEqual(step.output_preview, "")
    
    def test_execution_step_with_optional_fields(self):
        """Test ExecutionStep with all fields."""
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=10)
        
        step = ExecutionStep(
            step_id="step_002",
            agent_name="TestAgent2",
            agent_type="ComplexAgent",
            description="Complex test",
            status="completed",
            start_time=start_time,
            end_time=end_time,
            events_generated=5,
            output_preview="Test output"
        )
        
        self.assertEqual(step.status, "completed")
        self.assertEqual(step.start_time, start_time)
        self.assertEqual(step.end_time, end_time)
        self.assertEqual(step.events_generated, 5)
        self.assertEqual(step.output_preview, "Test output")


class TestCollectAgentExecutionSteps(unittest.TestCase):
    """Test cases for collect_agent_execution_steps function."""
    
    def test_single_agent_no_sub_agents(self):
        """Test collection with a single agent with no sub-agents."""
        agent = MockAgent("MainAgent", "TestAgent")
        
        steps = collect_agent_execution_steps(agent)
        
        self.assertEqual(len(steps), 1)
        self.assertIn("MainAgent", steps)
        step = steps["MainAgent"]
        self.assertEqual(step.step_id, "step_001")
        self.assertEqual(step.agent_name, "MainAgent")
        self.assertEqual(step.agent_type, "TestAgent")
        self.assertIn("Main Agent", step.description)
        self.assertEqual(step.status, "pending")
    
    def test_agent_with_single_sub_agent(self):
        """Test collection with agent containing one sub-agent."""
        sub_agent = MockAgent("SubAgent1", "SubAgentType")
        main_agent = MockAgent("MainAgent", "MainAgentType", [sub_agent])
        
        steps = collect_agent_execution_steps(main_agent)
        
        self.assertEqual(len(steps), 2)
        
        # Check main agent
        self.assertIn("MainAgent", steps)
        main_step = steps["MainAgent"]
        self.assertEqual(main_step.step_id, "step_001")
        self.assertEqual(main_step.agent_name, "MainAgent")
        self.assertIn("Main Agent", main_step.description)
        
        # Check sub-agent
        self.assertIn("SubAgent1", steps)
        sub_step = steps["SubAgent1"]
        self.assertEqual(sub_step.step_id, "step_002")
        self.assertEqual(sub_step.agent_name, "SubAgent1")
        self.assertIn("Sub-agent", sub_step.description)
        self.assertIn("under MainAgent", sub_step.description)
    
    def test_agent_with_multiple_sub_agents(self):
        """Test collection with agent containing multiple sub-agents."""
        sub_agent1 = MockAgent("SubAgent1", "SubType1")
        sub_agent2 = MockAgent("SubAgent2", "SubType2")
        sub_agent3 = MockAgent("SubAgent3", "SubType3")
        main_agent = MockAgent("MainAgent", "MainType", [sub_agent1, sub_agent2, sub_agent3])
        
        steps = collect_agent_execution_steps(main_agent)
        
        self.assertEqual(len(steps), 4)
        
        # Verify all agents are collected
        agent_names = list(steps.keys())
        self.assertIn("MainAgent", agent_names)
        self.assertIn("SubAgent1", agent_names)
        self.assertIn("SubAgent2", agent_names)
        self.assertIn("SubAgent3", agent_names)
        
        # Verify step IDs are sequential (check specific steps)
        self.assertEqual(steps["MainAgent"].step_id, "step_001")
        self.assertEqual(steps["SubAgent1"].step_id, "step_002")
        self.assertEqual(steps["SubAgent2"].step_id, "step_003")
        self.assertEqual(steps["SubAgent3"].step_id, "step_004")
    
    def test_nested_agents_depth_2(self):
        """Test collection with nested agents (depth 2)."""
        nested_agent = MockAgent("NestedAgent", "NestedType")
        sub_agent = MockAgent("SubAgent", "SubType", [nested_agent])
        main_agent = MockAgent("MainAgent", "MainType", [sub_agent])
        
        steps = collect_agent_execution_steps(main_agent)
        
        self.assertEqual(len(steps), 3)
        
        # Check descriptions reflect nesting
        descriptions = [step.description for step in steps.values()]
        self.assertTrue(any("Main Agent" in desc for desc in descriptions))
        self.assertTrue(any("Sub-agent" in desc and "under MainAgent" in desc for desc in descriptions))
        self.assertTrue(any("Nested (depth 2)" in desc and "under SubAgent" in desc for desc in descriptions))
    
    def test_nested_agents_depth_3(self):
        """Test collection with deeper nesting (depth 3)."""
        deep_nested = MockAgent("DeepNested", "DeepType")
        nested_agent = MockAgent("NestedAgent", "NestedType", [deep_nested])
        sub_agent = MockAgent("SubAgent", "SubType", [nested_agent])
        main_agent = MockAgent("MainAgent", "MainType", [sub_agent])
        
        steps = collect_agent_execution_steps(main_agent)
        
        self.assertEqual(len(steps), 4)
        
        # Verify the deepest nested agent has correct description
        self.assertIn("DeepNested", steps)
        deep_step = steps["DeepNested"]
        self.assertIn("Nested (depth 3)", deep_step.description)
        self.assertIn("under NestedAgent", deep_step.description)
    
    def test_custom_step_id_prefix(self):
        """Test collection with custom step ID prefix."""
        agent = MockAgent("TestAgent")
        
        steps = collect_agent_execution_steps(agent, step_id_prefix="custom")
        
        self.assertEqual(len(steps), 1)
        self.assertIn("TestAgent", steps)
        self.assertEqual(steps["TestAgent"].step_id, "custom_001")
    
    def test_agent_without_name_attribute(self):
        """Test collection with agent missing name attribute."""
        class NoNameAgent:
            def __init__(self):
                self.sub_agents = []
        
        agent = NoNameAgent()
        
        steps = collect_agent_execution_steps(agent)
        
        self.assertEqual(len(steps), 1)
        self.assertIn("Unknown Agent", steps)
        self.assertEqual(steps["Unknown Agent"].agent_name, "Unknown Agent")
    
    def test_circular_reference_prevention(self):
        """Test that circular references are handled properly."""
        agent1 = MockAgent("Agent1", "Type1")
        agent2 = MockAgent("Agent2", "Type2")
        
        # Create circular reference
        agent1.sub_agents = [agent2]
        agent2.sub_agents = [agent1]
        
        steps = collect_agent_execution_steps(agent1)
        
        # Should only collect each agent once despite circular reference
        self.assertEqual(len(steps), 2)
        agent_names = list(steps.keys())
        self.assertEqual(set(agent_names), {"Agent1", "Agent2"})
    
    def test_complex_hierarchy(self):
        """Test collection with complex agent hierarchy."""
        # Create a complex hierarchy
        leaf1 = MockAgent("Leaf1", "LeafType")
        leaf2 = MockAgent("Leaf2", "LeafType")
        leaf3 = MockAgent("Leaf3", "LeafType")
        
        branch1 = MockAgent("Branch1", "BranchType", [leaf1, leaf2])
        branch2 = MockAgent("Branch2", "BranchType", [leaf3])
        
        root = MockAgent("Root", "RootType", [branch1, branch2])
        
        steps = collect_agent_execution_steps(root)
        
        # Should have 6 agents total
        self.assertEqual(len(steps), 6)
        
        # Verify all agents are present
        agent_names = list(steps.keys())
        expected_names = {"Root", "Branch1", "Branch2", "Leaf1", "Leaf2", "Leaf3"}
        self.assertEqual(set(agent_names), expected_names)
        
        # Verify Root has main agent description
        self.assertIn("Root", steps)
        self.assertIn("Main Agent", steps["Root"].description)


class TestDisplayExecutionStepsSummary(unittest.TestCase):
    """Test cases for display_execution_steps_summary function."""
    
    @patch('builtins.print')
    def test_display_empty_list(self, mock_print):
        """Test display with empty execution steps list."""
        display_execution_steps_summary([])
        
        # Verify print was called
        self.assertTrue(mock_print.called)
        
        # Check that it shows 0 total steps
        print_calls = [str(call) for call in mock_print.call_args_list]
        total_steps_line = next(call for call in print_calls if "Total Steps: 0" in call)
        self.assertIsNotNone(total_steps_line)
    
    @patch('builtins.print')
    def test_display_single_step(self, mock_print):
        """Test display with single execution step."""
        step = ExecutionStep(
            step_id="step_001",
            agent_name="TestAgent",
            agent_type="TestType",
            description="Test description",
            status="pending"
        )
        
        display_execution_steps_summary({"TestAgent": step})
        
        # Verify key information is displayed
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Check total steps
        self.assertTrue(any("Total Steps: 1" in call for call in print_calls))
        
        # Check agent information
        self.assertTrue(any("step_001: TestAgent" in call for call in print_calls))
        self.assertTrue(any("Type: TestType" in call for call in print_calls))
        self.assertTrue(any("Status: pending" in call for call in print_calls))
    
    @patch('builtins.print')
    def test_display_multiple_steps(self, mock_print):
        """Test display with multiple execution steps."""
        steps = {
            "Agent1": ExecutionStep(
                step_id="step_001",
                agent_name="Agent1",
                agent_type="Type1",
                description="Description 1",
                status="completed"
            ),
            "Agent2": ExecutionStep(
                step_id="step_002",
                agent_name="Agent2",
                agent_type="Type2",
                description="Description 2",
                status="running"
            )
        }
        
        display_execution_steps_summary(steps)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Check total steps
        self.assertTrue(any("Total Steps: 2" in call for call in print_calls))
        
        # Check both agents are displayed
        self.assertTrue(any("Agent1" in call for call in print_calls))
        self.assertTrue(any("Agent2" in call for call in print_calls))
        self.assertTrue(any("completed" in call for call in print_calls))
        self.assertTrue(any("running" in call for call in print_calls))


class TestIntegration(unittest.TestCase):
    """Integration tests combining both functions."""
    
    @patch('builtins.print')
    def test_collect_and_display_integration(self, mock_print):
        """Test collecting steps and displaying them."""
        # Create a simple agent hierarchy
        sub_agent = MockAgent("SubAgent", "SubType")
        main_agent = MockAgent("MainAgent", "MainType", [sub_agent])
        
        # Collect steps
        steps = collect_agent_execution_steps(main_agent)
        
        # Display steps
        display_execution_steps_summary(steps)
        
        # Verify we have 2 steps
        self.assertEqual(len(steps), 2)
        
        # Verify display was called
        self.assertTrue(mock_print.called)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_agent_with_empty_sub_agents_list(self):
        """Test agent with empty sub_agents list."""
        agent = MockAgent("TestAgent", "TestType", [])
        
        steps = collect_agent_execution_steps(agent)
        
        self.assertEqual(len(steps), 1)
        self.assertIn("TestAgent", steps)
        self.assertEqual(steps["TestAgent"].agent_name, "TestAgent")
    
    def test_agent_with_none_sub_agents(self):
        """Test agent with None sub_agents."""
        agent = MockAgent("TestAgent", "TestType", None)
        
        steps = collect_agent_execution_steps(agent)
        
        self.assertEqual(len(steps), 1)
        self.assertIn("TestAgent", steps)
        self.assertEqual(steps["TestAgent"].agent_name, "TestAgent")
    
    def test_agent_without_sub_agents_attribute(self):
        """Test agent without sub_agents attribute."""
        class MinimalAgent:
            def __init__(self, name):
                self.name = name
        
        agent = MinimalAgent("MinimalAgent")
        
        steps = collect_agent_execution_steps(agent)
        
        self.assertEqual(len(steps), 1)
        self.assertIn("MinimalAgent", steps)
        self.assertEqual(steps["MinimalAgent"].agent_name, "MinimalAgent")

    def test_e2e(self):
        # find out work directory
        from pathlib import Path
        from agent_io.agent_io import create_agent_from_config
        from utils.agent_utils import collect_agent_execution_steps 

        work_dir = os.path.dirname(os.path.abspath(__file__))
        # For each configuration file in {work_dir}/../config/agent/json_examples
        # 1. Load the configuration file.
        config_files = Path(work_dir).parent / "config/agent/yaml_examples"
        for config_file in config_files.glob("*.yaml"):
            # 2. Create the agent using the configuration and create_agent_from_config() in agent_io/agent_io.py
            agent = create_agent_from_config(config_file)

            # 3. Create execution steps using collect_agent_execution_steps, given the agent.
            steps = collect_agent_execution_steps(agent)

            # 4. Read the file and compute the number of Agents in the config.
            import yaml
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Count agents recursively in YAML structure
            def count_agents(obj):
                if isinstance(obj, dict):
                    count = 1 if 'name' in obj else 0
                    if 'sub_agents' in obj:
                        for sub_agent in obj['sub_agents']:
                            count += count_agents(sub_agent)
                    return count
                return 0
            
            num_agents = count_agents(config_data)
            assert len(steps) == num_agents, f"Expected {num_agents} steps, but got {len(steps)} for {config_file}"


if __name__ == '__main__':
    unittest.main()