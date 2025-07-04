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
import logging
from pathlib import Path
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_io.agent_io import create_agent_from_config
from data_model import validate_configuration_file
from utils import analyze_agent_structure, display_agent_readiness
from utils.agent_utils import collect_agent_execution_steps, display_execution_steps_summary, ExecutionStep, maintain_execution_status, report_finished_steps


def load_job_config(job_config_path):
    """Load job configuration from JSON file."""
    with open(job_config_path, 'r') as f:
        return json.load(f)


def load_template_config(template_config_path):
    """Load template configuration from JSON file."""
    with open(template_config_path, 'r') as f:
        return json.load(f)


def synthesize_user_query_jinja2(template_config, analysis_config, input_config, code_content, file_name):
    """Synthesize user query using Jinja2 template."""
    try:
        from jinja2 import Template
    except ImportError:
        logging.error("Jinja2 not installed. Please install with: pip install jinja2")
        raise
    
    # Get template content
    template_content = template_config.get('template_content', '')
    language_mapping = template_config.get('language_mapping', {})
    
    # Prepare template variables
    language = input_config.get('language', 'Python')
    framework = input_config.get('framework', 'Generic')
    language_code_block = language_mapping.get(language, language.lower())
    analysis_focus = analysis_config.get('analysis_focus', [])
    
    # Template variables
    template_vars = {
        'language': language,
        'file_name': file_name,
        'framework': framework,
        'language_code_block': language_code_block,
        'code_content': code_content,
        'analysis_focus': analysis_focus
    }
    
    # Render template
    template = Template(template_content)
    rendered_query = template.render(**template_vars)
    
    return rendered_query


emojis = ["👤", "🤖", "💡", "🔍", "⚙️", "📊", "🛠️", "📈", "📝", "✅", "🌟", 
          "🚀", "🎯", "🧩", "🔧", "📅", "💻", "🖥️", "📱", "🖨️", "🗂️", "🔒", 
          "🔑", "🧰", "🧪", "🧬", "🧫", "🧫", "🧪", "🧬"]


def create_agent_from_config_file(config_path):
    """
    Complete workflow to create an agent from a configuration file.
    
    Args:
        config_path (str or Path): Path to the JSON configuration file
        
    Returns:
        The instantiated agent or None if creation failed
    """
    config_path = Path(config_path)
    
    logging.info("=" * 60)
    logging.info(f"Agent Initialization: {config_path.name}")
    logging.info("=" * 60)

    # Validate configuration
    print("1. Validating configuration...")
    try:
        _, warnings = validate_configuration_file(config_path)
        logger.info(f"   ✓ Configuration is valid")
        if warnings:
            logger.warning(f"   ⚠ {len(warnings)} warnings found:")
            for warning in warnings:
                logger.warning(f"     - {warning}")
        else:
            logger.info("   ✓ No warnings")
    except Exception as e:
        logging.error(f"   ✗ Configuration validation failed: {e}")
        return None
    
    # Create agent
    logging.info("\n2. Creating agent from configuration...")
    try:
        agent = create_agent_from_config(str(config_path))
        logging.info(f"   ✓ Agent '{agent.name}' created successfully")
        logging.info(f"   ✓ Agent type: {agent.__class__.__name__}")
        if hasattr(agent, 'sub_agents'):
            logging.info(f"   ✓ Number of sub-agents: {len(agent.sub_agents)}")
    except Exception as e:
        logging.error(f"   ✗ Agent creation failed: {e}")
        return None
    
    # Analyze structure and display readiness
    analyze_agent_structure(agent)
    display_agent_readiness(agent)
    
    return agent


def _save_analysis_results(input_path, agent, event_count, final_responses: Dict[str, str], code_content: str, job_config: dict):
    """Helper function to save analysis results to files."""
    output_config = job_config.get('output_config', {})
    output_dir = Path(__file__).parent.parent / output_config.get('output_directory', 'output')
    output_dir.mkdir(exist_ok=True)
    
    timestamp_format = output_config.get('timestamp_format', '%Y%m%d_%H%M%S')
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    current_time = datetime.datetime.now()
    
    # Save text report
    file_naming = output_config.get('file_naming', 'code_analysis_{input_filename}_{timestamp}')
    output_file = output_dir / f"{file_naming.format(input_filename=input_path.stem, timestamp=timestamp)}.txt"
    with open(output_file, 'w') as f:
        f.write(f"Code Improvement Analysis Report\n")
        f.write(f"================================\n\n")
        f.write(f"Analysis Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input File: {input_path}\n")
        f.write(f"Agent: {agent.name}\n")
        f.write(f"Events Generated: {event_count}\n\n")
        # Include final responses.
        if final_responses:
            f.write("\n\nFinal Responses:\n")
            f.write("-" * 40 + "\n")
            for author, response in final_responses.items():
                f.write(f"{author}:\n")
                f.write(response + "\n\n")
    
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
        "analysis_results": final_responses,
        "code_analyzed": code_content
    }
    
    json_file = output_dir / f"{file_naming.format(input_filename=input_path.stem, timestamp=timestamp)}.json"
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2)
    
    logging.info(f"📁 Output saved to: {output_file}")
    logging.info(f"📄 JSON output saved to: {json_file}")

    return str(output_file), str(json_file)


