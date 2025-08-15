"""
Agent Metadata Collector

This module provides utilities to collect structured agent metadata including
processed prompts with template variables resolved and file content summaries.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Metadata for a single agent including processed prompts."""
    name: str
    agent_type: str
    model: Optional[str]
    instruction: str
    description: Optional[str]
    output_key: Optional[str]
    tools: List[str]
    attached_files: List[Dict[str, Any]]
    template_variables_used: List[str]
    instruction_length: int
    sub_agents: List['AgentMetadata']


def truncate_text_to_words(text: str, max_words: int = 256) -> str:
    """
    Truncate text to specified number of words.
    
    Args:
        text: Text to truncate
        max_words: Maximum number of words to keep
        
    Returns:
        Truncated text with ellipsis if truncated
    """
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= max_words:
        return text
    
    truncated = " ".join(words[:max_words])
    return f"{truncated}..."


def extract_attached_files_from_instruction(instruction: str) -> List[Dict[str, Any]]:
    """
    Extract file information from agent instruction that contains attached file content.
    
    Args:
        instruction: Agent instruction that may contain attached files
        
    Returns:
        List of file information dictionaries
    """
    files = []
    
    # Pattern to match file content blocks added by prompt_utils.py
    file_pattern = r"--- Content from ([^-]+) ---\n\n```(\w+)\n(.*?)\n```\n\n--- End of ([^-]+) ---"
    
    matches = re.findall(file_pattern, instruction, re.DOTALL)
    
    for match in matches:
        file_name = match[0].strip()
        file_type = match[1].strip()
        file_content = match[2].strip()
        end_file_name = match[3].strip()
        
        # Ensure start and end file names match
        if file_name == end_file_name:
            # Decode HTML entities back to original characters for content analysis
            decoded_content = file_content.replace('&#123;', '{').replace('&#125;', '}')
            decoded_content = decoded_content.replace('&#91;', '[').replace('&#93;', ']')
            
            # Truncate to first 256 words
            truncated_content = truncate_text_to_words(decoded_content, 256)
            
            files.append({
                "file_name": file_name,
                "file_type": file_type,
                "content_preview": truncated_content,
                "original_content_length": len(decoded_content),
                "is_truncated": len(decoded_content.split()) > 256
            })
    
    return files


