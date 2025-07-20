#!/usr/bin/env python3
"""
Test script to verify unified suggester prompt configuration.
"""

import unittest
import logging
from agent_optimizer.config_loader import get_optimizer_config


class TestUnifiedPrompts(unittest.TestCase):
    """Test cases for unified suggester prompt configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
        
        # Initialize config loader
        self.config = get_optimizer_config()
        
        # Define expected prompt types
        self.prompt_types = ['accuracy', 'fluency', 'factuality', 'instruction_following']
        
        # Define required format elements
        self.required_elements = {
            'exact_format': 'EXACT JSON format',
            'double_braces': ['{{', '}}'],
            'confidence_example': '"confidence": 0.8'
        }
    
    def test_all_prompt_types_exist(self):
        """Test that all expected prompt types exist in configuration."""
        for prompt_type in self.prompt_types:
            with self.subTest(prompt_type=prompt_type):
                try:
                    prompt = self.config.get_suggester_prompt(prompt_type)
                    self.assertIsInstance(prompt, str, f"{prompt_type} prompt should be a string")
                    self.assertGreater(len(prompt), 0, f"{prompt_type} prompt should not be empty")
                except Exception as e:
                    self.fail(f"Failed to get {prompt_type} prompt: {e}")
    
    def test_prompt_format_consistency(self):
        """Test that all suggester prompts have consistent format."""
        inconsistent_prompts = []
        
        for prompt_type in self.prompt_types:
            with self.subTest(prompt_type=prompt_type):
                prompt = self.config.get_suggester_prompt(prompt_type)
                
                # Check for consistent JSON format specification
                has_exact_format = self.required_elements['exact_format'] in prompt
                has_double_braces = all(brace in prompt for brace in self.required_elements['double_braces'])
                has_confidence_example = self.required_elements['confidence_example'] in prompt
                
                # Log detailed results
                print(f"\n{prompt_type.upper()} Prompt:")
                print(f"Length: {len(prompt)} characters")
                print(f"✓ Has 'EXACT JSON format': {has_exact_format}")
                print(f"✓ Uses {{ }} braces: {has_double_braces}")
                print(f"✓ Has confidence example: {has_confidence_example}")
                
                # Collect inconsistent prompts
                if not (has_exact_format and has_double_braces and has_confidence_example):
                    inconsistent_prompts.append(prompt_type)
                    print(f"❌ {prompt_type} prompt format is inconsistent!")
                else:
                    print(f"✅ {prompt_type} prompt format is consistent!")
                
                # Individual assertions
                self.assertTrue(has_exact_format, 
                               f"{prompt_type} prompt should contain 'EXACT JSON format'")
                self.assertTrue(has_double_braces, 
                               f"{prompt_type} prompt should use {{ }} braces")
                self.assertTrue(has_confidence_example, 
                               f"{prompt_type} prompt should have confidence example")
        
        # Overall consistency check
        self.assertEqual(len(inconsistent_prompts), 0, 
                        f"Inconsistent prompt formats found: {inconsistent_prompts}")
    
    def test_system_message_format(self):
        """Test system message format consistency."""
        try:
            system_msg = self.config.get_suggester_system_message('default')
            
            self.assertIsInstance(system_msg, str, "System message should be a string")
            self.assertGreater(len(system_msg), 0, "System message should not be empty")
            
            # Check format requirements
            has_exact_format = "EXACT format" in system_msg
            has_double_braces = "{{" in system_msg and "}}" in system_msg
            
            print(f"\nSystem Message:")
            print(f"Length: {len(system_msg)} characters")
            print(f"✓ Has 'EXACT format': {has_exact_format}")
            print(f"✓ Uses {{ }} braces: {has_double_braces}")
            
            if not (has_exact_format and has_double_braces):
                print(f"❌ System message format is inconsistent!")
            else:
                print(f"✅ System message format is consistent!")
            
            # Assertions
            self.assertTrue(has_exact_format, 
                           "System message should contain 'EXACT format'")
            self.assertTrue(has_double_braces, 
                           "System message should use {{ }} braces")
            
        except Exception as e:
            self.fail(f"Failed to get system message: {e}")
    
    def test_feedback_aggregation_prompt_exists(self):
        """Test that the new feedback aggregation prompt exists."""
        try:
            aggregation_prompt = self.config.get_suggester_prompt('feedback_aggregation')
            
            self.assertIsInstance(aggregation_prompt, str, "Aggregation prompt should be a string")
            self.assertGreater(len(aggregation_prompt), 0, "Aggregation prompt should not be empty")
            
            # Check for specific aggregation-related content
            self.assertIn("multiple", aggregation_prompt.lower(), 
                         "Aggregation prompt should mention 'multiple'")
            self.assertIn("pairs", aggregation_prompt.lower(), 
                         "Aggregation prompt should mention 'pairs'")
            
            print(f"\nFeedback Aggregation Prompt:")
            print(f"Length: {len(aggregation_prompt)} characters")
            print("✅ Feedback aggregation prompt exists and contains expected content!")
            
        except Exception as e:
            self.fail(f"Failed to get feedback aggregation prompt: {e}")
    
    def test_aggregation_system_message_exists(self):
        """Test that the aggregation system message exists."""
        try:
            aggregation_system_msg = self.config.get_suggester_system_message('aggregation')
            
            self.assertIsInstance(aggregation_system_msg, str, "Aggregation system message should be a string")
            self.assertGreater(len(aggregation_system_msg), 0, "Aggregation system message should not be empty")
            
            # Check for aggregation-specific content
            self.assertIn("aggregation", aggregation_system_msg.lower(), 
                         "Should mention aggregation")
            self.assertIn("pattern", aggregation_system_msg.lower(), 
                         "Should mention patterns")
            
            print(f"\nAggregation System Message:")
            print(f"Length: {len(aggregation_system_msg)} characters")
            print("✅ Aggregation system message exists and contains expected content!")
            
        except Exception as e:
            self.fail(f"Failed to get aggregation system message: {e}")
    
    def test_prompt_placeholders(self):
        """Test that prompts contain expected placeholders."""
        expected_placeholders = [
            '{current_prompts}',
            '{global_feedback}',
            '{score}',
            '{expected_output}'
        ]
        
        for prompt_type in self.prompt_types:
            with self.subTest(prompt_type=prompt_type):
                prompt = self.config.get_suggester_prompt(prompt_type)
                
                for placeholder in expected_placeholders:
                    self.assertIn(placeholder, prompt, 
                                 f"{prompt_type} prompt should contain {placeholder}")


if __name__ == "__main__":
    unittest.main()