import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_io import create_agent_from_config, save_agent_to_config
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import FunctionTool

# First, let's create an agent from scratch to demonstrate the serialization
def dummy_function():
    """A dummy function for demonstration."""
    return "This is a dummy function result"

# Create a simple agent with tools
simple_agent = Agent(
    name="SimpleAgent",
    model="test-model",
    instruction="A simple test agent",
    tools=[FunctionTool(dummy_function)]
)

print("=== Creating and saving a simple agent ===")
print(f"Created agent: {simple_agent.name}")
print(f"Agent type: {type(simple_agent).__name__}")
print(f"Number of tools: {len(simple_agent.tools)}")

# Save the agent
save_agent_to_config(simple_agent, "simple_agent_config.json")
print("✅ Agent saved to simple_agent_config.json")

# Load it back
loaded_agent = create_agent_from_config("simple_agent_config.json")
print(f"✅ Loaded agent: {loaded_agent.name}")
print(f"   Type: {type(loaded_agent).__name__}")
print(f"   Tools: {len(loaded_agent.tools)}")

print("\n=== Creating a sequential agent ===")
# Create a sequential agent
sub_agent1 = Agent(name="SubAgent1", model="test-model", instruction="First sub-agent")
sub_agent2 = Agent(name="SubAgent2", model="test-model", instruction="Second sub-agent")

sequential_agent = SequentialAgent(
    name="MySequentialAgent",
    description="A test sequential agent",
    sub_agents=[sub_agent1, sub_agent2]
)

print(f"Created sequential agent: {sequential_agent.name}")
print(f"Sub-agents: {[sub.name for sub in sequential_agent.sub_agents]}")

# Save and load the sequential agent
save_agent_to_config(sequential_agent, "sequential_agent_config.json")
print("✅ Sequential agent saved to sequential_agent_config.json")

loaded_sequential = create_agent_from_config("sequential_agent_config.json")
print(f"✅ Loaded sequential agent: {loaded_sequential.name}")
print(f"   Sub-agents: {[sub.name for sub in loaded_sequential.sub_agents]}")

print("\n🎉 Example completed successfully!")
