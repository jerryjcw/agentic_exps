
import unittest
import os
import json
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent, BaseAgent
from tools.gadk.tools import get_current_time, get_temperature
from google.adk.tools import FunctionTool

from agent_io.agent_io import save_agent_to_config, create_agent_from_config

# A custom agent for testing purposes
class MyCustomAgent(BaseAgent):
    def __init__(self, name: str, custom_property: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.custom_property = custom_property

    def __call__(self, session, query):
        pass # Not needed for this test

class TestAgentIO(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for config files."""
        self.temp_dir = "temp_test_configs"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.config_path = os.path.join(self.temp_dir, "agent_config.json")

    def tearDown(self):
        """Clean up the temporary directory and files."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)

    def test_save_and_load_simple_agent(self):
        """Test saving and loading a simple Agent."""
        original_agent = Agent(
            name="TestAgent",
            model="test_model",
            instruction="This is a test agent.",
            tools=[FunctionTool(get_current_time)]
        )
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, Agent)
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(original_agent.model, loaded_agent.model)
        self.assertEqual(original_agent.instruction, loaded_agent.instruction)
        self.assertEqual(len(original_agent.tools), len(loaded_agent.tools))
        self.assertEqual(original_agent.tools[0].name, loaded_agent.tools[0].name)

    def test_save_and_load_sequential_agent(self):
        """Test saving and loading a SequentialAgent."""
        sub_agent1 = Agent(name="FirstStep", model="sequential-model-1", instruction="First step in the sequence.")
        sub_agent2 = Agent(name="SecondStep", model="sequential-model-2", instruction="Second step in the sequence.")
        original_agent = SequentialAgent(
            name="TestSequentialAgent",
            sub_agents=[sub_agent1, sub_agent2],
            description="A test sequential agent with two steps."
        )
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, SequentialAgent)
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(original_agent.description, loaded_agent.description)
        self.assertEqual(len(original_agent.sub_agents), len(loaded_agent.sub_agents))
        self.assertEqual(loaded_agent.sub_agents[0].name, "FirstStep")
        self.assertEqual(loaded_agent.sub_agents[0].instruction, "First step in the sequence.")

    def test_save_and_load_parallel_agent(self):
        """Test saving and loading a ParallelAgent."""
        sub_agent1 = Agent(name="ParallelTask1", model="parallel-model-1", instruction="First parallel task.")
        sub_agent2 = Agent(name="ParallelTask2", model="parallel-model-2", instruction="Second parallel task.")
        original_agent = ParallelAgent(
            name="TestParallelAgent",
            sub_agents=[sub_agent1, sub_agent2],
            description="A test parallel agent with two tasks."
        )
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, ParallelAgent)
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(original_agent.description, loaded_agent.description)
        self.assertEqual(len(loaded_agent.sub_agents), 2)
        self.assertEqual(loaded_agent.sub_agents[1].name, "ParallelTask2")
        self.assertEqual(loaded_agent.sub_agents[1].model, "parallel-model-2")

    def test_save_and_load_loop_agent(self):
        """Test saving and loading a LoopAgent."""
        sub_agent = Agent(name="RepeatingAgent", model="loop-model", instruction="This agent will be repeated.")
        original_agent = LoopAgent(
            name="TestLoopAgent",
            sub_agents=[sub_agent],
            description="A test loop agent.",
            max_iterations=7
        )
        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, LoopAgent)
        self.assertEqual(original_agent.name, loaded_agent.name)
        self.assertEqual(loaded_agent.max_iterations, 7)
        self.assertEqual(loaded_agent.sub_agents[0].instruction, "This agent will be repeated.")

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for a non-existent config file."""
        with self.assertRaises(FileNotFoundError):
            create_agent_from_config("non_existent_file.json")

    def test_invalid_class_module(self):
        """Test that ValueError is raised for an invalid class or module."""
        config = {
            "name": "InvalidAgent",
            "class": "NonExistentAgent",
            "module": "non_existent_module"
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)

        with self.assertRaises(ValueError):
            create_agent_from_config(self.config_path)

    def test_save_and_load_nested_mixed_agents(self):
        """Test saving and loading a nested structure of mixed agent types."""
        # Step 2 of the main sequence: a loop agent
        loop_sub_agent1 = Agent(name="LoopSubAgent1", model="loop-sub-model-1", instruction="First step in the loop.")
        loop_sub_agent2 = Agent(name="LoopSubAgent2", model="loop-sub-model-2", instruction="Second step in the loop.")
        loop_agent = LoopAgent(
            name="MyLoopAgent",
            sub_agents=[loop_sub_agent1, loop_sub_agent2],
            description="A loop agent that repeats 2 steps",
            max_iterations=5
        )

        # Main sequential agent
        step1 = Agent(name="Step1", model="main-model-1", instruction="The first step of the main sequence.")
        step3 = Agent(name="Step3", model="main-model-2", instruction="The third step of the main sequence.")
        original_agent = SequentialAgent(
            name="MainSequentialAgent",
            sub_agents=[step1, loop_agent, step3],
            description="A sequential agent with a nested loop"
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, SequentialAgent)
        self.assertEqual(len(loaded_agent.sub_agents), 3)

        # Verify the nested loop agent
        loaded_loop_agent = loaded_agent.sub_agents[1]
        self.assertIsInstance(loaded_loop_agent, LoopAgent)
        self.assertEqual(loaded_loop_agent.name, "MyLoopAgent")
        self.assertEqual(loaded_loop_agent.max_iterations, 5)
        self.assertEqual(len(loaded_loop_agent.sub_agents), 2)
        self.assertEqual(loaded_loop_agent.sub_agents[0].name, "LoopSubAgent1")
        self.assertEqual(loaded_loop_agent.sub_agents[1].instruction, "Second step in the loop.")

    def test_save_and_load_parallel_with_nested_workflow_agents(self):
        """Test a parallel agent with nested loop and sequential agents."""
        # Nested loop agent
        loop_sub = Agent(name="LoopSub", model="model-a", instruction="This agent repeats itself.")
        loop_agent = LoopAgent(
            name="NestedLoop",
            sub_agents=[loop_sub],
            description="A loop inside a parallel workflow.",
            max_iterations=3
        )

        # Nested sequential agent
        seq_sub1 = Agent(name="SeqSub1", model="model-b", instruction="First step in a sequence.")
        seq_sub2 = Agent(name="SeqSub2", model="model-c", instruction="Second step in a sequence.")
        sequential_agent = SequentialAgent(
            name="NestedSequential",
            sub_agents=[seq_sub1, seq_sub2],
            description="A sequence inside a parallel workflow."
        )

        original_agent = ParallelAgent(
            name="MainParallelAgent",
            sub_agents=[loop_agent, sequential_agent],
            description="A parallel agent with complex nested workflows."
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, ParallelAgent)
        self.assertEqual(len(loaded_agent.sub_agents), 2)
        self.assertIsInstance(loaded_agent.sub_agents[0], LoopAgent)
        self.assertEqual(loaded_agent.sub_agents[0].description, "A loop inside a parallel workflow.")
        self.assertIsInstance(loaded_agent.sub_agents[1], SequentialAgent)
        self.assertEqual(loaded_agent.sub_agents[1].sub_agents[0].instruction, "First step in a sequence.")
        self.assertEqual(loaded_agent.sub_agents[0].max_iterations, 3)

    def test_save_and_load_loop_with_nested_parallel_agent(self):
        """Test a loop agent with a nested parallel agent."""
        # Nested parallel agent
        par_sub1 = Agent(name="ParSub1", model="model-x", instruction="One parallel task.")
        par_sub2 = Agent(name="ParSub2", model="model-y", instruction="Another parallel task.")
        parallel_agent = ParallelAgent(
            name="NestedParallel",
            sub_agents=[par_sub1, par_sub2],
            description="A parallel workflow inside a loop."
        )

        original_agent = LoopAgent(
            name="MainLoopAgent",
            sub_agents=[parallel_agent],
            description="A loop agent with a nested parallel workflow.",
            max_iterations=10
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, LoopAgent)
        self.assertEqual(loaded_agent.max_iterations, 10)
        self.assertEqual(len(loaded_agent.sub_agents), 1)
        self.assertIsInstance(loaded_agent.sub_agents[0], ParallelAgent)
        self.assertEqual(loaded_agent.sub_agents[0].description, "A parallel workflow inside a loop.")
        self.assertEqual(len(loaded_agent.sub_agents[0].sub_agents), 2)
        self.assertEqual(loaded_agent.sub_agents[0].sub_agents[1].name, "ParSub2")

    def test_deeply_nested_sequential_loop_parallel_agents(self):
        """Test a deeply nested combination of sequential, loop, and parallel agents."""
        # Innermost loop agent
        inner_loop_sub = Agent(name="InnerLoopSub", model="innermost-model", instruction="The deepest agent.")
        inner_loop_agent = LoopAgent(
            name="InnerLoop",
            sub_agents=[inner_loop_sub],
            description="A loop nested inside another loop.",
            max_iterations=2
        )

        # Outer loop agent
        outer_loop_sub1 = Agent(name="OuterLoopSub1", model="outer-model-1", instruction="First step of outer loop.")
        outer_loop_sub2 = inner_loop_agent
        outer_loop_sub3 = Agent(name="OuterLoopSub3", model="outer-model-2", instruction="Third step of outer loop.")
        outer_loop_agent = LoopAgent(
            name="OuterLoop",
            sub_agents=[outer_loop_sub1, outer_loop_sub2, outer_loop_sub3],
            description="A loop as the second step of the main sequence.",
            max_iterations=4
        )

        # Parallel agent
        parallel_sub1 = Agent(name="ParallelSub1", model="parallel-model-1", instruction="First parallel task.")
        parallel_sub2 = Agent(name="ParallelSub2", model="parallel-model-2", instruction="Second parallel task.")
        parallel_agent = ParallelAgent(
            name="MyParallelAgent",
            sub_agents=[parallel_sub1, parallel_sub2],
            description="A parallel agent as the third step of the main sequence."
        )

        # Main sequential agent
        step1 = Agent(name="Step1", model="step1-model", instruction="The first step.")
        step4 = Agent(name="Step4", model="step4-model", instruction="The final step.")
        original_agent = SequentialAgent(
            name="MainSequentialAgent",
            sub_agents=[step1, outer_loop_agent, parallel_agent, step4],
            description="A complex sequential agent with deeply nested workflows."
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, SequentialAgent)
        self.assertEqual(len(loaded_agent.sub_agents), 4)

        # Verify the outer loop agent
        loaded_outer_loop = loaded_agent.sub_agents[1]
        self.assertIsInstance(loaded_outer_loop, LoopAgent)
        self.assertEqual(loaded_outer_loop.name, "OuterLoop")
        self.assertEqual(loaded_outer_loop.max_iterations, 4)
        self.assertEqual(len(loaded_outer_loop.sub_agents), 3)
        self.assertEqual(loaded_outer_loop.sub_agents[0].instruction, "First step of outer loop.")

        # Verify the inner loop agent
        loaded_inner_loop = loaded_outer_loop.sub_agents[1]
        self.assertIsInstance(loaded_inner_loop, LoopAgent)
        self.assertEqual(loaded_inner_loop.name, "InnerLoop")
        self.assertEqual(loaded_inner_loop.max_iterations, 2)
        self.assertEqual(loaded_inner_loop.sub_agents[0].model, "innermost-model")

        # Verify the parallel agent
        loaded_parallel = loaded_agent.sub_agents[2]
        self.assertIsInstance(loaded_parallel, ParallelAgent)
        self.assertEqual(len(loaded_parallel.sub_agents), 2)
        self.assertEqual(loaded_parallel.sub_agents[1].name, "ParallelSub2")

    def test_save_and_load_agent_with_various_tools(self):
        """Test saving and loading an agent with multiple FunctionTools."""
        from tools.gadk.tools import get_current_time, get_temperature

        tool1 = FunctionTool(get_current_time)
        tool2 = FunctionTool(get_temperature)

        original_agent = Agent(
            name="ToolAgent",
            model="test-model",
            instruction="This agent has multiple function tools.",
            tools=[tool1, tool2]
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, Agent)
        self.assertEqual(len(loaded_agent.tools), 2)
        self.assertIsInstance(loaded_agent.tools[0], FunctionTool)
        self.assertEqual(loaded_agent.tools[0].func.__name__, "get_current_time")
        self.assertIsInstance(loaded_agent.tools[1], FunctionTool)
        self.assertEqual(loaded_agent.tools[1].func.__name__, "get_temperature")

    def test_save_and_load_agent_with_even_more_tools(self):
        """Test saving and loading an agent with a mix of tool types."""
        from google.adk.tools import FunctionTool, LongRunningFunctionTool
        from google.adk.tools.agent_tool import AgentTool
        from tools.gadk.tools import get_current_time, get_temperature

        tool1 = FunctionTool(get_current_time)
        tool2 = LongRunningFunctionTool(get_temperature)
        tool3 = AgentTool(Agent(name="SubAgentTool", model="sub-agent-model", instruction="This agent is a tool."))

        original_agent = Agent(
            name="ToolAgent",
            model="test-model",
            instruction="This agent has a variety of tools.",
            tools=[tool1, tool2, tool3]
        )

        save_agent_to_config(original_agent, self.config_path)
        loaded_agent = create_agent_from_config(self.config_path)

        self.assertIsInstance(loaded_agent, Agent)
        self.assertEqual(len(loaded_agent.tools), 3)
        self.assertIsInstance(loaded_agent.tools[0], FunctionTool)
        self.assertEqual(loaded_agent.tools[0].func.__name__, "get_current_time")
        self.assertIsInstance(loaded_agent.tools[1], LongRunningFunctionTool)
        self.assertEqual(loaded_agent.tools[1].func.__name__, "get_temperature")
        self.assertIsInstance(loaded_agent.tools[2], AgentTool)
        self.assertEqual(loaded_agent.tools[2].agent.name, "SubAgentTool")


if __name__ == '__main__':
    unittest.main()