def extract_template_variables_from_instruction(instruction: str) -> List[str]:
    """
    Extract template variable names that were processed in the instruction.
    
    This looks for patterns that suggest template variables were replaced,
    by finding common contextual phrases that indicate template processing.
    
    Args:
        instruction: Agent instruction to analyze
        
    Returns:
        List of likely template variable names that were processed
    """
    variables = set()
    
    # Common patterns that suggest template variables were processed
    # Look for contextual phrases that indicate template replacement
    patterns = [
        r"You are (?:a|an) (.+?) (?:expert|specialist|developer|engineer)",
        r"specializing in (.+?) (?:development|security|analysis)",
        r"focused on (.+?) (?:security|analysis|development)",
        r"Conduct (?:a )?(.+?) (?:analysis|review|assessment)",
        r"considering (?:the )?(.+?) (?:environment|context|requirements)",
        r"suitable for (.+?) (?:environment|context|teams)",
        r"following (.+?) (?:guidelines|standards|practices)",
        r"Perform (.+?) (?:analysis|assessment|review)",
        r"provide (.+?) (?:analysis|explanations|recommendations)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, instruction, re.IGNORECASE)
        for match in matches:
            # Clean up the match and add as potential variable value
            cleaned = match.strip().lower()
            if cleaned and len(cleaned) > 2:  # Avoid very short matches
                variables.add(cleaned)
    
    return sorted(list(variables))


def collect_agent_metadata(agent_config: Dict[str, Any], depth: int = 0) -> AgentMetadata:
    """
    Collect metadata from a processed agent configuration.
    
    Args:
        agent_config: Agent configuration dictionary (after template processing)
        depth: Current depth in agent hierarchy (for tracking nesting)
        
    Returns:
        AgentMetadata object with all collected information
    """
    # Extract basic agent information
    name = agent_config.get('name', 'Unknown Agent')
    agent_type = agent_config.get('class', 'Unknown')
    model = agent_config.get('model')
    instruction = agent_config.get('instruction', '')
    description = agent_config.get('description', '')
    output_key = agent_config.get('output_key')
    
    # Convert model object to string if needed
    if model and hasattr(model, 'model'):
        model = model.model
    elif model:
        model = str(model)
    
    # Extract tools information
    tools = []
    if 'tools' in agent_config and agent_config['tools']:
        for tool in agent_config['tools']:
            if hasattr(tool, 'func') and hasattr(tool.func, '__name__'):
                tools.append(tool.func.__name__)
            elif isinstance(tool, dict):
                tool_name = tool.get('function_name', tool.get('class', 'Unknown Tool'))
                tools.append(tool_name)
            else:
                tools.append(str(type(tool).__name__))
    
    # Extract attached files from instruction
    attached_files = extract_attached_files_from_instruction(instruction)
    
    # Extract template variables that were likely processed
    template_variables_used = extract_template_variables_from_instruction(instruction)
    
    # Calculate instruction length
    instruction_length = len(instruction)
    
    # Recursively collect sub-agent metadata
    sub_agents = []
    if 'sub_agents' in agent_config and agent_config['sub_agents']:
        for sub_agent_config in agent_config['sub_agents']:
            sub_agent_metadata = collect_agent_metadata(sub_agent_config, depth + 1)
            sub_agents.append(sub_agent_metadata)
    
    return AgentMetadata(
        name=name,
        agent_type=agent_type,
        model=model,
        instruction=instruction,
        description=description,
        output_key=output_key,
        tools=tools,
        attached_files=attached_files,
        template_variables_used=template_variables_used,
        instruction_length=instruction_length,
        sub_agents=sub_agents
    )


def agent_metadata_to_dict(metadata: AgentMetadata, instruction_preview_length: int = 256) -> Dict[str, Any]:
    """
    Convert AgentMetadata to dictionary for JSON serialization.
    
    Args:
        metadata: AgentMetadata object to convert
        instruction_preview_length: Maximum number of words for instruction preview (default: 256)
        
    Returns:
        Dictionary representation of agent metadata
    """
    result = {
        "name": metadata.name,
        "agent_type": metadata.agent_type,
        "model": metadata.model,
        "description": metadata.description,
        "output_key": metadata.output_key,
        "tools": metadata.tools,
        "attached_files": metadata.attached_files,
        "template_variables_used": metadata.template_variables_used,
        "instruction_length": metadata.instruction_length,
        "instruction_preview": truncate_text_to_words(metadata.instruction, instruction_preview_length) if metadata.instruction else "",
        "sub_agents": [agent_metadata_to_dict(sub, instruction_preview_length) for sub in metadata.sub_agents]
    }
    
    return result


def collect_all_agents_metadata(agent_config: Dict[str, Any], instruction_preview_length: int = 256) -> Dict[str, Any]:
    """
    Collect metadata from all agents in a configuration hierarchy.
    
    Args:
        agent_config: Root agent configuration (after template processing)
        instruction_preview_length: Maximum number of words for instruction preview (default: 256)
        
    Returns:
        Dictionary containing structured agent metadata
    """
    root_metadata = collect_agent_metadata(agent_config)
    
    # Create a flat list of all agents for easy reference
    all_agents = []
    
    def _flatten_agents(metadata: AgentMetadata, parent_name: Optional[str] = None):
        """Recursively flatten agent hierarchy."""
        agent_info = agent_metadata_to_dict(metadata, instruction_preview_length)
        agent_info["parent_agent"] = parent_name
        agent_info["has_sub_agents"] = len(metadata.sub_agents) > 0
        agent_info["sub_agent_count"] = len(metadata.sub_agents)
        all_agents.append(agent_info)
        
        for sub_agent in metadata.sub_agents:
            _flatten_agents(sub_agent, metadata.name)
    
    _flatten_agents(root_metadata)
    
    # Create summary statistics
    total_agents = len(all_agents)
    agents_with_files = sum(1 for agent in all_agents if agent["attached_files"])
    agents_with_tools = sum(1 for agent in all_agents if agent["tools"])
    total_attached_files = sum(len(agent["attached_files"]) for agent in all_agents)
    
    agent_types = {}
    for agent in all_agents:
        agent_type = agent["agent_type"]
        agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
    
    return {
        "root_agent": agent_metadata_to_dict(root_metadata, instruction_preview_length),
        "all_agents": all_agents,
        "summary": {
            "total_agents": total_agents,
            "agents_with_attached_files": agents_with_files,
            "agents_with_tools": agents_with_tools,
            "total_attached_files": total_attached_files,
            "agent_types": agent_types,
            "hierarchy_depth": _calculate_max_depth(root_metadata)
        }
    }


def _calculate_max_depth(metadata: AgentMetadata, current_depth: int = 1) -> int:
    """Calculate maximum depth of agent hierarchy."""
    if not metadata.sub_agents:
        return current_depth
    
    max_sub_depth = max(_calculate_max_depth(sub, current_depth + 1) for sub in metadata.sub_agents)
    return max_sub_depth


def log_agent_metadata_summary(metadata: Dict[str, Any]) -> None:
    """
    Log a summary of collected agent metadata.
    
    Args:
        metadata: Agent metadata dictionary from collect_all_agents_metadata()
    """
    summary = metadata["summary"]
    logger.info("🤖 Agent Metadata Collection Summary:")
    logger.info(f"   Total Agents: {summary['total_agents']}")
    logger.info(f"   Agents with Attached Files: {summary['agents_with_attached_files']}")
    logger.info(f"   Agents with Tools: {summary['agents_with_tools']}")
    logger.info(f"   Total Attached Files: {summary['total_attached_files']}")
    logger.info(f"   Hierarchy Depth: {summary['hierarchy_depth']}")
    logger.info(f"   Agent Types: {summary['agent_types']}")