async def run_agent(agent, user_query, job_config: dict):
    # Import all required modules at once
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import types
    from dotenv import load_dotenv
    
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
        import traceback
        traceback.print_exc()
        return None


def log_event_details(event, session):
    for field in ["author", "id", "invocation_id"]:
        logging.debug(f"📝 {field} = {getattr(event, field, 'N/A')}")
    if hasattr(event, 'actions'):
        logging.info(f"📝 Actions: transfer_to_agent = {event.actions.transfer_to_agent}, escalate = {event.actions.escalate}")
    logging.info(f"Session state: {session.state}")


async def run_job(agent, input_file_path: str, execution_steps: Dict[str, ExecutionStep], job_config: dict):
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
        logging.error(f"Input file not found: {input_path}")
        return None
    
    with open(input_path, 'r') as f:
        code_content = f.read()
    
    # Display input information
    logging.info("\n" + "=" * 60)
    logging.info(f"Running Agent with Input: {input_path.name}")
    logging.info("=" * 60)
    logging.info(f"Input file: {input_path}")
    logging.info(f"File size: {len(code_content)} characters")
    logging.info(f"Lines of code: {len(code_content.splitlines())}")
    logging.info(f"\nCode preview (first 500 characters):")
    logging.info("-" * 40)
    logging.info(code_content[:500] + ("..." if len(code_content) > 500 else ""))
    logging.info("-" * 40)
    logging.info(f"\nExecuting agent workflow...")

    # Create analysis request using Jinja2 template synthesis
    analysis_config = job_config.get('analysis_config', {})
    input_config = job_config.get('input_config', {})
    
    # Load and synthesize template using Jinja2
    template_config_path = analysis_config.get('template_config_path')
    logging.info(f"Using template config path from job config: {template_config_path}")
    template_full_path = Path(__file__).parent.parent / template_config_path
    template_config = load_template_config(template_full_path)
    
    user_query = synthesize_user_query_jinja2(
        template_config, analysis_config, input_config, 
        code_content, input_path.name
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


            author, error_code = getattr(event, 'author', 'unknown'), getattr(event, 'error_code', None)
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
                    logging.info(f"📨 Final response received with {len(final_response)} characters")
                    preview = (final_response[:256].replace('\n', ' ') + "..." 
                             if len(final_response) > 256 else final_response)
                    logging.info(f"   📝 Final response preview: {preview}")
                    final_responses[event.author] = final_response
            else:
                # Even events without content are valuable for tracking
                logging.debug(f"📨 Event {event_count}: {type(event).__name__} has no content.")

        logging.info(f"\n✅ Analysis completed! Generated {event_count} events")

        # Save results
        output_file, json_file = _save_analysis_results(
            input_path, agent, event_count, final_responses, code_content, job_config
        )
        
        return {
            "status": "completed",
            "output_file": output_file,
            "json_file": json_file,
            "events_generated": event_count,
            "response_length": sum(len(resp) for resp in final_responses.values()),
            "analysis_results": final_responses,
        }
        
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
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


async def main_async(job_name: str = "simple_code_improvement"):
    """Main async function that creates and runs the code improvement agent."""
    
    try:
        # Load job configuration
        job_config_path = Path(__file__).parent.parent / "config" / "job" / "json_examples" / f"{job_name}.json"
        job_config = load_job_config(job_config_path)
        
        job_name = job_config.get('job_name', 'Code Improvement Agent')
        logging.info(f"{job_name} - Live Execution Demo")
        logging.info("=" * 60)

        # Create agent using job config
        agent_config = job_config.get('agent_config', {})
        config_path = Path(__file__).parent.parent / agent_config.get('config_path', 'config/agent/json_examples/simple_code_improvement.json')
        logging.info("Creating Code Improvement Agent...")
        agent = create_agent_from_config_file(config_path)
        
        if agent is None:
            logging.error("Failed to create agent. Exiting.")
            return 1
        
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
        input_file = Path(__file__).parent.parent / input_config.get('input_file_path', 'agent_io/agent_io.py')
        logging.info(f"\n💡 Executing agent analysis on: {input_file}")
        results = await run_job(agent, input_file, execution_steps, job_config)
        
        # Display results
        report_config = job_config.get('report_config', {})
        if results and report_config.get('display_results_summary', True):
            _display_results_summary(results)
            if execution_config.get('track_execution_steps', True):
                report_finished_steps(execution_steps)
        
        logger.info("\n" + "=" * 60)
        logger.info("Agent execution completed successfully!")
        logger.info("=" * 60)

        return 0
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Add argparse support for command line execution
    import argparse
    parser = argparse.ArgumentParser(description="Run the Code Improvement Agent with a specified job configuration.")
    parser.add_argument('--job_name', type=str, default='simple_code_improvement',
                        help='Name of the job configuration to run (default: simple_code_improvement)')
    args = parser.parse_args()
    job_name = args.job_name
    asyncio.run(main_async(job_name))