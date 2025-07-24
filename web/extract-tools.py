#!/usr/bin/env python3
"""
Tool Registry Extractor for Web UI Database

Extracts tool information from the tools/gadk registry and formats it for database storage.
This script is called by the database server on EVERY startup to ensure fresh tool data.
"""

import sys
import os
import json
import inspect
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def extract_tools():
    """Extract tool information from the registry and return as JSON."""
    try:
        # Import the registry
        from tools.gadk.registry import registry
        
        tools_data = []
        
        # Get all tools from registry
        all_tools = registry.get_all_tools()
        
        for tool_name, tool_obj in all_tools.items():
            # Get tool metadata
            tool_info = registry.get_tool_info(tool_name)
            
            if tool_info and tool_info.get('function'):
                func = tool_info['function']
                
                # Extract module information
                func_module = func.__module__ if hasattr(func, '__module__') else 'unknown'
                
                # Add tools.gadk. prefix as requested
                if func_module and not func_module.startswith('tools.gadk.'):
                    if func_module.startswith('gadk.'):
                        func_module = f'tools.{func_module}'
                    elif not func_module.startswith('tools.'):
                        func_module = f'tools.gadk.{func_module}'
                
                # Create tool record
                tool_record = {
                    'function_name': tool_name,
                    'class': 'FunctionTool',  # As specified in requirements
                    'module': 'google.adk.tools',  # As specified in requirements
                    'function_module': func_module,
                    'category': tool_info.get('category', 'general'),
                    'description': tool_info.get('doc', '').split('\n')[0].strip() if tool_info.get('doc') else '',
                    'signature': tool_info.get('signature', ''),
                    'registry_module': tool_info.get('module', '')
                }
                
                tools_data.append(tool_record)
        
        return {
            'status': 'success',
            'tools': tools_data,
            'count': len(tools_data)
        }
        
    except ImportError as e:
        return {
            'status': 'error',
            'error': f'Could not import registry: {e}',
            'tools': []
        }
    except Exception as e:
        return {
            'status': 'error', 
            'error': f'Error extracting tools: {e}',
            'tools': []
        }

if __name__ == '__main__':
    result = extract_tools()
    print(json.dumps(result, indent=2))