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

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local imports
from utils.document_reader import DocumentReader
from agent_io.agent_io import create_agent_from_config, _create_agent_from_dict
from data_model import validate_configuration_file
from utils import analyze_agent_structure, display_agent_readiness
from utils.agent_utils import (
    collect_agent_execution_steps, display_execution_steps_summary, 
    ExecutionStep, maintain_execution_status, report_finished_steps,
    save_results, display_results_summary
)
from utils.prompt_utils import synthesize_user_query_jinja2
from utils.workflow_configuration import WorkflowConfiguration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


emojis = ["👤", "🤖", "💡", "🔍", "⚙️", "📊", "🛠️", "📈", "📝", "✅", "🌟", 
          "🚀", "🎯", "🧩", "🔧", "📅", "💻", "🖥️", "📱", "🖨️", "🗂️", "🔒", 
          "🔑", "🧰", "🧪", "🧬", "🧫", "🧫", "🧪", "🧬"]


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
        
        print(f"\n🤖 Starting task analysis...")
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


async def run_job(agent, input_file_paths, execution_steps: Dict[str, ExecutionStep], workflow_config: WorkflowConfiguration):
    """
    Run the agent with input files for processing.
    
    Args:
        agent: The instantiated agent
        input_file_paths: List of paths to the files to process, or single path as string
        execution_steps: Dictionary of execution steps to track
        workflow_config: WorkflowConfiguration instance for all configuration needs
        
    Returns:
        dict: Execution results with file paths and metadata
    """
    # Load environment variables
    load_dotenv()
    
    # Handle input files structure
    input_files_data = []
    file_names = []  # Only non-targeted files for Jinja2
    file_types = []  # Only non-targeted files for Jinja2
    file_contents = []  # Only non-targeted files for Jinja2
    
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
            target_agents = file_info.get('target_agents', [])
            
            file_data = workflow_config.read_input_file(Path(file_path), input_type)
            input_files_data.append(file_data)
            
            if target_agents:
                # This file was already processed and added to agent config - skip for Jinja2
                agent_names = ", ".join(target_agents)
                logging.info(f"📌 File '{file_data['file_name']}' was targeted to agent(s) '{agent_names}' (processed earlier)")
            else:
                # This file goes to the general user query via Jinja2
                file_names.append(file_data['file_name'])
                file_types.append(file_data['file_type'])
                file_contents.append(file_data['file_content'])
                logging.info(f"📄 File '{file_data['file_name']}' will be processed via Jinja2 template")
                
        except FileNotFoundError as e:
            logging.error(str(e))
            return None
    
    # Display input information
    logging.info(f"Running agent with {len(input_files_data)} total file(s) ({len(file_names)} for Jinja2)")
    total_size = sum(data['file_size'] for data in input_files_data)
    
    for i, file_data in enumerate(input_files_data, 1):
        logging.info(f"  {i}. {file_data['file_name']} ({file_data['file_size']} chars, {file_data['file_type']})")
    
    logging.info(f"Total size: {total_size} characters")

    # Create analysis request using Jinja2 template synthesis
    analysis_config = workflow_config.job_config.get('analysis_config', {})
    
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
        template_config = workflow_config.load_template_config(template_full_path)
    
    # Create analysis request using Jinja2 template synthesis (only for non-targeted files)
    if file_names:  # Only synthesize if there are non-targeted files
        user_query = synthesize_user_query_jinja2(
            template_config, file_names, file_types, file_contents
        )
        logging.info(f"Synthesized query using Jinja2: {len(user_query)} characters")
    else:
        # All files are targeted to specific agents, create a basic query
        user_query = "Please analyze the provided content and generate your report."
        logging.info("All files are targeted to specific agents, using basic query")

    try:
        response_generator, session = await run_agent(agent, user_query, workflow_config.job_config)
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
        output_file, json_file = save_results(
            input_files_data, agent, event_count, final_responses, workflow_config.job_config
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
        # Initialize WorkflowConfiguration
        workflow_config = WorkflowConfiguration()
        
        # Load configurations
        workflow_config.load_job_config_from_content(job_config_content)
        workflow_config.load_agent_config_from_content(agent_config_content)
        workflow_config.load_template_config_from_content(template_config_content)
        
        job_name = workflow_config.job_config.get('job_name', 'Flexible Agent')
        logging.info(f"Loaded job config: {workflow_config.job_config.get('job_name', 'Unknown')}")
        logging.info(f"{job_name} - Execution")
        
        # Process input files and folders using WorkflowConfiguration
        try:
            input_files, _ = workflow_config.process_input_files_and_folders()
        except (ValueError, FileNotFoundError) as e:
            logging.error(str(e))
            return 1
        
        # Apply targeted file content to agent configuration
        workflow_config.apply_targeted_files_to_agent_config()
        
        # Create agent from the modified configuration
        agent = _create_agent_from_dict(workflow_config.agent_config)
        
        if agent is None:
            logging.error("Failed to create agent")
            return 1
        
        # Analyze structure and display readiness
        analyze_agent_structure(agent)
        display_agent_readiness(agent)
        
        # Collect agent execution steps
        execution_config = workflow_config.get_execution_config()
        if execution_config.get('track_execution_steps', True):
            execution_steps = collect_agent_execution_steps(agent)
            if execution_config.get('display_progress', True):
                display_execution_steps_summary(execution_steps)
        else:
            execution_steps = {}
        
        results = await run_job(agent, input_files, execution_steps, workflow_config)
        
        # Display results
        report_config = workflow_config.get_report_config()
        if results and report_config.get('display_results_summary', True):
            display_results_summary(results)
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
        
        # Initialize WorkflowConfiguration
        workflow_config = WorkflowConfiguration()
        workflow_config.load_job_config_from_content(job_config_content)
        
        logging.info(f"Loaded job config: {workflow_config.job_config.get('job_name', 'Unknown')}")

        # Load agent configuration content
        agent_config_info = workflow_config.job_config.get('agent_config', {})
        config_path = Path(__file__).parent.parent / agent_config_info.get('config_path', 'config/agent/json_examples/simple_code_improvement.json')
        logging.info(f"Loading agent config from: {config_path}")
        
        with open(config_path, 'r') as f:
            if str(config_path).endswith(('.yaml', '.yml')):
                agent_config_content = f.read()
            else:
                # Convert JSON to YAML for consistency
                agent_config_dict = json.load(f)
                agent_config_content = yaml.dump(agent_config_dict)
        
        # Load template configuration content
        analysis_config = workflow_config.job_config.get('analysis_config', {})
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