"""
Agent Workflow Runner - Executes ADK-style agent workflows with tracing support.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Tuple
import yaml

from core.flexible_agents import main_async_with_config
from .types import WorkflowTrace, AgentTrace

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """Executes agent workflows with optional tracing and debugging."""
    
    def __init__(self, enable_tracing: bool = True):
        self.enable_tracing = enable_tracing
        self.current_trace = None
    
    async def run_workflow(
        self,
        agent_config: Dict[str, Any],
        input_data: Any,
        job_config: Optional[Dict[str, Any]] = None,
        template_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[WorkflowTrace]]:
        """
        Execute an agent workflow with the given configuration and input.
        
        Args:
            agent_config: Agent configuration dictionary
            input_data: Input data for the workflow
            job_config: Job configuration (optional)
            template_config: Template configuration (optional)
            
        Returns:
            Tuple of (output_string, trace_object)
        """
        start_time = time.time()
        
        if self.enable_tracing:
            self.current_trace = WorkflowTrace()
        
        # Create default configurations if not provided
        if job_config is None:
            job_config = self._create_default_job_config()
        
        if template_config is None:
            template_config = self._create_default_template_config()
        
        # Update job config with input data if it doesn't have template_config_content
        if 'analysis_config' not in job_config or 'template_config_content' not in job_config['analysis_config']:
            job_config = self._update_job_config_with_input(job_config, input_data)
        
        try:
            # Convert configurations to YAML strings
            agent_config_yaml = yaml.dump(agent_config, default_flow_style=False)
            job_config_yaml = yaml.dump(job_config, default_flow_style=False)
            template_config_yaml = yaml.dump(template_config, default_flow_style=False)
            
            # Execute the workflow
            exit_code, results = await main_async_with_config(
                job_config_content=job_config_yaml,
                agent_config_content=agent_config_yaml,
                template_config_content=template_config_yaml,
                uuid="optimization_run"
            )
            
            # Extract output
            if exit_code == 0 and results:
                output = self._extract_output_from_results(results)
                
                # Complete trace if enabled
                if self.enable_tracing and self.current_trace:
                    self.current_trace.total_execution_time = time.time() - start_time
                    self.current_trace.final_output = output
                    # TODO: Extract individual agent traces from results
                    self._extract_agent_traces_from_results(results)
                
                return output, self.current_trace
            else:
                error_msg = f"Workflow execution failed with exit code {exit_code}"
                if results and isinstance(results, dict):
                    error_msg += f": {results.get('error_message', 'Unknown error')}"
                
                logger.error(error_msg)
                return error_msg, self.current_trace
                
        except Exception as e:
            error_msg = f"Error executing workflow: {str(e)}"
            logger.error(error_msg)
            return error_msg, self.current_trace
    
    def _create_default_job_config(self) -> Dict[str, Any]:
        """Create a default job configuration."""
        return {
            "job_name": "AgentOptimizationRun",
            "job_description": "Optimization run for agent workflow",
            "job_type": "optimization",
            "runner_config": {
                "app_name": "AgentOptimization",
                "session_config": {
                    "user_id": "optimizer",
                    "session_id": "optimization_session"
                }
            },
            "agent_config": {
                "config_type": "content"
            },
            "input_config": {
                "input_files": [],
                "preview_length": 1000
            },
            "analysis_config": {
                "template_config_content": {}
            },
            "output_config": {
                "output_directory": "output",
                "output_format": ["json"],
                "file_naming": "optimization_run_{timestamp}",
                "timestamp_format": "%Y%m%d_%H%M%S",
                "include_metadata": True
            },
            "execution_config": {
                "track_execution_steps": True,
                "display_progress": False,
                "log_level": "INFO",
                "error_handling": "continue_on_agent_failure",
                "timeout_seconds": 300
            },
            "report_config": {
                "include_final_responses": True,
                "include_code_preview": False,
                "include_execution_summary": True,
                "display_results_summary": False
            }
        }
    
    def _create_default_template_config(self) -> Dict[str, Any]:
        """Create a default template configuration."""
        return {
            "template_name": "optimization_template",
            "template_description": "Template for optimization runs",
            "user_query_template": "{{input_data}}",
            "variables": {
                "input_data": "Please analyze the following input data."
            }
        }
    
    def _update_job_config_with_input(self, job_config: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        """Update job configuration with input data."""
        # Create a copy to avoid modifying original
        updated_config = json.loads(json.dumps(job_config))
        
        # Update analysis config with input data
        if 'analysis_config' not in updated_config:
            updated_config['analysis_config'] = {}
        
        # Set template config content with input data
        updated_config['analysis_config']['template_config_content'] = {
            "template_name": "optimization_input",
            "template_description": "Input data for optimization",
            "user_query_template": str(input_data),
            "variables": {}
        }
        
        return updated_config
    
    def _extract_output_from_results(self, results: Dict[str, Any]) -> str:
        """Extract the main output from workflow results."""
        if 'execution_results' in results:
            execution_results = results['execution_results']
            if isinstance(execution_results, dict):
                # Combine all agent outputs
                outputs = []
                for agent_name, response in execution_results.items():
                    if isinstance(response, str):
                        outputs.append(f"[{agent_name}]\n{response}")
                    else:
                        outputs.append(f"[{agent_name}]\n{str(response)}")
                return "\n\n".join(outputs)
            else:
                return str(execution_results)
        
        # Fallback to string representation of results
        return str(results)
    
    def _extract_agent_traces_from_results(self, results: Dict[str, Any]) -> None:
        """Extract individual agent traces from workflow results."""
        if not self.current_trace:
            return
        
        # Extract execution results
        execution_results = results.get('execution_results', {})
        
        for agent_name, output in execution_results.items():
            if isinstance(output, str):
                # Parse the output to extract timestamp and content
                parts = output.split(' %% (', 1)
                if len(parts) == 2:
                    actual_output = parts[1].split('): ', 1)
                    if len(actual_output) == 2:
                        _, content = actual_output
                        agent_trace = AgentTrace(
                            agent_id=agent_name,
                            input_data="",  # Would need more detailed tracing
                            output_data=content,
                            prompt="",  # Would need access to agent config
                            tools_used=[]
                        )
                        self.current_trace.agent_traces[agent_name] = agent_trace
    
    def get_agent_prompts(self, agent_config: Dict[str, Any]) -> Dict[str, str]:
        """Extract agent prompts from configuration."""
        prompts = {}
        
        def extract_recursive(agent_dict: Dict[str, Any]):
            if 'name' in agent_dict and 'instruction' in agent_dict:
                prompts[agent_dict['name']] = agent_dict['instruction']
            
            if 'sub_agents' in agent_dict:
                for sub_agent in agent_dict['sub_agents']:
                    extract_recursive(sub_agent)
        
        extract_recursive(agent_config)
        return prompts
    
