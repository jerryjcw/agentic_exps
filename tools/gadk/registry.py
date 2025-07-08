#!/usr/bin/env python3
"""
Google ADK FunctionTool Registry - Automatic tool discovery and registration.

This module provides a centralized registry that automatically discovers and registers
all FunctionTool objects from the tools/gadk directory, allowing easy access via
registry.tool_name syntax.

Usage:
    from tools.gadk.registry import registry
    
    # Use tools directly
    result = registry.current_time_tool(city="New York")
    result = registry.google_search_tool(query="python programming")
    
    # Get all available tools
    all_tools = registry.get_all_tools()
    
    # Get tools by category
    financial_tools = registry.get_tools_by_category("financial")
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from google.adk.tools import FunctionTool
except ImportError:
    logger.warning("Google ADK not available. Registry will work in mock mode.")
    # Mock FunctionTool for development
    class FunctionTool:
        def __init__(self, func):
            self.func = func
            self.name = func.__name__
        
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)


class FunctionToolRegistry:
    """
    Automatic registry for Google ADK FunctionTool objects.
    
    This registry automatically discovers and registers all FunctionTool objects
    from the tools/gadk directory, providing easy access via attribute syntax.
    """
    
    def __init__(self):
        """Initialize the registry and discover all available tools."""
        self._tools: Dict[str, FunctionTool] = {}
        self._raw_functions: Dict[str, callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = defaultdict(list)
        
        # Get the tools/gadk directory path
        self._tools_dir = Path(__file__).parent
        
        # Auto-discover all tools
        self._discover_tools()
    
    def _discover_tools(self) -> None:
        """Automatically discover and register all FunctionTool objects."""
        logger.info(f"Discovering tools in {self._tools_dir}")
        
        # Get all Python files in the tools/gadk directory
        python_files = list(self._tools_dir.glob("*.py"))
        
        for file_path in python_files:
            # Skip __init__.py, registry.py, and test files
            if file_path.name in ["__init__.py", "registry.py"] or file_path.name.startswith("test_"):
                continue
                
            module_name = file_path.stem
            self._discover_tools_from_module(module_name)
    
    def _discover_tools_from_module(self, module_name: str) -> None:
        """Discover tools from a specific module."""
        try:
            # Import the module
            module_path = f"tools.gadk.{module_name}"
            module = importlib.import_module(module_path)
            
            # Determine category from module name
            category = self._get_category_from_module_name(module_name)
            
            # Look for FunctionTool objects and raw functions
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, FunctionTool):
                    self._register_tool(name, obj, category, module_name)
                elif callable(obj) and not name.startswith("_") and hasattr(obj, "__module__"):
                    # Check if it's a function defined in this module
                    if obj.__module__ == module_path:
                        self._register_raw_function(name, obj, category, module_name)
            
            logger.info(f"Discovered tools from {module_name}: {len([t for t in self._tools.keys() if self._tool_metadata[t]['module'] == module_name])} FunctionTools")
            
        except ImportError as e:
            logger.warning(f"Could not import {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error discovering tools from {module_name}: {e}")
    
    def _get_category_from_module_name(self, module_name: str) -> str:
        """Extract category from module name."""
        if "financial" in module_name.lower():
            return "financial"
        elif "debug" in module_name.lower() or "test" in module_name.lower():
            return "debug"
        elif "search" in module_name.lower():
            return "search"
        elif "weather" in module_name.lower():
            return "weather"
        else:
            return "general"
    
    def _register_tool(self, name: str, tool: FunctionTool, category: str, module_name: str) -> None:
        """Register a FunctionTool object."""
        self._tools[name] = tool
        self._categories[category].append(name)
        
        # Extract metadata
        func = getattr(tool, 'func', None) or getattr(tool, '_func', None)
        self._tool_metadata[name] = {
            'category': category,
            'module': module_name,
            'type': 'FunctionTool',
            'function': func,
            'doc': getattr(func, '__doc__', '') if func else '',
            'signature': str(inspect.signature(func)) if func else ''
        }
    
    def _register_raw_function(self, name: str, func: callable, category: str, module_name: str) -> None:
        """Register a raw function and create a FunctionTool wrapper."""
        # Skip if already registered as FunctionTool
        if name in self._tools:
            return
            
        # Create FunctionTool wrapper
        tool_name = f"{name}_tool" if not name.endswith("_tool") else name
        
        try:
            function_tool = FunctionTool(func)
            self._tools[tool_name] = function_tool
            self._raw_functions[name] = func
            self._categories[category].append(tool_name)
            
            # Store metadata
            self._tool_metadata[tool_name] = {
                'category': category,
                'module': module_name,
                'type': 'FunctionTool',
                'function': func,
                'doc': func.__doc__ or '',
                'signature': str(inspect.signature(func))
            }
            
        except Exception as e:
            logger.warning(f"Could not create FunctionTool for {name}: {e}")
    
    def __getattr__(self, name: str) -> FunctionTool:
        """Allow access to tools via attribute syntax (registry.tool_name)."""
        if name in self._tools:
            return self._tools[name]
        
        # Try with _tool suffix
        tool_name = f"{name}_tool"
        if tool_name in self._tools:
            return self._tools[tool_name]
        
        # Try without _tool suffix
        if name.endswith("_tool"):
            base_name = name[:-5]
            if base_name in self._tools:
                return self._tools[base_name]
        
        raise AttributeError(f"Tool '{name}' not found in registry. Available tools: {list(self._tools.keys())}")
    
    def __getitem__(self, name: str) -> FunctionTool:
        """Allow access to tools via dictionary syntax (registry['tool_name'])."""
        return self.__getattr__(name)
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return (name in self._tools or 
                f"{name}_tool" in self._tools or 
                (name.endswith("_tool") and name[:-5] in self._tools))
    
    def get_all_tools(self) -> Dict[str, FunctionTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tools_by_category(self, category: str) -> Dict[str, FunctionTool]:
        """Get tools by category."""
        if category not in self._categories:
            return {}
        
        return {name: self._tools[name] for name in self._categories[category]}
    
    def get_available_categories(self) -> List[str]:
        """Get all available tool categories."""
        return list(self._categories.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata information for a tool."""
        if name in self._tool_metadata:
            return self._tool_metadata[name].copy()
        
        # Try with _tool suffix
        tool_name = f"{name}_tool"
        if tool_name in self._tool_metadata:
            return self._tool_metadata[tool_name].copy()
        
        return None
    
    def list_tools(self, category: Optional[str] = None) -> None:
        """Print a formatted list of all tools."""
        if category:
            tools_to_show = self.get_tools_by_category(category)
            print(f"\n=== {category.title()} Tools ===")
        else:
            tools_to_show = self._tools
            print(f"\n=== All Tools ({len(tools_to_show)} total) ===")
        
        for name, tool in tools_to_show.items():
            info = self._tool_metadata.get(name, {})
            print(f"\n• {name}")
            print(f"  Category: {info.get('category', 'unknown')}")
            print(f"  Module: {info.get('module', 'unknown')}")
            print(f"  Signature: {info.get('signature', 'unknown')}")
            if info.get('doc'):
                # Show first line of docstring
                first_line = info['doc'].split('\n')[0].strip()
                print(f"  Description: {first_line}")
    
    def reload_tools(self) -> None:
        """Reload all tools (useful for development)."""
        self._tools.clear()
        self._raw_functions.clear()
        self._tool_metadata.clear()
        self._categories.clear()
        
        # Reload all modules
        modules_to_reload = []
        for module_name in sys.modules.keys():
            if module_name.startswith("tools.gadk.") and module_name != "tools.gadk.registry":
                modules_to_reload.append(module_name)
        
        for module_name in modules_to_reload:
            try:
                importlib.reload(sys.modules[module_name])
            except Exception as e:
                logger.warning(f"Could not reload {module_name}: {e}")
        
        # Rediscover tools
        self._discover_tools()
        logger.info("Registry reloaded successfully")
    
    def get_tool_list_for_agent(self) -> List[FunctionTool]:
        """Get a list of all tools suitable for Agent initialization."""
        return list(self._tools.values())
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"FunctionToolRegistry(tools={len(self._tools)}, categories={list(self._categories.keys())})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"FunctionTool Registry with {len(self._tools)} tools across {len(self._categories)} categories"


# Create global registry instance
registry = FunctionToolRegistry()

# Convenience function for agent integration
def get_all_tools() -> List[FunctionTool]:
    """Get all tools as a list for agent initialization."""
    return registry.get_tool_list_for_agent()

# Export for easy importing
__all__ = ['registry', 'get_all_tools', 'FunctionToolRegistry']


if __name__ == "__main__":
    # Demo usage
    print("=== Google ADK FunctionTool Registry Demo ===")
    print(f"Registry: {registry}")
    print(f"Available categories: {registry.get_available_categories()}")
    
    # List all tools
    registry.list_tools()
    
    # Example usage (if tools are available)
    available_tools = registry.get_all_tools()
    if available_tools:
        print(f"\n=== Example Usage ===")
        tool_name = list(available_tools.keys())[0]
        print(f"Example: registry.{tool_name}")
        print(f"Tool info: {registry.get_tool_info(tool_name)}")
    
    # Show usage by category
    for category in registry.get_available_categories():
        tools_in_category = registry.get_tools_by_category(category)
        print(f"\n{category.title()} tools: {list(tools_in_category.keys())}")