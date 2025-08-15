#!/usr/bin/env python3
"""
Test script to verify JSON parsing fixes in critic and suggester.
"""

import unittest
import logging
from agent_optimizer.critic import OutputEvaluator
from agent_optimizer.types import OptimizationObjective


class TestCriticParsing(unittest.TestCase):
    """Test cases for critic's JSON parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
        
        # Initialize evaluator
        self.evaluator = OutputEvaluator()
        
        # Test response formats
        self.expected_format_response = '''Here is my evaluation:
    {
        "score": 0.75,
        "global_feedback": "The output matches most requirements but lacks detail in some areas.",
        "agent_feedback": [
            {
                "agent_id": "GeneralCodeAnalysisAgent",
                "issue": "Missing function documentation",
                "evidence": "No docstrings found"
            }
        ]
    }
    That completes my evaluation.'''
        
        self.simple_format_response = '''Based on my analysis:
    {
        "score": 0.8,
        "feedback": "Good analysis overall, but could be more comprehensive"
    }
    End of evaluation.'''
        
        self.malformed_json_response = '''Here is malformed JSON:
    {
        "score": 0.6
        "feedback": "Missing comma"
    }'''
        
        self.no_json_response = "This is just plain text without any JSON structure."
    
    def test_parse_expected_format(self):
        """Test parsing of expected JSON format response."""
        result = self.evaluator._parse_evaluation_response(self.expected_format_response)
        
        self.assertIsNotNone(result, "Should successfully parse expected format")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('score', result, "Result should contain score")
        self.assertIn('global_feedback', result, "Result should contain global_feedback")
        self.assertIn('agent_feedback', result, "Result should contain agent_feedback")
        
        # Validate specific values
        self.assertEqual(result['score'], 0.75)
        self.assertIsInstance(result['agent_feedback'], list)
        self.assertEqual(len(result['agent_feedback']), 1)
        
        print(f"Expected format result: {result}")
    
    def test_parse_simple_format(self):
        """Test parsing of simple JSON format response (what Google ADK might return)."""
        result = self.evaluator._parse_evaluation_response(self.simple_format_response)
        
        self.assertIsNotNone(result, "Should successfully parse simple format")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('score', result, "Result should contain score")
        
        # Should have been converted from 'feedback' to 'global_feedback'
        self.assertIn('global_feedback', result, "Should convert 'feedback' to 'global_feedback'")
        self.assertEqual(result['score'], 0.8)
        
        print(f"Simple format result: {result}")
    
    def test_parse_malformed_json(self):
        """Test parsing of malformed JSON response."""
        result = self.evaluator._parse_evaluation_response(self.malformed_json_response)
        
        # Should return None for malformed JSON
        self.assertIsNone(result, "Should return None for malformed JSON")
        
        print(f"Malformed JSON result: {result}")
    
    def test_parse_no_json(self):
        """Test parsing of response with no JSON structure."""
        result = self.evaluator._parse_evaluation_response(self.no_json_response)
        
        # Should return None when no JSON is found
        self.assertIsNone(result, "Should return None when no JSON structure is found")
        
        print(f"No JSON result: {result}")
    
    def test_parse_edge_cases(self):
        """Test parsing edge cases."""
        # Empty string
        result = self.evaluator._parse_evaluation_response("")
        self.assertIsNone(result, "Should handle empty string")
        
        # Only JSON without text
        json_only = '{"score": 0.9, "global_feedback": "Perfect match"}'
        result = self.evaluator._parse_evaluation_response(json_only)
        self.assertIsNotNone(result, "Should parse JSON-only response")
        self.assertEqual(result['score'], 0.9)
        
        # Invalid score range
        invalid_score = '{"score": 1.5, "feedback": "Score out of range"}'
        result = self.evaluator._parse_evaluation_response(invalid_score)
        # Should still parse but might be caught later in validation
        if result:
            self.assertEqual(result['score'], 1.5)
    
    def test_score_validation(self):
        """Test score validation logic."""
        # Valid score
        valid_response = '{"score": 0.5, "feedback": "Valid score"}'
        result = self.evaluator._parse_evaluation_response(valid_response)
        self.assertIsNotNone(result)
        self.assertTrue(0.0 <= result['score'] <= 1.0)
        
        # Test boundary values
        boundary_low = '{"score": 0.0, "feedback": "Minimum score"}'
        result_low = self.evaluator._parse_evaluation_response(boundary_low)
        self.assertIsNotNone(result_low)
        self.assertEqual(result_low['score'], 0.0)
        
        boundary_high = '{"score": 1.0, "feedback": "Maximum score"}'
        result_high = self.evaluator._parse_evaluation_response(boundary_high)
        self.assertIsNotNone(result_high)
        self.assertEqual(result_high['score'], 1.0)


if __name__ == "__main__":
    unittest.main()