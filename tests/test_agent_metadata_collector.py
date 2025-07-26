#!/usr/bin/env python3
"""
Unit tests for the agent metadata collector.

Tests the collection of agent metadata including processed prompts,
template variables, and file content summaries.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.agent_metadata_collector import (
    truncate_text_to_words,
    extract_attached_files_from_instruction,
    extract_template_variables_from_instruction,
    collect_agent_metadata,
    agent_metadata_to_dict,
    collect_all_agents_metadata,
    AgentMetadata
)


class TestAgentMetadataCollector(unittest.TestCase):
    """Test suite for agent metadata collection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_agent_config = {
            "name": "TestAgent",
            "class": "Agent",
            "module": "google.adk.agents",
            "model": "openai/gpt-4o",
            "instruction": "You are a Python expert with detailed analysis skills for enterprise software development.",
            "description": "Test agent for Python analysis",
            "output_key": "test_output",
            "tools": [],
            "sub_agents": [
                {
                    "name": "SubAgent",
                    "class": "Agent",
                    "module": "google.adk.agents",
                    "model": "openai/gpt-4o",
                    "instruction": "You specialize in Python security analysis for enterprise environments.",
                    "description": "Sub-agent for security analysis"
                }
            ]
        }
        
        self.instruction_with_files = """
You are a security expert.

Focus on the content from the following files: test_file.py

--- Content from test_file.py ---

```python
def hello_world():
    # This contains &#123;&#123; template_like &#125;&#125; patterns
    config = {
        "setting": "&#123;&#123; value &#125;&#125;",
        "another": "&#123;% if condition %&#125;value&#123;% endif %&#125;"
    }
    return config

def another_function():
    print("Hello from Python!")
    return "success"
```

--- End of test_file.py ---

Analyze this code for security issues.
"""
        
        self.long_text = " ".join([f"word{i}" for i in range(300)])
    
    def test_truncate_text_to_words(self):
        """Test text truncation to specified word count."""
        # Test short text (no truncation)
        short_text = "This is a short text"
        result = truncate_text_to_words(short_text, 10)
        self.assertEqual(result, short_text)
        
        # Test long text (with truncation)
        result = truncate_text_to_words(self.long_text, 5)
        expected = "word0 word1 word2 word3 word4..."
        self.assertEqual(result, expected)
        
        # Test empty text
        result = truncate_text_to_words("", 10)
        self.assertEqual(result, "")
        
        # Test exact word count
        text = "one two three four five"
        result = truncate_text_to_words(text, 5)
        self.assertEqual(result, text)
    
    def test_extract_attached_files_from_instruction(self):
        """Test extraction of attached file information."""
        files = extract_attached_files_from_instruction(self.instruction_with_files)
        
        self.assertEqual(len(files), 1)
        file_info = files[0]
        
        self.assertEqual(file_info["file_name"], "test_file.py")
        self.assertEqual(file_info["file_type"], "python")
        self.assertIn("def hello_world", file_info["content_preview"])
        self.assertIn("{{ template_like }}", file_info["content_preview"])  # Should be decoded
        self.assertGreater(file_info["original_content_length"], 0)
        self.assertFalse(file_info["is_truncated"])  # This content is short enough
    
    def test_extract_attached_files_truncation(self):
        """Test file content truncation to 256 words."""
        # Create instruction with long file content
        long_content = " ".join([f"word{i}" for i in range(300)])
        instruction = f"""
--- Content from long_file.py ---

```python
{long_content}
```

--- End of long_file.py ---
"""
        
        files = extract_attached_files_from_instruction(instruction)
        self.assertEqual(len(files), 1)
        
        file_info = files[0]
        self.assertTrue(file_info["is_truncated"])
        self.assertTrue(file_info["content_preview"].endswith("..."))
        
        # Count words in preview (should be 256 or less)
        preview_words = file_info["content_preview"].replace("...", "").split()
        self.assertLessEqual(len(preview_words), 256)
    
    def test_extract_template_variables_from_instruction(self):
        """Test extraction of template variables from instruction."""
        instruction = """
        You are a Python expert with detailed analysis skills for enterprise software development.
        Conduct a comprehensive security analysis following OWASP Top 10 guidelines.
        Perform detailed performance analysis considering cloud-native requirements.
        """
        
        variables = extract_template_variables_from_instruction(instruction)
        
        # Should find context-based patterns
        expected_patterns = ["python", "detailed", "comprehensive", "cloud-native"]
        for pattern in expected_patterns:
            self.assertIn(pattern, " ".join(variables))
    
    def test_collect_agent_metadata(self):
        """Test collection of agent metadata from configuration."""
        metadata = collect_agent_metadata(self.sample_agent_config)
        
        self.assertEqual(metadata.name, "TestAgent")
        self.assertEqual(metadata.agent_type, "Agent")
        self.assertEqual(metadata.model, "openai/gpt-4o")
        self.assertIn("Python expert", metadata.instruction)
        self.assertEqual(metadata.description, "Test agent for Python analysis")
        self.assertEqual(metadata.output_key, "test_output")
        self.assertEqual(len(metadata.tools), 0)
        self.assertEqual(len(metadata.sub_agents), 1)
        self.assertGreater(metadata.instruction_length, 0)
        
        # Check sub-agent
        sub_agent = metadata.sub_agents[0]
        self.assertEqual(sub_agent.name, "SubAgent")
        self.assertEqual(sub_agent.agent_type, "Agent")
    
    def test_agent_metadata_to_dict(self):
        """Test conversion of agent metadata to dictionary."""
        metadata = collect_agent_metadata(self.sample_agent_config)
        
        # Test with default preview length (256 words)
        dict_default = agent_metadata_to_dict(metadata)
        self.assertNotIn("full_instruction", dict_default)  # full_instruction removed
        self.assertEqual(dict_default["name"], "TestAgent")
        self.assertEqual(dict_default["agent_type"], "Agent")
        self.assertIn("instruction_preview", dict_default)
        self.assertEqual(len(dict_default["sub_agents"]), 1)
        
        # Test with custom preview length
        dict_custom = agent_metadata_to_dict(metadata, instruction_preview_length=50)
        self.assertNotIn("full_instruction", dict_custom)  # full_instruction removed
        self.assertIn("instruction_preview", dict_custom)
    
    def test_collect_all_agents_metadata(self):
        """Test collection of metadata from entire agent hierarchy."""
        metadata = collect_all_agents_metadata(self.sample_agent_config)
        
        # Check structure
        self.assertIn("root_agent", metadata)
        self.assertIn("all_agents", metadata)
        self.assertIn("summary", metadata)
        
        # Check summary
        summary = metadata["summary"]
        self.assertEqual(summary["total_agents"], 2)  # TestAgent + SubAgent
        self.assertEqual(summary["hierarchy_depth"], 2)
        self.assertIn("Agent", summary["agent_types"])
        self.assertEqual(summary["agent_types"]["Agent"], 2)
        
        # Check all_agents list
        all_agents = metadata["all_agents"]
        self.assertEqual(len(all_agents), 2)
    
    def test_configurable_instruction_preview_length(self):
        """Test that instruction preview length is configurable."""
        metadata = collect_all_agents_metadata(self.sample_agent_config, instruction_preview_length=10)
        
        # Check that preview length is respected
        all_agents = metadata["all_agents"]
        for agent in all_agents:
            if agent["instruction_preview"]:
                # Count words in preview (should be 10 or less, plus "..." if truncated)
                preview_words = agent["instruction_preview"].replace("...", "").split()
                self.assertLessEqual(len(preview_words), 10)
        
        # Check root agent
        root_agent = next(agent for agent in all_agents if agent["name"] == "TestAgent")
        self.assertIsNone(root_agent["parent_agent"])
        self.assertTrue(root_agent["has_sub_agents"])
        self.assertEqual(root_agent["sub_agent_count"], 1)
        
        # Check sub-agent
        sub_agent = next(agent for agent in all_agents if agent["name"] == "SubAgent")
        self.assertEqual(sub_agent["parent_agent"], "TestAgent")
        self.assertFalse(sub_agent["has_sub_agents"])
        self.assertEqual(sub_agent["sub_agent_count"], 0)
    
    def test_agent_with_attached_files(self):
        """Test agent metadata collection with attached files."""
        config_with_files = self.sample_agent_config.copy()
        config_with_files["instruction"] = self.instruction_with_files
        
        metadata = collect_agent_metadata(config_with_files)
        
        self.assertEqual(len(metadata.attached_files), 1)
        file_info = metadata.attached_files[0]
        self.assertEqual(file_info["file_name"], "test_file.py")
        self.assertEqual(file_info["file_type"], "python")
        self.assertIn("def hello_world", file_info["content_preview"])
    
    def test_empty_agent_config(self):
        """Test handling of minimal agent configuration."""
        minimal_config = {
            "name": "MinimalAgent",
            "class": "Agent"
        }
        
        metadata = collect_agent_metadata(minimal_config)
        
        self.assertEqual(metadata.name, "MinimalAgent")
        self.assertEqual(metadata.agent_type, "Agent")
        self.assertIsNone(metadata.model)
        self.assertEqual(metadata.instruction, "")
        self.assertEqual(len(metadata.tools), 0)
        self.assertEqual(len(metadata.sub_agents), 0)
        self.assertEqual(len(metadata.attached_files), 0)
    
    def test_complex_hierarchy(self):
        """Test metadata collection for complex agent hierarchy."""
        complex_config = {
            "name": "RootAgent",
            "class": "SequentialAgent",
            "description": "Root sequential agent",
            "sub_agents": [
                {
                    "name": "ParallelGroup",
                    "class": "ParallelAgent",
                    "sub_agents": [
                        {
                            "name": "Worker1",
                            "class": "Agent",
                            "instruction": "Worker 1 instruction"
                        },
                        {
                            "name": "Worker2", 
                            "class": "Agent",
                            "instruction": "Worker 2 instruction"
                        }
                    ]
                },
                {
                    "name": "FinalProcessor",
                    "class": "Agent",
                    "instruction": "Final processing instruction"
                }
            ]
        }
        
        metadata = collect_all_agents_metadata(complex_config)
        summary = metadata["summary"]
        
        self.assertEqual(summary["total_agents"], 5)  # Root + Parallel + 2 Workers + Final
        self.assertEqual(summary["hierarchy_depth"], 3)  # Root -> Parallel -> Workers
        self.assertEqual(summary["agent_types"]["SequentialAgent"], 1)
        self.assertEqual(summary["agent_types"]["ParallelAgent"], 1)
        self.assertEqual(summary["agent_types"]["Agent"], 3)


if __name__ == '__main__':
    unittest.main()