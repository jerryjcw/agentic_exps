#!/usr/bin/env python3
"""
Agent Creator - General utility for loading and instantiating agents from JSON configurations.

This script provides a general framework for creating Google ADK agents from JSON
configuration files, with the code improvement workflow as a demonstration example.
"""

import os
import sys
import json
import asyncio
import datetime
import threading
import time
from pathlib import Path
from typing import Dict

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_io.agent_io import create_agent_from_config
from data_model import validate_configuration_file
from utils import analyze_agent_structure, display_agent_readiness
from utils.agent_utils import collect_agent_execution_steps, display_execution_steps_summary




def create_agent_from_config_file(config_path):
    """
    Complete workflow to create an agent from a configuration file.
    
    Args:
        config_path (str or Path): Path to the JSON configuration file
        
    Returns:
        The instantiated agent or None if creation failed
    """
    config_path = Path(config_path)
    
    print("=" * 60)
    print(f"Agent Initialization: {config_path.name}")
    print("=" * 60)
    
    # Validate configuration
    print("1. Validating configuration...")
    try:
        _, warnings = validate_configuration_file(config_path)
        print(f"   ✓ Configuration is valid")
        if warnings:
            print(f"   ⚠ {len(warnings)} warnings found:")
            for warning in warnings:
                print(f"     - {warning}")
        else:
            print("   ✓ No warnings")
    except Exception as e:
        print(f"   ✗ Configuration validation failed: {e}")
        return None
    
    # Create agent
    print("\n2. Creating agent from configuration...")
    try:
        agent = create_agent_from_config(str(config_path))
        print(f"   ✓ Agent '{agent.name}' created successfully")
        print(f"   ✓ Agent type: {agent.__class__.__name__}")
        if hasattr(agent, 'sub_agents'):
            print(f"   ✓ Number of sub-agents: {len(agent.sub_agents)}")
    except Exception as e:
        print(f"   ✗ Agent creation failed: {e}")
        return None
    
    # Analyze structure and display readiness
    analyze_agent_structure(agent)
    display_agent_readiness(agent)
    
    return agent


def _save_analysis_results(input_path, agent, event_count, full_response, code_content):
    """Helper function to save analysis results to files."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_time = datetime.datetime.now()
    
    # Save text report
    output_file = output_dir / f"code_analysis_{input_path.stem}_{timestamp}.txt"
    with open(output_file, 'w') as f:
        f.write(f"Code Improvement Analysis Report\n")
        f.write(f"================================\n\n")
        f.write(f"Analysis Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input File: {input_path}\n")
        f.write(f"Agent: {agent.name}\n")
        f.write(f"Events Generated: {event_count}\n\n")
        f.write("Analysis Results:\n")
        f.write("-" * 40 + "\n\n")
        f.write(full_response)
    
    # Save JSON report
    json_output = {
        "metadata": {
            "analysis_date": current_time.isoformat(),
            "input_file": str(input_path),
            "agent_name": agent.name,
            "events_generated": event_count,
            "file_size": len(code_content),
            "lines_of_code": len(code_content.splitlines())
        },
        "analysis_results": full_response,
        "code_analyzed": code_content
    }
    
    json_file = output_dir / f"code_analysis_{input_path.stem}_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2)
    
    print(f"📁 Output saved to: {output_file}")
    print(f"📄 JSON output saved to: {json_file}")
    
    return str(output_file), str(json_file)


async def run_agent_with_input(agent, input_file_path):
    """
    Run the agent with actual code input for analysis.
    
    Args:
        agent: The instantiated agent
        input_file_path: Path to the code file to analyze
        
    Returns:
        dict: Analysis results with file paths and metadata
    """
    # Import all required modules at once
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import types
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Read and validate input file
    input_path = Path(input_file_path)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return None
    
    with open(input_path, 'r') as f:
        code_content = f.read()
    
    # Display input information
    print("\n" + "=" * 60)
    print(f"Running Agent with Input: {input_path.name}")
    print("=" * 60)
    print(f"Input file: {input_path}")
    print(f"File size: {len(code_content)} characters")
    print(f"Lines of code: {len(code_content.splitlines())}")
    print(f"\nCode preview (first 500 characters):")
    print("-" * 40)
    print(code_content[:500] + ("..." if len(code_content) > 500 else ""))
    print("-" * 40)
    print(f"\nExecuting agent workflow...")

    try:
        # Set up session and runner
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="CodeImprovementAnalysis",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            user_id="code_analyzer",
            session_id="analysis_session",
            app_name="CodeImprovementAnalysis"
        )
        
        # Create analysis request
        user_query = f"""Please analyze the following Python code for improvements:

