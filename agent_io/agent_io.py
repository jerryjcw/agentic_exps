
import json
import yaml
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
        # Handle string tool names by using the registry
        tool_name = tool_config
        
        from tools.gadk.registry import registry
        
        # Try to get the tool from the registry
        if tool_name in registry:
            return registry[tool_name]
        
        # Try with _tool suffix
        tool_name_with_suffix = f"{tool_name}_tool"
        if tool_name_with_suffix in registry:
            return registry[tool_name_with_suffix]
        
        # Try without _tool suffix if it has one
        if tool_name.endswith("_tool"):
            tool_name_without_suffix = tool_name[:-5]
            if tool_name_without_suffix in registry:
                return registry[tool_name_without_suffix]
        
        # If tool not found, provide helpful error message
        available_tools = list(registry.get_all_tools().keys())
        raise ValueError(f"Unknown tool name: '{tool_name}'. Available tools in registry: {available_tools}")
    
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

    # Start with core agent metadata
    config = {
        "name": agent.name,
        "class": agent.__class__.__name__,
        "module": agent.__class__.__module__
    }
    
    # Explicitly handle all required agent parameters
    required_params = [
        "model", "instruction", "description", "output_key", 
        "max_iterations", "max_iteration"  # Handle both naming conventions
    ]
    
    for param in required_params:
        if hasattr(agent, param):
            value = getattr(agent, param)
            if value is not None:
                # Handle model serialization
                if param == "model":
                    # Convert model object to string representation
                    if hasattr(value, 'model'):
                        config[param] = value.model
                    else:
                        config[param] = str(value)
                else:
                    config[param] = value
    
    # Handle other agent attributes (for backward compatibility and extensibility)
    for key, value in agent.__dict__.items():
        if (key not in ["name", "class", "module", "sub_agents", "parent_agent", "tools"] 
            and not key.startswith("_") 
            and value is not None
            and key not in config):  # Don't overwrite explicitly handled params
            if isinstance(value, (str, int, float, bool, list, dict)):
                config[key] = value

    # Handle sub_agents (for composite agents)
    if hasattr(agent, "sub_agents") and agent.sub_agents:
        config["sub_agents"] = [_agent_to_dict(sub_agent, visited_agents) for sub_agent in agent.sub_agents]

    # Handle tools
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
    Reads an agent configuration from a YAML or JSON file and creates an Agent instance.
    Handles Agent, SequentialAgent, ParallelAgent, LoopAgent, and custom agents.

    Args:
        config_path (str): The path to the YAML or JSON configuration file.

    Returns:
        BaseAgent: An instance of the created agent.
    """
    with open(config_path, 'r') as f:
        if str(config_path).endswith(('.yaml', '.yml')):
            config = yaml.safe_load(f)
        else:
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
    agent_args = config_copy.copy()

    # Handle tools - convert tool configs to actual tool instances
    if "tools" in agent_args:
        agent_args["tools"] = [_create_tool_from_config(tool_config) for tool_config in agent_args["tools"]]

    # Handle sub_agents - recursively create sub-agent instances
    if "sub_agents" in agent_args:
        agent_args["sub_agents"] = [_create_agent_from_dict(sub_agent_config) for sub_agent_config in agent_args["sub_agents"]]

    # Handle model - convert string model names to LiteLlm objects
    if "model" in agent_args and isinstance(agent_args["model"], str):
        from google.adk.models.lite_llm import LiteLlm
        model_name = agent_args["model"]
        agent_args["model"] = LiteLlm(model=model_name)

    # Handle parameter name variations (max_iterations vs max_iteration)
    if "max_iteration" in agent_args and "max_iterations" not in agent_args:
        agent_args["max_iterations"] = agent_args.pop("max_iteration")
    elif "max_iterations" in agent_args and "max_iteration" in agent_args:
        # If both exist, prefer max_iterations and remove max_iteration
        agent_args.pop("max_iteration", None)

    # Validate required parameters for different agent types
    _validate_agent_parameters(agent_class_name, agent_args)

    return agent_class(**agent_args)

def _validate_agent_parameters(agent_class_name: str, agent_args: dict):
    """Validates that agent parameters are appropriate for the agent type."""
    
    # Define required/expected parameters for each agent type based on actual Google ADK support
    agent_parameter_requirements = {
        "Agent": {
            "required": ["name"],
            "optional": [
                "model", "instruction", "description", "output_key", "tools", 
                "global_instruction", "generate_content_config", "disallow_transfer_to_parent",
                "disallow_transfer_to_peers", "include_contents", "input_schema", "output_schema",
                "planner", "code_executor"
            ]
        },
        "SequentialAgent": {
            "required": ["name"],
            "optional": [
                "description", "sub_agents", "parent_agent", 
                "before_agent_callback", "after_agent_callback"
            ]
        },
        "ParallelAgent": {
            "required": ["name"],
            "optional": [
                "description", "sub_agents", "parent_agent",
                "before_agent_callback", "after_agent_callback"
            ]
        },
        "LoopAgent": {
            "required": ["name"],
            "optional": [
                "description", "sub_agents", "max_iterations", "parent_agent",
                "before_agent_callback", "after_agent_callback"
            ]
        }
    }
    
    if agent_class_name not in agent_parameter_requirements:
        # For unknown agent types, don't validate - assume they know what they're doing
        return
    
    requirements = agent_parameter_requirements[agent_class_name]
    
    # Check that required parameters are present
    for required_param in requirements["required"]:
        if required_param not in agent_args or agent_args[required_param] is None:
            raise ValueError(f"{agent_class_name} requires parameter '{required_param}' but it was not provided")
    
    # Warn about unexpected parameters (but don't fail - allow extensibility)
    all_expected = set(requirements["required"] + requirements["optional"])
    unexpected_params = set(agent_args.keys()) - all_expected
    if unexpected_params:
        print(f"Warning: {agent_class_name} received unexpected parameters: {unexpected_params}")
