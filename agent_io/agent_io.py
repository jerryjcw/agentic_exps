
import json
import importlib
from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent, BaseAgent
from google.adk.tools import FunctionTool, LongRunningFunctionTool
from google.adk.tools.agent_tool import AgentTool

def _tool_to_dict(tool) -> dict:
    """Converts a tool to a dictionary for serialization."""
    tool_config = {
        "class": tool.__class__.__name__,
        "module": tool.__class__.__module__
    }
    if isinstance(tool, (FunctionTool, LongRunningFunctionTool)):
        tool_config["function_name"] = tool.func.__name__
        tool_config["function_module"] = tool.func.__module__
    elif isinstance(tool, AgentTool):
        tool_config["agent"] = _agent_to_dict(tool.agent)
    # Handle other tool types that may need specific serialization
    
    return tool_config

def _create_tool_from_dict(tool_config: dict):
    """Recursively creates a tool from a dictionary configuration."""
    # Make a copy to avoid modifying the original dict
    config_copy = tool_config.copy()
    tool_class_name = config_copy.pop("class")
    tool_module_name = config_copy.pop("module")

    try:
        tool_module = importlib.import_module(tool_module_name)
        tool_class = getattr(tool_module, tool_class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Could not import tool class {tool_class_name} from module {tool_module_name}: {e}")

    if tool_class_name in ["FunctionTool", "LongRunningFunctionTool"]:
        function_name = config_copy["function_name"]
        function_module_name = config_copy["function_module"]
        try:
            function_module = importlib.import_module(function_module_name)
            function = getattr(function_module, function_name)
            return tool_class(function)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not import function {function_name} from module {function_module_name}: {e}")
    elif tool_class_name == "AgentTool":
        agent = _create_agent_from_dict(config_copy["agent"])
        return AgentTool(agent)

    # For other tool types, try to instantiate with no arguments
    return tool_class()

def _create_tool_from_config(tool_config):
    """Creates a tool from either a string name or dictionary configuration."""
    if isinstance(tool_config, str):
        # Handle string tool names by looking up common functions
        tool_name = tool_config
        
        # Try to import common tool functions
        try:
            # First try from tools.gadk.tools
            from tools.gadk.tools import get_taipei_time, get_temperature
            tool_functions = {
                'get_taipei_time': get_taipei_time,
                'get_temperature': get_temperature
            }
            
            if tool_name in tool_functions:
                return FunctionTool(tool_functions[tool_name])
            else:
                raise ValueError(f"Unknown tool name: {tool_name}")
                
        except ImportError:
            raise ValueError(f"Could not import tools module to resolve tool name: {tool_name}")
    
    elif isinstance(tool_config, dict):
        return _create_tool_from_dict(tool_config)
    
    else:
        raise ValueError(f"Tool config must be string or dict, got {type(tool_config)}")

def _agent_to_dict(agent: BaseAgent, visited_agents=None) -> dict:
    """Converts an agent to a dictionary for serialization."""
    if visited_agents is None:
        visited_agents = set()

    if id(agent) in visited_agents:
        return {"name": agent.name, "class": agent.__class__.__name__, "module": agent.__class__.__module__}

    visited_agents.add(id(agent))

    config = {
        "name": agent.name,
        "class": agent.__class__.__name__,
        "module": agent.__class__.__module__
    }
    for key, value in agent.__dict__.items():
        if key not in ["name", "class", "module", "sub_agents", "parent_agent", "tools"] and not key.startswith("_") and value is not None:
            if isinstance(value, (str, int, float, bool, list, dict)):
                config[key] = value

    if hasattr(agent, "sub_agents") and agent.sub_agents:
        config["sub_agents"] = [_agent_to_dict(sub_agent, visited_agents) for sub_agent in agent.sub_agents]

    if hasattr(agent, "tools") and agent.tools:
        config["tools"] = [_tool_to_dict(tool) for tool in agent.tools]

    return config

def save_agent_to_config(agent: BaseAgent, config_path: str):
    """
    Saves an Agent instance to a text-based configuration file (JSON).
    Handles Agent, SequentialAgent, ParallelAgent, and LoopAgent.

    Args:
        agent (BaseAgent): The Agent instance to save.
        config_path (str): The path to the output JSON configuration file.
    """
    config = _agent_to_dict(agent)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def create_agent_from_config(config_path: str) -> BaseAgent:
    """
    Reads an agent configuration from a JSON file and creates an Agent instance.
    Handles Agent, SequentialAgent, ParallelAgent, LoopAgent, and custom agents.

    Args:
        config_path (str): The path to the JSON configuration file.

    Returns:
        BaseAgent: An instance of the created agent.
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    return _create_agent_from_dict(config)

def _create_agent_from_dict(config: dict) -> BaseAgent:
    """Recursively creates an agent from a dictionary configuration."""
    # Make a copy to avoid modifying the original dict
    config_copy = config.copy()
    agent_class_name = config_copy.pop("class")
    agent_module_name = config_copy.pop("module")

    try:
        agent_module = importlib.import_module(agent_module_name)
        agent_class = getattr(agent_module, agent_class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Could not import agent class {agent_class_name} from module {agent_module_name}: {e}")

    # Prepare args for the agent constructor
    agent_args = config_copy

    if "tools" in agent_args:
        agent_args["tools"] = [_create_tool_from_config(tool_config) for tool_config in agent_args["tools"]]

    if "sub_agents" in agent_args:
        agent_args["sub_agents"] = [_create_agent_from_dict(sub_agent_config) for sub_agent_config in agent_args["sub_agents"]]

    return agent_class(**agent_args)

