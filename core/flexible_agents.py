#!/usr/bin/env python3
"""
Flexible Agent Framework - General utility for loading and instantiating agents from configurations.

This script provides a general framework for creating Google ADK agents from configuration
files, supporting flexible workflows with multiple input files.
"""

# Standard library imports
import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
import re
import traceback
from pathlib import Path
from typing import Dict

# Third-party imports
import yaml
from dotenv import load_dotenv
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService
from jinja2 import Template

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local imports
from utils.document_reader import DocumentReader
from agent_io.agent_io import create_agent_from_config, _create_agent_from_dict
from data_model import validate_configuration_file
from utils import analyze_agent_structure, display_agent_readiness
from utils.agent_utils import (
    collect_agent_execution_steps, display_execution_steps_summary, 
    ExecutionStep, maintain_execution_status, report_finished_steps
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_job_config(job_config_path):
    """Load job configuration from YAML or JSON file."""
    with open(job_config_path, 'r') as f:
        if str(job_config_path).endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def load_template_config(template_config_path):
    """Load template configuration from YAML or JSON file."""
    with open(template_config_path, 'r') as f:
        if str(template_config_path).endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def read_input_file(file_path, input_type=None, **metadata):
    """
    Read a single input file and return its content and metadata.
    
    Args:
        file_path (str or Path): Path to the input file
        input_type (str): Explicit input type (overrides file extension)
        **metadata: Additional metadata for the file
        
    Returns:
        dict: Dictionary containing file_name, file_type, file_content, and metadata
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    document_reader = DocumentReader()
    if document_reader.is_supported(file_path):
        content = document_reader.read_document(file_path, as_markdown=True)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    # Determine file type
    if input_type:
        file_type = input_type
    else:
        file_type = file_path.suffix.lstrip('.') if file_path.suffix else ''
    
    result = {
        'file_name': file_path.name,
        'file_type': file_type,
        'file_content': content,
        'file_size': len(content),
        'full_path': str(file_path)
    }
    
    # Add any additional metadata
    result.update(metadata)
    
    return result


def synthesize_user_query_jinja2(template_config, file_names, file_types, file_contents):
    """
    Synthesize user query using Jinja2 template.
    
    Args:
        template_config: Template configuration dictionary
        file_names: List of file names (strings)
        file_types: List of file types (strings)  
        file_contents: List of file contents (strings)
    """
    
    # Get template content
    template_content = template_config.get('template_content', '')
    variable_mapping = template_config.get('template_variables', {})
    
    # Template variables
    template_vars = {
        k: v['default'] for k, v in variable_mapping.items()
    }

    logging.debug(f"Using template variables: {template_vars}")

    # Update template variables with file data arrays
    template_vars.update({
        'file_name': file_names,
        'file_type': file_types, 
        'file_content': file_contents
    })

    # Render template
    template = Template(template_content)
    rendered_query = template.render(**template_vars)

    logging.debug(f"Rendered query length: {len(rendered_query)} characters")

    return rendered_query


emojis = ["👤", "🤖", "💡", "🔍", "⚙️", "📊", "🛠️", "📈", "📝", "✅", "🌟", 
          "🚀", "🎯", "🧩", "🔧", "📅", "💻", "🖥️", "📱", "🖨️", "🗂️", "🔒", 
          "🔑", "🧰", "🧪", "🧬", "🧫", "🧫", "🧪", "🧬"]


def create_agent_from_config_file(config_path):
    """
    Complete workflow to create an agent from a configuration file.
    
    Args:
        config_path (str or Path): Path to the configuration file
        
    Returns:
        The instantiated agent or None if creation failed
    """
    config_path = Path(config_path)
    
    logging.info(f"Initializing agent: {config_path.name}")

    # Validate configuration
    try:
        _, warnings = validate_configuration_file(config_path)
        if warnings:
            logging.warning(f"Configuration has {len(warnings)} warnings")
    except Exception as e:
        logging.error(f"Configuration validation failed: {e}")
        return None
    
    # Create agent
    try:
        agent = create_agent_from_config(str(config_path))
        logging.info(f"Agent '{agent.name}' created successfully")
    except Exception as e:
        logging.error(f"Agent creation failed: {e}")
        return None
    
    # Analyze structure and display readiness
    analyze_agent_structure(agent)
    display_agent_readiness(agent)
    
    return agent


def _save_results(input_files_data, agent, event_count, final_responses: Dict[str, str], job_config: dict):
    """Helper function to save agent execution results to files."""
    output_config = job_config.get('output_config', {})
    output_dir = Path(__file__).parent.parent / output_config.get('output_directory', 'output')
    output_dir.mkdir(exist_ok=True)
    
    timestamp_format = output_config.get('timestamp_format', '%Y%m%d_%H%M%S')
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    current_time = datetime.datetime.now()
    
    # Generate filename based on input files
    if len(input_files_data) == 1:
        input_filename = Path(input_files_data[0]['full_path']).stem
    else:
        input_filename = f"multi_file_execution_{len(input_files_data)}_files"
    
    # Save text report
    file_naming = output_config.get('file_naming', 'agent_execution_{input_filename}_{timestamp}')
    output_file = output_dir / f"{file_naming.format(input_filename=input_filename, timestamp=timestamp)}.txt"
    with open(output_file, 'w') as f:
        f.write(f"Agent Execution Report\n")
        f.write(f"=====================\n\n")
        f.write(f"Execution Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input Files ({len(input_files_data)}):\n")
        for i, file_data in enumerate(input_files_data, 1):
            f.write(f"  {i}. {file_data['full_path']} ({file_data['file_size']} chars)\n")
        f.write(f"Agent: {agent.name}\n")
        f.write(f"Events Generated: {event_count}\n\n")
        
        # Include final responses
        if final_responses:
            f.write("\n\nFinal Responses:\n")
            f.write("-" * 40 + "\n")
            for author, response in final_responses.items():
                f.write(f"{author}:\n")
                f.write(response + "\n\n")
    
    # Save JSON report
    json_output = {
        "metadata": {
            "execution_date": current_time.isoformat(),
            "input_files": [
                {
                    "file_path": file_data['full_path'],
                    "file_name": file_data['file_name'],
                    "file_type": file_data['file_type'],
                    "file_size": file_data['file_size'],
                }
                for file_data in input_files_data
            ],
            "agent_name": agent.name,
            "events_generated": event_count,
            "total_file_size": sum(f['file_size'] for f in input_files_data),
        },
        "execution_results": final_responses,
        "content_analyzed": [file_data['file_content'] for file_data in input_files_data]
    }
    
    json_file = output_dir / f"{file_naming.format(input_filename=input_filename, timestamp=timestamp)}.json"
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2)
    
    logging.info(f"📁 Output saved to: {output_file}")
    logging.info(f"📄 JSON output saved to: {json_file}")

    return str(output_file), str(json_file)


async def run_agent(agent, user_query, job_config: dict):
    # Load environment variables
    load_dotenv()

    try:
        # Set up session and runner using job config
        runner_config = job_config.get('runner_config', {})
        session_config = runner_config.get('session_config', {})
        
        session_service = InMemorySessionService()
        runner = Runner(
            app_name=runner_config.get('app_name', 'CodeImprovementAnalysis'),
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            user_id=session_config.get('user_id', 'code_analyzer'),
            session_id=session_config.get('session_id', 'analysis_session'),
            app_name=runner_config.get('app_name', 'CodeImprovementAnalysis')
        )

        message = types.Content(role="user", parts=[{"text": user_query}])
        
        print(f"\n🤖 Starting code improvement analysis...")
        print("This may take several minutes as the workflow processes through all agents...")
        print("-" * 60)
        
        # Run agent and collect responses
        response_generator = runner.run(
            user_id=session_config.get('user_id', 'code_analyzer'),
            session_id=session_config.get('session_id', 'analysis_session'), 
            new_message=message
        )
        return response_generator, session
    except Exception as e:
        print(f"\nError during execution: {e}")
        traceback.print_exc()
        return None


def log_event_details(event, session):
    for field in ["author", "id", "invocation_id"]:
        logging.debug(f"📝 {field} = {getattr(event, field, 'N/A')}")
    if hasattr(event, 'actions'):
        logging.info(f"📝 Actions: transfer_to_agent = {event.actions.transfer_to_agent}, escalate = {event.actions.escalate}")
    logging.info(f"Session state: {session.state}")


def get_error_code_from_event(event):
    error_code = None
    if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts') and event.content.parts and len(event.content.parts) > 0:
        response = event.content.parts[0].text
        # Regular expression to extract error code
        error_code_match = re.search(r'Error code: (\d+)', response) if response else None
        if error_code_match:
            error_code = error_code_match.group(1)
    return error_code


async def run_job(agent, input_file_paths, execution_steps: Dict[str, ExecutionStep], job_config: dict):
    """
    Run the agent with input files for processing.
    
    Args:
        agent: The instantiated agent
        input_file_paths: List of paths to the files to process, or single path as string
        execution_steps: Dictionary of execution steps to track
        job_config: Job configuration dictionary
        
    Returns:
        dict: Execution results with file paths and metadata
    """
    # Load environment variables
    load_dotenv()
    
    # Handle input files structure
    input_files_data = []
    file_names = []
    file_types = []
    file_contents = []
    
    # Support different input formats
    if isinstance(input_file_paths, str):
        # Single file path as string
        input_file_paths = [{'path': input_file_paths, 'input_type': None}]
    elif isinstance(input_file_paths, list):
        # Check if it's a list of file info dicts or just paths
        if input_file_paths and isinstance(input_file_paths[0], dict):
            # Already in the correct format
            pass
        else:
            # Convert list of paths to list of file info dicts
            input_file_paths = [{'path': path, 'input_type': None} for path in input_file_paths]
    
    for file_info in input_file_paths:
        try:
            file_path = file_info['path']
            input_type = file_info.get('input_type')
            
            file_data = read_input_file(file_path, input_type)
            input_files_data.append(file_data)
            file_names.append(file_data['file_name'])
            file_types.append(file_data['file_type'])
            file_contents.append(file_data['file_content'])
        except FileNotFoundError as e:
            logging.error(str(e))
            return None
    
    # Display input information
    logging.info(f"Running agent with {len(input_files_data)} input file(s)")
    total_size = sum(data['file_size'] for data in input_files_data)
    
    for i, file_data in enumerate(input_files_data, 1):
        logging.info(f"  {i}. {file_data['file_name']} ({file_data['file_size']} chars, {file_data['file_type']})")
    
    logging.info(f"Total size: {total_size} characters")

    # Create analysis request using Jinja2 template synthesis
    analysis_config = job_config.get('analysis_config', {})
    
    # Load template config - either from content or from file path
    if 'template_config_content' in analysis_config:
        # Use template content directly
        template_config = analysis_config['template_config_content']
        logging.info("Using template config provided as content")
    else:
        # Load and synthesize template using Jinja2
        template_config_path = analysis_config.get('template_config_path')
        logging.info(f"Using template config path from job config: {template_config_path}")
        template_full_path = Path(__file__).parent.parent / template_config_path
        template_config = load_template_config(template_full_path)
    
    user_query = synthesize_user_query_jinja2(
        template_config, file_names, file_types, file_contents
    )
    logging.info(f"Synthesized query using Jinja2: {len(user_query)} characters")

    try:
        response_generator, session = await run_agent(agent, user_query, job_config)
        final_responses = {}
        event_count = 0
        
        for event in response_generator:
            event_count += 1

            # Make the following paragraph a function.
            log_event_details(event, session)

            author = event.author if hasattr(event, 'author') else 'unknown'
            error_code = get_error_code_from_event(event)
            
            if author in execution_steps:
                step = execution_steps[author]
                if step.status == "pending":
                    step.status = "running"
                    step.start_time = datetime.datetime.now().isoformat()

                if not error_code:
                    logging.info(f"✅ Agent: {step.agent_name} ({step.agent_type}) finished.")
                    step.status = "completed"
                    step.events_generated += 1
                    step.end_time = datetime.datetime.now().isoformat()
                    maintain_execution_status(execution_steps=execution_steps, agent_name=author)
                else:
                    logging.error(f"❌ Agent: {step.agent_name} ({step.agent_type}) failed.")
                    step.status = "failed"
                    step.end_time = datetime.datetime.now().isoformat()
            
            report_finished_steps(execution_steps)

            # Process event content
            if hasattr(event, 'content') and event.content:
                # If the event is the final response, keep it.
                if event.is_final_response():
                    final_response = f"{event.author} %% ({datetime.datetime.now().isoformat()}): "
                    if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                final_response += part.text
                    logging.info(f"Final response received: {len(final_response)} characters")
                    final_responses[event.author] = final_response
            else:
                # Even events without content are valuable for tracking
                logging.debug(f"📨 Event {event_count}: {type(event).__name__} has no content.")

        logging.info(f"Execution completed: {event_count} events generated")

        # Save results
        output_file, json_file = _save_results(
            input_files_data, agent, event_count, final_responses, job_config
        )
        
        return {
            "status": "completed",
            "output_file": output_file,
            "json_file": json_file,
            "events_generated": event_count,
            "response_length": sum(len(resp) for resp in final_responses.values()),
            "execution_results": final_responses,
        }
        
    except Exception as e:
        print(f"\nError during execution: {e}")
        traceback.print_exc()
        return None


def _display_results_summary(results):
    """Helper function to display execution results summary."""
    logging.info("\n" + "=" * 60)
    logging.info("Execution Results Summary")
    logging.info("=" * 60)

    if isinstance(results, dict):
        logging.info(f"Status: {results.get('status', 'unknown')}")
        logging.info(f"Events Generated: {results.get('events_generated', 0)}")
        logging.info(f"Response Length: {results.get('response_length', 0)} characters")
        if results.get('output_file'):
            logging.info(f"Text Output: {results['output_file']}")
        if results.get('json_file'):
            logging.info(f"JSON Output: {results['json_file']}")
    else:
        logging.warning("No results returned from agent execution")


async def main_async_with_config(job_config_content: str, agent_config_content: str, template_config_content: str):
    """
    Main async function that creates and runs the flexible agent using YAML content directly.
    
    Args:
        job_config_content (str): YAML content for job configuration
        agent_config_content (str): YAML content for agent configuration  
        template_config_content (str): YAML content for template configuration
        
    Returns:
        int: 0 for success, 1 for failure
    """
    
    try:
        # Parse job configuration from content
        job_config = yaml.safe_load(job_config_content)
        logging.info(f"Loaded job config: {job_config.get('job_name', 'Unknown')}")
        
        job_name = job_config.get('job_name', 'Flexible Agent')
        logging.info(f"{job_name} - Execution")

        # Parse agent configuration from content
        agent_config = yaml.safe_load(agent_config_content)
        logging.info("Creating agent from provided configuration...")
        
        # Create agent directly from the configuration content
        agent = _create_agent_from_dict(agent_config)
        
        if agent is None:
            logging.error("Failed to create agent. Exiting.")
            return 1
        
        # Analyze structure and display readiness
        analyze_agent_structure(agent)
        display_agent_readiness(agent)
        
        # Collect agent execution steps
        execution_config = job_config.get('execution_config', {})
        if execution_config.get('track_execution_steps', True):
            logging.info(f"\nCollecting agent execution steps...")
            execution_steps = collect_agent_execution_steps(agent)
            logging.info(f"💡 Total execution steps collected: {len(execution_steps)}")
            if execution_config.get('display_progress', True):
                display_execution_steps_summary(execution_steps)
        else:
            execution_steps = {}
        
        # Run agent analysis using job config
        input_config = job_config.get('input_config', {})
        
        # Handle input_files structure with input_path and input_type
        if 'input_files' in input_config:
            input_files_config = input_config['input_files']
            input_files = []
            
            logging.info(f"Executing agent on {len(input_files_config)} files:")
            for i, file_config in enumerate(input_files_config, 1):
                file_path = Path(__file__).parent.parent / file_config['input_path']
                input_files.append({
                    'path': file_path,
                    'input_type': file_config.get('input_type')
                })
                logging.info(f"  {i}. {file_path} ({file_config.get('input_type', 'auto')})")
        else:
            logging.error("No input_files found in input_config. Please configure input_files with input_path and input_type.")
            return 1
        
        # Parse template configuration and modify job_config to include it
        template_config = yaml.safe_load(template_config_content)
        
        # Temporarily modify job_config to include template content instead of path
        original_analysis_config = job_config.get('analysis_config', {}).copy()
        job_config['analysis_config'] = job_config.get('analysis_config', {}).copy()
        job_config['analysis_config']['template_config_content'] = template_config
        
        results = await run_job(agent, input_files, execution_steps, job_config)
        
        # Restore original analysis_config
        job_config['analysis_config'] = original_analysis_config
        
        # Display results
        report_config = job_config.get('report_config', {})
        if results and report_config.get('display_results_summary', True):
            _display_results_summary(results)
            if execution_config.get('track_execution_steps', True):
                report_finished_steps(execution_steps)
        
        logging.info("Agent execution completed successfully!")

        return 0
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        traceback.print_exc()
        return 1


async def main_async(job_name: str = "simple_code_improvement"):
    """Main async function that creates and runs the flexible agent."""
    
    try:
        # Load job configuration
        # Try YAML first, then fall back to JSON
        yaml_path = Path(__file__).parent.parent / "config" / "job" / "yaml_examples" / f"{job_name}.yaml"
        # json_path = Path(__file__).parent.parent / "config" / "job" / "json_examples" / f"{job_name}.json"
        
        if yaml_path.exists():
            job_config_path = yaml_path
            logging.info(f"Using YAML job config: {job_config_path}")
        else:
            raise FileNotFoundError(f"No job config found for '{job_name}' in YAML or JSON format")
        
        # Read job config content
        with open(job_config_path, 'r') as f:
            job_config_content = f.read()
        
        job_config = yaml.safe_load(job_config_content)
        logging.info(f"Loaded job config: {job_config.get('job_name', 'Unknown')}")

        # Load agent configuration content
        agent_config = job_config.get('agent_config', {})
        config_path = Path(__file__).parent.parent / agent_config.get('config_path', 'config/agent/json_examples/simple_code_improvement.json')
        logging.info(f"Loading agent config from: {config_path}")
        
        with open(config_path, 'r') as f:
            if str(config_path).endswith(('.yaml', '.yml')):
                agent_config_content = f.read()
            else:
                # Convert JSON to YAML for consistency
                agent_config_dict = json.load(f)
                agent_config_content = yaml.dump(agent_config_dict)
        
        # Load template configuration content
        analysis_config = job_config.get('analysis_config', {})
        template_config_path = analysis_config.get('template_config_path')
        template_full_path = Path(__file__).parent.parent / template_config_path
        logging.info(f"Loading template config from: {template_full_path}")
        
        with open(template_full_path, 'r') as f:
            template_config_content = f.read()
        
        # Call main_async_with_config with the loaded content
        return await main_async_with_config(job_config_content, agent_config_content, template_config_content)

    except Exception as e:
        logger.error(f"\nError: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Add argparse support for command line execution
    parser = argparse.ArgumentParser(description="Run the Flexible Agent with a specified job configuration.")
    parser.add_argument('--job_name', type=str, default='simple_code_improvement',
                        help='Name of the job configuration to run (default: simple_code_improvement)')
    args = parser.parse_args()
    job_name = args.job_name
    asyncio.run(main_async(job_name))