File: {input_path.name}
Language: Python
Framework: Google ADK

Code to analyze:
```python
{code_content}
```

Please provide a comprehensive analysis focusing on:
1. Security vulnerabilities and defensive measures
2. Performance bottlenecks and optimization opportunities  
3. Code quality issues and maintainability improvements
4. Testing gaps and coverage recommendations

Provide specific recommendations with examples where possible."""

        message = types.Content(role="user", parts=[{"text": user_query}])
        
        print(f"\n🤖 Starting code improvement analysis...")
        print("This may take several minutes as the workflow processes through all agents...")
        print("-" * 60)
        
        # Run agent and collect responses
        response_generator = runner.run(
            user_id="code_analyzer",
            session_id="analysis_session", 
            new_message=message
        )
        
        full_response = ""
        event_count = 0
        
        for event in response_generator:
            event_count += 1
            for field in ["author", "id", "invocation_id"]:
                print(f"📌 {field} = {getattr(event, field, 'N/A')}")
            if hasattr(event, 'actions'):
                print(f"📌 Actions: transfer_to_agent = {event.actions.transfer_to_agent}, escalate = {event.actions.escalate}")
            print(f"Session state: {session.state}")

            # Process event content
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            content_text = part.text
                            full_response += content_text
                            
                            # Show progress
                            preview = (content_text[:100].replace('\n', ' ') + "..." 
                                     if len(content_text) > 100 else content_text)
                            print(f"📨 Event {event_count}: {type(event).__name__}")
                            print(f"   📝 Content: {preview}")
            else:
                # Even events without content are valuable for tracking
                print(f"📨 Event {event_count}: {type(event).__name__}")
        
        print(f"\n✅ Analysis completed! Generated {event_count} events")
        
        # Save results
        output_file, json_file = _save_analysis_results(
            input_path, agent, event_count, full_response, code_content
        )
        
        return {
            "status": "completed",
            "output_file": output_file,
            "json_file": json_file,
            "events_generated": event_count,
            "response_length": len(full_response),
            "analysis_results": full_response
        }
        
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        return None


def _display_results_summary(results):
    """Helper function to display execution results summary."""
    print("\n" + "=" * 60)
    print("Execution Results Summary")
    print("=" * 60)
    
    if isinstance(results, dict):
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Events Generated: {results.get('events_generated', 0)}")
        print(f"Response Length: {results.get('response_length', 0)} characters")
        if results.get('output_file'):
            print(f"Text Output: {results['output_file']}")
        if results.get('json_file'):
            print(f"JSON Output: {results['json_file']}")
    else:
        print("No results returned from agent execution")


async def main_async():
    """Main async function that creates and runs the code improvement agent."""
    print("Code Improvement Agent - Live Execution Demo")
    print("=" * 60)
    
    try:
        # Create agent
        config_path = Path(__file__).parent.parent / "config" / "json_examples" / "code_improvement_workflow.json"
        print("Creating Code Improvement Agent...")
        agent = create_agent_from_config_file(config_path)
        
        if agent is None:
            print("Failed to create agent. Exiting.")
            return 1
        
        # Collect agent execution steps
        print(f"\nCollecting agent execution steps...")
        execution_steps = collect_agent_execution_steps(agent)
        print(f"######## Total execution steps collected: {len(execution_steps)}")
        display_execution_steps_summary(execution_steps)
        
        # Run agent analysis
        input_file = Path(__file__).parent.parent / "agent_io" / "agent_io.py"
        print(f"\nExecuting agent analysis on: {input_file}")
        results = await run_agent_with_input(agent, input_file)
        
        # Display results
        if results:
            _display_results_summary(results)
        
        print("\n" + "=" * 60)
        print("Agent execution completed successfully!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Synchronous main function that runs the async workflow."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    exit_code = main()