"""
Prompt utilities for the Flexible Agent Framework.

This module contains functions for formatting prompts, appending content to agent configurations,
and synthesizing user queries using Jinja2 templates.
"""

import logging
from jinja2 import Template


def append_content_to_agent_config(agent_config, target_agent_name, grouped_files):
    """
    Recursively find and append content to the target agent's instruction.
    
    Args:
        agent_config: The agent configuration dictionary
        target_agent_name: Name of the target agent to append content to
        grouped_files: List of file data dictionaries for this target agent
        
    Returns:
        bool: True if target agent was found and content appended, False otherwise
    """
    def _append_to_agent_config(current_config):
        if current_config.get('name') == target_agent_name:
            current_instruction = current_config.get('instruction', '') or ''
            
            file_names = [f['file_name'] for f in grouped_files]
            additional_content = f"\n\nFocus on the content from the following files: {', '.join(file_names)}\n"
            
            for file_data in grouped_files:
                additional_content += f"\n--- Content from {file_data['file_name']} ---\n"
                
                # Escape template characters to prevent interpretation
                escaped_content = file_data['file_content']
                escaped_content = escaped_content.replace('{', '&#123;').replace('}', '&#125;')
                escaped_content = escaped_content.replace('[', '&#91;').replace(']', '&#93;')
                
                additional_content += f"\n```python\n{escaped_content}\n```\n"
                additional_content += f"\n--- End of {file_data['file_name']} ---\n"
            
            current_config['instruction'] = current_instruction + additional_content
            logging.info(f"📎 Appended {len(grouped_files)} file(s) to agent '{target_agent_name}'")
            return True
        
        # Search sub_agents for composite agents
        if 'sub_agents' in current_config and current_config['sub_agents']:
            for sub_agent_config in current_config['sub_agents']:
                if _append_to_agent_config(sub_agent_config):
                    return True
        
        return False
    
    return _append_to_agent_config(agent_config)


def synthesize_user_query_jinja2(template_config, file_names, file_types, file_contents):
    """
    Synthesize user query using Jinja2 template.
    
    Args:
        template_config: Template configuration dictionary
        file_names: List of file names (strings)
        file_types: List of file types (strings)  
        file_contents: List of file contents (strings)
        
    Returns:
        str: Rendered user query
    """
    template_content = template_config.get('template_content', '')
    variable_mapping = template_config.get('template_variables', {})
    
    # Prepare template variables
    template_vars = {k: v['default'] for k, v in variable_mapping.items()}
    template_vars.update({
        'file_name': file_names,
        'file_type': file_types, 
        'file_content': file_contents
    })

    # Render template
    template = Template(template_content)
    return template.render(**template_vars)