"""
Workflow Configuration Management

This module provides the WorkflowConfiguration class for centralized configuration
processing, including job configs, template configs, and input file/folder management.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from utils.document_reader import DocumentReader
from utils.prompt_utils import append_content_to_agent_config

logger = logging.getLogger(__name__)


class WorkflowConfiguration:
    """Centralized configuration management for the flexible agent workflow."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize WorkflowConfiguration.
        
        Args:
            base_path: Base path for resolving relative file paths
        """
        self.base_path = base_path or Path(__file__).parent.parent
        self.job_config = {}
        self.agent_config = {}
        self.template_config = {}
        self.input_files = []
        self.targeted_files_by_agent = {}
        
    def load_job_config(self, job_config_path: Path) -> Dict[str, Any]:
        """Load job configuration from YAML or JSON file."""
        with open(job_config_path, 'r') as f:
            if str(job_config_path).endswith(('.yaml', '.yml')):
                self.job_config = yaml.safe_load(f)
            else:
                self.job_config = json.load(f)
        return self.job_config
    
    def load_job_config_from_content(self, job_config_content: str) -> Dict[str, Any]:
        """Load job configuration from YAML content string."""
        self.job_config = yaml.safe_load(job_config_content)
        return self.job_config
    
    def load_agent_config_from_content(self, agent_config_content: str) -> Dict[str, Any]:
        """Load agent configuration from YAML content string."""
        self.agent_config = yaml.safe_load(agent_config_content)
        return self.agent_config
    
    def load_template_config(self, template_config_path: Path) -> Dict[str, Any]:
        """Load template configuration from YAML or JSON file."""
        with open(template_config_path, 'r') as f:
            if str(template_config_path).endswith(('.yaml', '.yml')):
                self.template_config = yaml.safe_load(f)
            else:
                self.template_config = json.load(f)
        return self.template_config
    
    def load_template_config_from_content(self, template_config_content: str) -> Dict[str, Any]:
        """Load template configuration from YAML content string."""
        self.template_config = yaml.safe_load(template_config_content)
        return self.template_config
    
    def read_input_file(self, file_path: Path, input_type: Optional[str] = None, **metadata) -> Dict[str, Any]:
        """
        Read a single input file and return its content and metadata.
        
        Args:
            file_path: Path to the input file
            input_type: Explicit input type (overrides file extension)
            **metadata: Additional metadata for the file
            
        Returns:
            Dictionary containing file_name, file_type, file_content, and metadata
        """
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
        
        result.update(metadata)
        return result
    
    def read_input_folder(self, folder_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Read all files from a folder (first level only) and return their content and metadata.
        
        Args:
            folder_config: Folder configuration with input_path and optional target_agent
            
        Returns:
            List of file data dictionaries from the folder
        """
        folder_path = Path(folder_config['input_path'])
        if not folder_path.is_absolute():
            folder_path = self.base_path / folder_path
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Input folder not found: {folder_path}")
        
        files_data = []
        
        for file_path in folder_path.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    file_data = self.read_input_file(file_path, folder_config.get('input_type'))
                    file_data['source_folder'] = str(folder_path)
                    files_data.append(file_data)
                except (UnicodeDecodeError, PermissionError):
                    continue  # Skip unreadable files silently
            
        return files_data
    
    def process_input_files_and_folders(self) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Process input files and folders from job configuration.
        
        Returns:
            Tuple of (input_files_list, targeted_files_by_agent_dict)
        """
        input_config = self.job_config.get('input_config', {})
        
        if 'input_files' not in input_config and 'input_folders' not in input_config:
            raise ValueError("No input_files or input_folders found in input_config")
            
        self.input_files = []
        self.targeted_files_by_agent = {}
        
        # Process input_files if present
        if 'input_files' in input_config:
            input_files_config = input_config['input_files']
            
            for file_config in input_files_config:
                file_path = self.base_path / file_config['input_path']
                target_agent = file_config.get('target_agent')
                
                # Convert target_agent to list format for consistent processing
                if target_agent:
                    if isinstance(target_agent, list):
                        target_agents = target_agent
                    else:
                        target_agents = [target_agent]
                else:
                    target_agents = []
                
                self.input_files.append({
                    'path': file_path,
                    'input_type': file_config.get('input_type'),
                    'target_agents': target_agents
                })
                
                # If this file targets specific agents, read it and group it for each agent
                if target_agents:
                    file_data = self.read_input_file(file_path, file_config.get('input_type'))
                    for agent in target_agents:
                        if agent not in self.targeted_files_by_agent:
                            self.targeted_files_by_agent[agent] = []
                        self.targeted_files_by_agent[agent].append(file_data)
        
        # Process input_folders if present
        if 'input_folders' in input_config:
            input_folders_config = input_config['input_folders']
            
            for folder_config in input_folders_config:
                target_agent = folder_config.get('target_agent')
                
                # Convert target_agent to list format for consistent processing
                if target_agent:
                    if isinstance(target_agent, list):
                        target_agents = target_agent
                    else:
                        target_agents = [target_agent]
                else:
                    target_agents = []
                
                folder_files_data = self.read_input_folder(folder_config)
                
                for file_data in folder_files_data:
                    self.input_files.append({
                        'path': file_data['full_path'],
                        'input_type': file_data['file_type'],
                        'target_agents': target_agents
                    })
                    
                    # If this folder targets specific agents, assign each file to those agents
                    if target_agents:
                        for agent in target_agents:
                            if agent not in self.targeted_files_by_agent:
                                self.targeted_files_by_agent[agent] = []
                            self.targeted_files_by_agent[agent].append(file_data)
        
        return self.input_files, self.targeted_files_by_agent
    
    def apply_targeted_files_to_agent_config(self) -> int:
        """
        Apply targeted file content to agent configuration.
        
        Returns:
            Number of agents that were successfully modified
        """
        modified_count = 0
        if self.targeted_files_by_agent:
            for target_agent, files in self.targeted_files_by_agent.items():
                success = append_content_to_agent_config(self.agent_config, target_agent, files)
                if success:
                    modified_count += 1
                else:
                    logger.warning(f"Could not find target agent '{target_agent}' in configuration")
        return modified_count
    
    def get_template_config(self) -> Dict[str, Any]:
        """
        Get template configuration, loading from path if needed.
        
        Returns:
            Template configuration dictionary
        """
        analysis_config = self.job_config.get('analysis_config', {})
        
        if 'template_config_content' in analysis_config:
            return analysis_config['template_config_content']
        else:
            template_config_path = analysis_config.get('template_config_path')
            template_full_path = self.base_path / template_config_path
            return self.load_template_config(template_full_path)
    
    def get_runner_config(self) -> Dict[str, Any]:
        """Get runner configuration from job config."""
        return self.job_config.get('runner_config', {})
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration from job config."""
        return self.job_config.get('execution_config', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration from job config."""
        return self.job_config.get('output_config', {})
    
    def get_report_config(self) -> Dict[str, Any]:
        """Get report configuration from job config."""
        return self.job_config.get('report_config', {})