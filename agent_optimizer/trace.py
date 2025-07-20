"""
Trace Extractor - Extracts sub-agent inputs/outputs/prompts from workflow runs.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from .types import WorkflowTrace, AgentTrace

logger = logging.getLogger(__name__)


class TraceExtractor:
    """Extracts detailed execution traces from workflow runs."""
    
    def __init__(self):
        self.trace_patterns = {
            'agent_start': r'Agent: (.+?) \((.+?)\) started',
            'agent_finish': r'Agent: (.+?) \((.+?)\) finished',
            'agent_error': r'Agent: (.+?) \((.+?)\) failed',
            'final_response': r'Final response received: (\d+) characters',
            'timestamp': r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        }
    
    def extract_trace_from_results(
        self,
        results: Dict[str, Any],
        agent_config: Dict[str, Any]
    ) -> WorkflowTrace:
        """
        Extract detailed trace information from workflow execution results.
        
        Args:
            results: Results from workflow execution
            agent_config: Agent configuration used
            
        Returns:
            WorkflowTrace with detailed execution information
        """
        trace = WorkflowTrace()
        
        try:
            # Extract agent traces from execution results
            execution_results = results.get('execution_results', {})
            agent_prompts = self._extract_agent_prompts(agent_config)
            
            for agent_id, response in execution_results.items():
                agent_trace = self._create_agent_trace(
                    agent_id, response, agent_prompts.get(agent_id, '')
                )
                trace.agent_traces[agent_id] = agent_trace
            
            # Extract timing information
            trace.total_execution_time = self._extract_execution_time(results)
            
            # Extract final output
            trace.final_output = self._extract_final_output(results)
            
            # Enrich with additional metadata
            self._enrich_trace_with_metadata(trace, results)
            
        except Exception as e:
            logger.error(f"Error extracting trace: {str(e)}")
            # Return empty trace rather than failing
            pass
        
        return trace
    
    def _create_agent_trace(
        self,
        agent_id: str,
        response: str,
        prompt: str
    ) -> AgentTrace:
        """Create an agent trace from response data."""
        # Parse response to extract timestamp and content
        input_data = ""
        output_data = response
        execution_time = None
        error = None
        
        # Extract timestamp and content from response format
        # Format: "AgentName %% (2023-01-01T12:00:00): actual content"
        if ' %% (' in response:
            parts = response.split(' %% (', 1)
            if len(parts) == 2:
                remaining = parts[1]
                if '): ' in remaining:
                    timestamp_part, content = remaining.split('): ', 1)
                    output_data = content
                    # Could parse timestamp here if needed
        
        # Check for error patterns
        if 'error' in response.lower() or 'failed' in response.lower():
            error = self._extract_error_message(response)
        
        # Extract tools used (if any)
        tools_used = self._extract_tools_used(response)
        
        return AgentTrace(
            agent_id=agent_id,
            input_data=input_data,
            output_data=output_data,
            prompt=prompt,
            tools_used=tools_used,
            execution_time=execution_time,
            error=error
        )
    
    def _extract_agent_prompts(self, agent_config: Dict[str, Any]) -> Dict[str, str]:
        """Extract all agent prompts from configuration."""
        prompts = {}
        
        def extract_recursive(agent_dict: Dict[str, Any]):
            if isinstance(agent_dict, dict):
                if 'name' in agent_dict and 'instruction' in agent_dict:
                    prompts[agent_dict['name']] = agent_dict['instruction']
                
                if 'sub_agents' in agent_dict:
                    for sub_agent in agent_dict['sub_agents']:
                        extract_recursive(sub_agent)
        
        extract_recursive(agent_config)
        return prompts
    
    def _extract_execution_time(self, results: Dict[str, Any]) -> Optional[float]:
        """Extract total execution time from results."""
        # Look for timing information in results
        if 'execution_time' in results:
            return results['execution_time']
        
        # Try to calculate from timestamps in logs
        # This would require more detailed log parsing
        return None
    
    def _extract_final_output(self, results: Dict[str, Any]) -> Optional[str]:
        """Extract the final output from results."""
        execution_results = results.get('execution_results', {})
        
        if isinstance(execution_results, dict):
            # Combine all outputs
            outputs = []
            for agent_id, response in execution_results.items():
                if isinstance(response, str):
                    outputs.append(response)
            return "\n\n".join(outputs)
        
        return str(execution_results)
    
    def _extract_error_message(self, response: str) -> Optional[str]:
        """Extract error message from response."""
        error_patterns = [
            r'Error: (.+)',
            r'Exception: (.+)',
            r'Failed: (.+)',
            r'Error code: (\d+)'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_tools_used(self, response: str) -> List[str]:
        """Extract tools used from response."""
        tools = []
        
        # Look for common tool patterns
        tool_patterns = [
            r'Using tool: (.+)',
            r'Tool called: (.+)',
            r'Function: (.+)',
            r'API call: (.+)'
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            tools.extend(matches)
        
        return tools
    
    def _enrich_trace_with_metadata(self, trace: WorkflowTrace, results: Dict[str, Any]) -> None:
        """Enrich trace with additional metadata."""
        # Add execution metadata
        for agent_id, agent_trace in trace.agent_traces.items():
            # Add execution order (could be extracted from results)
            # Add performance metrics
            # Add error context
            pass
    
