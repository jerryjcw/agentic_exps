#!/usr/bin/env python3
"""
Agent utility functions for analysis and display.

This module contains common functions for analyzing agent structures,
collecting statistics, displaying readiness information, and managing
execution steps.
"""

import datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ExecutionStep:
    """Represents a single execution step in the agent workflow."""
    step_id: str
    agent_name: str
    agent_type: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    events_generated: int = 0
    output_preview: str = ""


def analyze_agent_structure(agent):
    """
    Analyzes and displays the structure of an agent.
    
    Args:
        agent: The agent instance to analyze
    """
    print("\n3. Analyzing agent structure...")
    
    def analyze_recursive(agent, depth=0):
        """Recursively analyze agent structure."""
        indent = "  " * depth
        agent_type = agent.__class__.__name__
        
        print(f"{indent}├─ {agent.name} ({agent_type})")
        
        # Show agent-specific properties
        if hasattr(agent, 'model') and agent.model:
            print(f"{indent}│  └─ Model: {agent.model}")
        if hasattr(agent, 'instruction') and agent.instruction:
            instruction_preview = agent.instruction[:80] + "..." if len(agent.instruction) > 80 else agent.instruction
            print(f"{indent}│  └─ Instruction: {instruction_preview}")
        if hasattr(agent, 'output_key') and agent.output_key:
            print(f"{indent}│  └─ Output Key: {agent.output_key}")
        if hasattr(agent, 'tools') and agent.tools:
            print(f"{indent}│  └─ Tools: {len(agent.tools)} available")
            for tool in agent.tools:
                tool_name = tool.func.__name__ if hasattr(tool, 'func') else str(type(tool))
                print(f"{indent}│     - {tool_name}")
        if hasattr(agent, 'max_iterations') and agent.max_iterations:
            print(f"{indent}│  └─ Max Iterations: {agent.max_iterations}")
        
        # Recursively analyze sub-agents
        if hasattr(agent, 'sub_agents') and agent.sub_agents:
            print(f"{indent}│  └─ Sub-agents: {len(agent.sub_agents)}")
            for sub_agent in agent.sub_agents:
                analyze_recursive(sub_agent, depth + 1)
    
    analyze_recursive(agent)


def get_agent_statistics(agent):
    """
    Collects statistics about the agent structure.
    
    Args:
        agent: The agent instance to analyze
        
    Returns:
        dict: Statistics about the agent
    """
    stats = {
        'total_agents': 0,
        'agents_with_instructions': 0,
        'agents_with_tools': 0,
        'composite_agents': 0,
        'agent_types': {}
    }
    
    def count_recursive(agent):
        stats['total_agents'] += 1
        
        agent_type = agent.__class__.__name__
        stats['agent_types'][agent_type] = stats['agent_types'].get(agent_type, 0) + 1
        
        if hasattr(agent, 'instruction') and agent.instruction:
            stats['agents_with_instructions'] += 1
        if hasattr(agent, 'tools') and agent.tools:
            stats['agents_with_tools'] += 1
        if agent_type in ['SequentialAgent', 'ParallelAgent', 'LoopAgent']:
            stats['composite_agents'] += 1
            
        if hasattr(agent, 'sub_agents'):
            for sub_agent in agent.sub_agents:
                count_recursive(sub_agent)
    
    count_recursive(agent)
    return stats


def display_agent_readiness(agent):
    """
    Displays agent execution readiness information.
    
    Args:
        agent: The agent instance to check
    """
    print("\n4. Agent execution readiness check...")
    
    stats = get_agent_statistics(agent)
    
    print(f"   ✓ Total agents in workflow: {stats['total_agents']}")
    print(f"   ✓ Agents with instructions: {stats['agents_with_instructions']}")
    print(f"   ✓ Agents with tools: {stats['agents_with_tools']}")
    print(f"   ✓ Composite agents: {stats['composite_agents']}")
    
    print("   ✓ Agent types breakdown:")
    for agent_type, count in stats['agent_types'].items():
        print(f"     - {agent_type}: {count}")
    
    print(f"\n5. Agent creation complete!")
    print(f"   Agent '{agent.name}' is ready for execution.")


def collect_agent_execution_steps(agent, step_id_prefix="step"):
    """
    Collect all agent information in the form of ExecutionStep objects using DFS.
    
    Args:
        agent: The instantiated agent
        step_id_prefix: Prefix for step IDs
        
    Returns:
        List[ExecutionStep]: List of ExecutionStep objects for all agents
    """
    execution_steps = []
    visited_agents = set()  # Track visited agents by object id to prevent cycles
    step_counter = [1]  # Use list to allow modification in nested function
    
    def _create_execution_step(agent_obj, step_id, description_suffix=""):
        """Helper to create ExecutionStep from agent object."""
        agent_name = getattr(agent_obj, 'name', 'Unknown Agent')
        agent_type = agent_obj.__class__.__name__
        description = f"Execute {agent_name} ({agent_type}){description_suffix}"
        
        return ExecutionStep(
            step_id=step_id,
            agent_name=agent_name,
            agent_type=agent_type,
            description=description,
            status="pending",
            start_time=None,
            end_time=None,
            events_generated=0,
            output_preview=""
        )
    
    def _dfs_collect_agents(current_agent, depth=0, parent_name=""):
        """Depth-first search to collect all agents recursively."""
        agent_id = id(current_agent)
        
        # Skip if already visited (prevents infinite loops)
        if agent_id in visited_agents:
            return
        
        visited_agents.add(agent_id)
        
        # Create step for current agent
        step_id = f"{step_id_prefix}_{step_counter[0]:03d}"
        
        if depth == 0:
            description_suffix = " - Main Agent"
        elif depth == 1:
            description_suffix = f" - Sub-agent"
        else:
            description_suffix = f" - Nested (depth {depth})"
            
        if parent_name:
            description_suffix += f" under {parent_name}"
        
        step = _create_execution_step(current_agent, step_id, description_suffix)
        execution_steps.append(step)
        step_counter[0] += 1
        
        # Recursively process sub-agents if they exist
        if hasattr(current_agent, 'sub_agents') and current_agent.sub_agents:
            current_agent_name = getattr(current_agent, 'name', 'Unknown Agent')
            for sub_agent in current_agent.sub_agents:
                _dfs_collect_agents(sub_agent, depth + 1, current_agent_name)
    
    # Start DFS from the main agent
    _dfs_collect_agents(agent)
    
    return execution_steps


def display_execution_steps_summary(execution_steps):
    """
    Display a summary of all collected ExecutionStep objects.
    
    Args:
        execution_steps: List of ExecutionStep objects
    """
    print(f"\n" + "=" * 60)
    print(f"Agent Execution Steps Summary")
    print(f"=" * 60)
    print(f"Total Steps: {len(execution_steps)}")
    print(f"\nStep Details:")
    print("-" * 40)
    
    for step in execution_steps:
        print(f"🔄 {step.step_id}: {step.agent_name}")
        print(f"   Type: {step.agent_type}")
        print(f"   Description: {step.description}")
        print(f"   Status: {step.status}")
        print()