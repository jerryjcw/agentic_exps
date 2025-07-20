#!/usr/bin/env python3
"""
Test script to see what the Google ADK agent actually returns.
"""

import unittest
import asyncio
import logging
from agent_optimizer.llm_utils import call_evaluation_agent


class TestAgentResponse(unittest.TestCase):
    """Test cases for Google ADK agent responses."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
        
        # Test prompts and system instruction
        self.evaluation_prompt = """You are an expert evaluator. Compare these outputs:

EXPECTED OUTPUT: Hello World

ACTUAL OUTPUT: Hello World

Please evaluate and provide your response in this EXACT JSON format:
{
    "score": 0.8,
    "global_feedback": "Overall assessment",
    "agent_feedback": []
}

Score should be between 0.0 and 1.0."""
        
        self.system_instruction = "You are a helpful evaluation assistant. Always respond with valid JSON in the exact format requested."
    
    def test_google_adk_agent_response_format(self):
        """Test what the Google ADK evaluation agent actually returns."""
        async def run_test():
            try:
                response = await call_evaluation_agent(
                    evaluation_prompt=self.evaluation_prompt,
                    system_instruction=self.system_instruction,
                    model_name="openai/gpt-4o"
                )
                
                # Basic response validation
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)
                
                # Print detailed information for debugging
                print(f"\nResponse type: {type(response)}")
                print(f"Response length: {len(response)}")
                print(f"Raw response: {repr(response)}")
                print(f"Response content:\n{response}")
                
                return response
                
            except Exception as e:
                self.fail(f"Error calling evaluation agent: {e}")
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(run_test())
            # Additional assertions can be added here based on expected response format
        finally:
            loop.close()
    
    def test_agent_response_contains_expected_elements(self):
        """Test that agent response contains expected JSON elements."""
        async def run_test():
            try:
                response = await call_evaluation_agent(
                    evaluation_prompt=self.evaluation_prompt,
                    system_instruction=self.system_instruction,
                    model_name="openai/gpt-4o"
                )
                
                # Check for JSON-like structure (basic validation)
                self.assertIn("{", response)
                self.assertIn("}", response)
                
                # Check for expected fields (case-insensitive)
                response_lower = response.lower()
                self.assertTrue(
                    "score" in response_lower or 
                    "rating" in response_lower,
                    "Response should contain a score or rating field"
                )
                
                return response
                
            except Exception as e:
                self.fail(f"Error calling evaluation agent: {e}")
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(run_test())
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()